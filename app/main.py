import os
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from jinja2 import pass_context

try:
    from .i18n import translate, get_dir
except ImportError:
    from i18n import translate, get_dir


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "weighbridge.db"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

USERNAME = os.getenv("SWB_USERNAME", "admin")
PASSWORD = os.getenv("SWB_PASSWORD", "admin123")
SECRET = os.getenv("SWB_SECRET", "CHANGE-ME-IN-PRODUCTION")
DEVICE_TOKEN = os.getenv("SWB_DEVICE_TOKEN", "CHANGE-ME-DEVICE")

SUPPORTED_LANGS = {"fa", "en", "hy"}
DEFAULT_LANG = "fa"

app = FastAPI(title="Smart Weighbridge v1")
app.add_middleware(SessionMiddleware, secret_key=SECRET, max_age=60 * 60 * 12)

app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates")


@app.middleware("http")
async def set_language(request: Request, call_next):
    lang = request.cookies.get("lang", DEFAULT_LANG)
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG
    request.state.lang = lang
    request.state.dir = get_dir(lang)
    response = await call_next(request)
    return response


@app.get("/lang/{lang_code}")
def change_lang(lang_code: str, request: Request):
    if lang_code not in SUPPORTED_LANGS:
        lang_code = DEFAULT_LANG
    back = request.headers.get("referer") or "/"
    resp = RedirectResponse(url=back, status_code=303)
    resp.set_cookie("lang", lang_code, max_age=60 * 60 * 24 * 365, samesite="lax")
    return resp


@pass_context
def _(ctx, key: str) -> str:
    req = ctx.get("request")
    lang = getattr(req.state, "lang", DEFAULT_LANG) if req else DEFAULT_LANG
    return translate(lang, key)

templates.env.globals["_"] = _


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # enable foreign keys for this connection
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_weighments_columns(conn: sqlite3.Connection):
    # Add missing columns safely (idempotent)
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(weighments)").fetchall()}

    additions = {
        "vehicle_type": "vehicle_type TEXT",
        "driver_name": "driver_name TEXT",
        "driver_phone": "driver_phone TEXT",
        "cargo_type": "cargo_type TEXT",
        "cargo_owner": "cargo_owner TEXT",
        "origin": "origin TEXT",
        "destination": "destination TEXT",
        "document_no": "document_no TEXT",
        "notes": "notes TEXT",
    }

    for col, ddl in additions.items():
        if col not in cols:
            conn.execute(f"ALTER TABLE weighments ADD COLUMN {ddl}")


