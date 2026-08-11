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

# i18n import (works both locally and on Railway)
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


# ---------- Language middleware ----------
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


# ---------- DB ----------
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


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
    conn.commit()
    conn.close()


init_db()


# ---------- Auth ----------
def logged_in(request: Request) -> bool:
    return bool(request.session.get("user"))


def require_login(request: Request):
    if not logged_in(request):
        raise HTTPException(status_code=401, detail="Login required")


def next_ticket(conn):
    row = conn.execute("SELECT COALESCE(MAX(ticket_number), 0) + 1 AS n FROM weighments").fetchone()
    return int(row["n"])


# ---------- Routes ----------
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

    # فعلاً پیام خطا فارسیه؛ بعداً ترجمه‌اش می‌کنیم
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "نام کاربری یا رمز عبور اشتباه است."},
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
    photo: UploadFile | None = File(None),
):
    require_login(request)

    plate = plate.strip()
    if not plate:
        return RedirectResponse("/weigh?error=plate", status_code=303)
    if weight < 0 or weight > 1000000:
        return RedirectResponse("/weigh?error=weight", status_code=303)

    filename = None
    if photo and photo.filename:
        allowed = {".jpg", ".jpeg", ".png", ".webp"}
        ext = Path(photo.filename).suffix.lower()
        if ext not in allowed:
            return RedirectResponse("/weigh?error=photo", status_code=303)
        filename = f"{uuid.uuid4().hex}{ext}"
        target = UPLOAD_DIR / filename
        content = await photo.read()
        if len(content) > 10 * 1024 * 1024:
            return RedirectResponse("/weigh?error=photo_size", status_code=303)
        target.write_bytes(content)

    conn = db()
    ticket = next_ticket(conn)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO weighments
           (ticket_number, plate, weight, unit, photo_filename, scale_id, operator, created_at, status)
           VALUES (?, ?, ?, 'kg', ?, 'SCALE-01', ?, ?, 'SAVED')""",
        (ticket, plate, weight, filename, request.session["user"], now),
    )
    conn.commit()
    conn.close()

    return RedirectResponse(f"/weighments/{ticket}?saved=1", status_code=303)


@app.get("/weighments/{ticket}", response_class=HTMLResponse)
async def detail(request: Request, ticket: int):
    require_login(request)
    conn = db()
    row = conn.execute("SELECT * FROM weighments WHERE ticket_number=?", (ticket,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Ticket not found")
    return templates.TemplateResponse(
        "detail.html",
        {"request": request, "row": row, "user": request.session["user"]},
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