def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS weighments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_number INTEGER NOT NULL UNIQUE,
        plate TEXT NOT NULL,
        weight REAL NOT NULL,
        unit TEXT NOT NULL DEFAULT 'kg',
        photo_filename TEXT,
        scale_id TEXT NOT NULL DEFAULT 'SCALE-01',
        operator TEXT NOT NULL,
        created_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'SAVED'
    );

    CREATE TABLE IF NOT EXISTS weighment_photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        weighment_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (weighment_id) REFERENCES weighments(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS scale_state (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        scale_id TEXT NOT NULL,
        weight REAL NOT NULL DEFAULT 0,
        stable INTEGER NOT NULL DEFAULT 0,
        updated_at TEXT NOT NULL
    );

    INSERT OR IGNORE INTO scale_state(id, scale_id, weight, stable, updated_at)
    VALUES(1, 'SCALE-01', 0, 0, datetime('now'));
    """)

    # ensure new columns exist
    _ensure_weighments_columns(conn)

    conn.commit()
    conn.close()


init_db()


def logged_in(request: Request) -> bool:
    return bool(request.session.get("user"))


def require_login(request: Request):
    if not logged_in(request):
        raise HTTPException(status_code=401, detail="Login required")


def next_ticket(conn):
    row = conn.execute("SELECT COALESCE(MAX(ticket_number), 0) + 1 AS n FROM weighments").fetchone()
    return int(row["n"])


def _clean_text(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    return v if v else None


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    if not logged_in(request):
        return RedirectResponse("/login", status_code=303)
    return RedirectResponse("/dashboard", status_code=303)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == USERNAME and password == PASSWORD:
        request.session["user"] = username
        return RedirectResponse("/dashboard", status_code=303)

    error_msg = translate(getattr(request.state, "lang", DEFAULT_LANG), "login_error")
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": error_msg},
        status_code=401,
    )


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    require_login(request)
    conn = db()
    rows = conn.execute("SELECT * FROM weighments ORDER BY id DESC LIMIT 20").fetchall()
    state = conn.execute("SELECT * FROM scale_state WHERE id=1").fetchone()
    total = conn.execute("SELECT COUNT(*) AS c FROM weighments").fetchone()["c"]
    total_weight = conn.execute("SELECT COALESCE(SUM(weight),0) AS s FROM weighments").fetchone()["s"]
    conn.close()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "rows": rows,
            "state": state,
            "total": total,
            "total_weight": round(total_weight, 2),
            "user": request.session["user"],
        },
    )


@app.get("/weigh", response_class=HTMLResponse)
async def weigh_page(request: Request):
    require_login(request)
    conn = db()
    state = conn.execute("SELECT * FROM scale_state WHERE id=1").fetchone()
    conn.close()
    return templates.TemplateResponse(
        "weigh.html",
        {"request": request, "state": state, "user": request.session["user"]},
    )


@app.post("/weigh")
async def create_weighment(
    request: Request,
    plate: str = Form(...),
    weight: float = Form(...),

    vehicle_type: str | None = Form(None),
    driver_name: str | None = Form(None),
    driver_phone: str | None = Form(None),
    cargo_type: str | None = Form(None),
    cargo_owner: str | None = Form(None),
    origin: str | None = Form(None),
    destination: str | None = Form(None),
    document_no: str | None = Form(None),
    notes: str | None = Form(None),

    photo: list[UploadFile] | None = File(None),
):
    require_login(request)

    plate = plate.strip()
    if not plate:
        return RedirectResponse("/weigh?error=plate", status_code=303)
    if weight < 0 or weight > 1000000:
        return RedirectResponse("/weigh?error=weight", status_code=303)

    # clean optional fields
    vehicle_type = _clean_text(vehicle_type)
    driver_name = _clean_text(driver_name)
    driver_phone = _clean_text(driver_phone)
    cargo_type = _clean_text(cargo_type)
    cargo_owner = _clean_text(cargo_owner)
    origin = _clean_text(origin)
    destination = _clean_text(destination)
    document_no = _clean_text(document_no)
    notes = _clean_text(notes)

    # handle photos (multi)
    filenames: list[str] = []
    if photo:
        allowed = {".jpg", ".jpeg", ".png", ".webp"}
        max_each = 10 * 1024 * 1024  # 10MB each
        max_count = 10

        for up in photo[:max_count]:
            if not up or not up.filename:
                continue

            ext = Path(up.filename).suffix.lower()
            if ext not in allowed:
                return RedirectResponse("/weigh?error=photo", status_code=303)

            content = await up.read()
            if len(content) > max_each:
                return RedirectResponse("/weigh?error=photo_size", status_code=303)

            fn = f"{uuid.uuid4().hex}{ext}"
            (UPLOAD_DIR / fn).write_bytes(content)
            filenames.append(fn)

    # backward compatible: keep first photo in photo_filename
    first_photo = filenames[0] if filenames else None

    conn = db()

    # ensure schema (in case app started before init_db ran)
    _ensure_weighments_columns(conn)

    ticket = next_ticket(conn)
    now = datetime.now(timezone.utc).isoformat()

    cur = conn.execute(
        """INSERT INTO weighments
           (ticket_number, plate, weight, unit, photo_filename, scale_id, operator, created_at, status,
            vehicle_type, driver_name, driver_phone, cargo_type, cargo_owner, origin, destination, document_no, notes)
           VALUES (?, ?, ?, 'kg', ?, 'SCALE-01', ?, ?, 'SAVED',
                   ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            ticket, plate, weight, first_photo, request.session["user"], now,
            vehicle_type, driver_name, driver_phone, cargo_type, cargo_owner,
            origin, destination, document_no, notes
        ),
    )

    weighment_id = cur.lastrowid

    # store all photos in weighment_photos (if any)
    if filenames:
        for fn in filenames:
            conn.execute(
                "INSERT INTO weighment_photos (weighment_id, filename, created_at) VALUES (?, ?, ?)",
                (weighment_id, fn, now),
            )

    conn.commit()
    conn.close()

    return RedirectResponse(f"/weighments/{ticket}?saved=1", status_code=303)


@app.get("/weighments/{ticket}", response_class=HTMLResponse)
async def detail(request: Request, ticket: int):
    require_login(request)
    conn = db()
    row = conn.execute(
        "SELECT * FROM weighments WHERE ticket_number=?", (ticket,)
    ).fetchone()

    if not row:
        conn.close()
        raise HTTPException(404, "Ticket not found")

    weighment_id = row["id"]

    # get photos list
    has_photos_table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='weighment_photos'"
    ).fetchone()

    photos: list[str] = []
    if has_photos_table:
        photos_rows = conn.execute(
            "SELECT filename FROM weighment_photos WHERE weighment_id=? ORDER BY id ASC",
            (weighment_id,),
        ).fetchall()
        photos = [r["filename"] for r in photos_rows]

    # fallback
    if not photos and row["photo_filename"]:
        photos = [row["photo_filename"]]

    conn.close()

    return templates.TemplateResponse(
        "detail.html",
        {"request": request, "row": row, "photos": photos, "user": request.session["user"]},
    )


@app.get("/records", response_class=HTMLResponse)
async def records(request: Request, q: str = ""):
    require_login(request)
    conn = db()
    if q.strip():
        like = f"%{q.strip()}%"
        rows = conn.execute(
            """SELECT * FROM weighments
               WHERE plate LIKE ? OR CAST(ticket_number AS TEXT) LIKE ?
               ORDER BY id DESC""",
            (like, like),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM weighments ORDER BY id DESC").fetchall()
    conn.close()

    return templates.TemplateResponse(
        "records.html",
        {"request": request, "rows": rows, "q": q, "user": request.session["user"]},
    )


# ---------- DELETE ROUTE ----------
@app.post("/weighments/{ticket}/delete")
async def delete_weighment(request: Request, ticket: int, next: str = Form("/records")):
    require_login(request)

    if not next.startswith("/"):
        next = "/records"

    conn = db()
    row = conn.execute(
        "SELECT * FROM weighments WHERE ticket_number=?",
        (ticket,),
    ).fetchone()

    if not row:
        conn.close()
        return RedirectResponse(next, status_code=303)

    weighment_id = row["id"]

    filenames = []

    has_photos_table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='weighment_photos'"
    ).fetchone()

    if has_photos_table:
        photos_rows = conn.execute(
            "SELECT filename FROM weighment_photos WHERE weighment_id=?",
            (weighment_id,),
        ).fetchall()
        filenames = [r["filename"] for r in photos_rows]
        conn.execute("DELETE FROM weighment_photos WHERE weighment_id=?", (weighment_id,))

    if not filenames and row["photo_filename"]:
        filenames = [row["photo_filename"]]

    conn.execute("DELETE FROM weighments WHERE id=?", (weighment_id,))
    conn.commit()
    conn.close()

    for fn in filenames:
        try:
            p = UPLOAD_DIR / fn
            if p.exists():
                p.unlink()
        except Exception:
            pass

    return RedirectResponse(next, status_code=303)


@app.get("/api/scale/weight")
async def get_scale_weight(request: Request):
    conn = db()
    row = conn.execute("SELECT * FROM scale_state WHERE id=1").fetchone()
    conn.close()
    return JSONResponse({
        "scale_id": row["scale_id"],
        "weight": row["weight"],
        "unit": "kg",
        "stable": bool(row["stable"]),
        "updated_at": row["updated_at"],
    })


@app.post("/api/scale/weight")
async def set_scale_weight(request: Request):
    token = request.headers.get("X-Device-Token")
    if token != DEVICE_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid device token")

    body = await request.json()
    try:
        weight = float(body["weight"])
        stable = bool(body.get("stable", False))
        scale_id = str(body.get("scale_id", "SCALE-01"))
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if weight < 0 or weight > 1000000:
        raise HTTPException(status_code=400, detail="Invalid weight")

    now = datetime.now(timezone.utc).isoformat()
    conn = db()
    conn.execute(
        """UPDATE scale_state
           SET scale_id=?, weight=?, stable=?, updated_at=?
           WHERE id=1""",
        (scale_id, weight, 1 if stable else 0, now),
    )
    conn.commit()
    conn.close()
    return {"ok": True, "weight": weight, "stable": stable, "scale_id": scale_id}
