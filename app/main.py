import os
import re
import time
import sqlite3
import uuid

from pathlib import Path
from datetime import datetime, timezone

from fastapi import (
    FastAPI,
    Request,
    Form,
    UploadFile,
    File,
    HTTPException,
)

from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
    JSONResponse,
)

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from jinja2 import pass_context

try:
    from .i18n import translate, get_dir
except ImportError:
    from i18n import translate, get_dir

from .serial_manager import SerialManager, DeviceConfig


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "weighbridge.db"

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

USERNAME = os.getenv("SWB_USERNAME", "admin")
PASSWORD = os.getenv("SWB_PASSWORD", "admin123")
SECRET = os.getenv(
    "SWB_SECRET",
    "CHANGE-ME-IN-PRODUCTION",
)

DEVICE_TOKEN = os.getenv(
    "SWB_DEVICE_TOKEN",
    "SWB-DEV-9f3a1c7b-2e4d-4b1f-9a12-7c3d9e5a1f22",
)

SERIAL_MODE = os.getenv(
    "SWB_SERIAL_MODE",
    "local",
).strip().lower()

MAX_SCALE_AGE_SEC = float(
    os.getenv(
        "SWB_MAX_SCALE_AGE_SEC",
        "5",
    )
)

TEST_MODE = os.getenv(
    "SWB_TEST_MODE",
    "0",
).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

SUPPORTED_LANGS = {"fa", "en", "hy"}
DEFAULT_LANG = "fa"


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Smart Weighbridge v2"
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET,
    max_age=60 * 60 * 12,
)

app.mount(
    "/static",
    StaticFiles(
        directory=BASE_DIR / "app" / "static"
    ),
    name="static",
)

app.mount(
    "/uploads",
    StaticFiles(
        directory=UPLOAD_DIR
    ),
    name="uploads",
)

templates = Jinja2Templates(
    directory=BASE_DIR / "app" / "templates"
)

serial_mgr = SerialManager()


# ============================================================
# AGENT STATE
# ============================================================

agent_state = {
    "running": False,
    "last_error": "",
    "last_raw": "",
    "last_weight": None,
    "last_stable": False,
    "last_seen_ts": 0.0,
    "raw_lines": [],
}


# ============================================================
# LANGUAGE
# ============================================================

@app.middleware("http")
async def set_language(
    request: Request,
    call_next,
):
    lang = request.cookies.get(
        "lang",
        DEFAULT_LANG,
    )

    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG

    request.state.lang = lang
    request.state.dir = get_dir(lang)

    return await call_next(request)


@app.get("/lang/{lang_code}")
def change_lang(
    lang_code: str,
    request: Request,
):
    if lang_code not in SUPPORTED_LANGS:
        lang_code = DEFAULT_LANG

    back = (
        request.headers.get("referer")
        or "/"
    )

    response = RedirectResponse(
        back,
        status_code=303,
    )

    response.set_cookie(
        "lang",
        lang_code,
        max_age=60 * 60 * 24 * 365,
        samesite="lax",
    )

    return response


@pass_context
def _(ctx, key: str) -> str:
    req = ctx.get("request")

    lang = (
        getattr(
            req.state,
            "lang",
            DEFAULT_LANG,
        )
        if req
        else DEFAULT_LANG
    )

    return translate(lang, key)


templates.env.globals["_"] = _


# ============================================================
# DATABASE
# ============================================================

def db():
    conn = sqlite3.connect(
        DB_PATH,
        timeout=30,
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


def table_columns(
    conn,
    table,
):
    return {
        row["name"]
        for row in conn.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    }


def ensure_weighment_columns(conn):
    existing = table_columns(
        conn,
        "weighments",
    )

    additions = {
        "vehicle_type":
            "vehicle_type TEXT",

        "weighing_fee":
            "weighing_fee REAL",

        "vehicle_weight":
            "vehicle_weight REAL",

        "driver_name":
            "driver_name TEXT",

        "driver_phone":
            "driver_phone TEXT",

        "cargo_type":
            "cargo_type TEXT",

        "cargo_owner":
            "cargo_owner TEXT",

        "origin":
            "origin TEXT",

        "destination":
            "destination TEXT",

        "document_no":
            "document_no TEXT",

        "notes":
            "notes TEXT",

        "weighing_mode":
            "weighing_mode TEXT NOT NULL DEFAULT 'SINGLE'",

        "first_weight":
            "first_weight REAL",

        "first_weighed_at":
            "first_weighed_at TEXT",

        "first_operator":
            "first_operator TEXT",

        "second_weight":
            "second_weight REAL",

        "second_weighed_at":
            "second_weighed_at TEXT",

        "second_operator":
            "second_operator TEXT",

        "net_weight":
            "net_weight REAL",

        "first_weight_manual":
            "first_weight_manual INTEGER NOT NULL DEFAULT 0",

        "second_weight_manual":
            "second_weight_manual INTEGER NOT NULL DEFAULT 0",
    }

    for name, ddl in additions.items():
        if name not in existing:
            conn.execute(
                f"""
                ALTER TABLE weighments
                ADD COLUMN {ddl}
                """
            )


def init_db():
    conn = db()

    conn.executescript(
        """
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
            FOREIGN KEY(weighment_id)
                REFERENCES weighments(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS scale_state (
            id INTEGER PRIMARY KEY CHECK(id=1),
            scale_id TEXT NOT NULL,
            weight REAL NOT NULL DEFAULT 0,
            stable INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        );

        INSERT OR IGNORE INTO scale_state(
            id,
            scale_id,
            weight,
            stable,
            updated_at
        )
        VALUES(
            1,
            'SCALE-01',
            0,
            0,
            datetime('now')
        );

        CREATE TABLE IF NOT EXISTS device_config (
            id INTEGER PRIMARY KEY CHECK(id=1),
            enabled INTEGER NOT NULL DEFAULT 0,
            port TEXT NOT NULL DEFAULT '',
            baud INTEGER NOT NULL DEFAULT 2400,
            indicator TEXT NOT NULL
                DEFAULT 'GENERIC_SIGNED_5_6',
            stable_tol REAL NOT NULL DEFAULT 1.0,
            stable_seconds REAL NOT NULL DEFAULT 1.2,
            send_every_sec REAL NOT NULL DEFAULT 0.3,
            scale_id TEXT NOT NULL DEFAULT 'SCALE-01',
            updated_at TEXT NOT NULL DEFAULT(datetime('now'))
        );

        INSERT OR IGNORE INTO device_config(id)
        VALUES(1);

        CREATE TABLE IF NOT EXISTS vehicle_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_type TEXT NOT NULL,
            vehicle_key TEXT NOT NULL UNIQUE,
            weighing_fee REAL,
            vehicle_weight REAL,
            updated_at TEXT NOT NULL
        );
        """
    )

    ensure_weighment_columns(conn)

    conn.execute(
        """
        UPDATE weighments

        SET
            weighing_mode =
                COALESCE(
                    NULLIF(weighing_mode, ''),
                    'SINGLE'
                ),

            first_weight =
                COALESCE(
                    first_weight,
                    weight
                ),

            first_weighed_at =
                COALESCE(
                    first_weighed_at,
                    created_at
                ),

            first_operator =
                COALESCE(
                    first_operator,
                    operator
                ),

            first_weight_manual =
                COALESCE(
                    first_weight_manual,
                    0
                ),

            second_weight_manual =
                COALESCE(
                    second_weight_manual,
                    0
                )

        WHERE
            weighing_mode IS NULL
            OR weighing_mode = ''
            OR first_weight IS NULL
            OR first_weight_manual IS NULL
            OR second_weight_manual IS NULL
        """
    )

    conn.commit()
    conn.close()


init_db()


# ============================================================
# AUTH
# ============================================================

def logged_in(request):
    return bool(
        request.session.get("user")
    )


def require_login(request):
    if not logged_in(request):
        raise HTTPException(
            status_code=401,
            detail="Login required",
        )


# ============================================================
# HELPERS
# ============================================================

def next_ticket(conn):
    row = conn.execute(
        """
        SELECT
            COALESCE(
                MAX(ticket_number),
                0
            ) + 1 AS n
        FROM weighments
        """
    ).fetchone()

    return int(row["n"])


def clean_text(value):
    if value is None:
        return None

    value = str(value).strip()

    return value if value else None


def clean_optional_float(value):
    if value is None:
        return None

    value = (
        str(value)
        .strip()
        .replace(",", "")
    )

    if not value:
        return None

    try:
        return float(value)

    except ValueError:
        return None


def form_bool(value):
    return (
        str(value or "")
        .strip()
        .lower()
        in {
            "1",
            "true",
            "yes",
            "on",
        }
    )


def parse_datetime(value):
    dt = datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )

    if dt.tzinfo is None:
        dt = dt.replace(
            tzinfo=timezone.utc
        )

    return dt


def calculate_net_weight(
    first_weight,
    second_weight,
):
    return abs(
        abs(float(first_weight))
        -
        abs(float(second_weight))
    )


def validate_manual_weight(value):
    if value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not (
        0 <= number <= 1000000
    ):
        return None

    return number


# ============================================================
# VEHICLE PROFILES
# ============================================================

def normalize_vehicle_type(value):
    if not value:
        return ""

    value = " ".join(
        str(value)
        .strip()
        .split()
    )

    value = (
        value
        .replace("ي", "ی")
        .replace("ك", "ک")
    )

    return value.casefold()


def get_vehicle_profile(vehicle_type):
    key = normalize_vehicle_type(
        vehicle_type
    )

    if not key:
        return None

    conn = db()

    row = conn.execute(
        """
        SELECT *
        FROM vehicle_profiles
        WHERE vehicle_key=?
        """,
        (key,),
    ).fetchone()

    conn.close()

    return row


def save_vehicle_profile(
    vehicle_type,
    weighing_fee,
    vehicle_weight,
):
    vehicle_type = clean_text(
        vehicle_type
    )

    if not vehicle_type:
        return

    key = normalize_vehicle_type(
        vehicle_type
    )

    if not key:
        return

    now = datetime.now(
        timezone.utc
    ).isoformat()

    conn = db()

    existing = conn.execute(
        """
        SELECT *
        FROM vehicle_profiles
        WHERE vehicle_key=?
        """,
        (key,),
    ).fetchone()

    if existing:
        fee_value = (
            weighing_fee
            if weighing_fee is not None
            else existing["weighing_fee"]
        )

        weight_value = (
            vehicle_weight
            if vehicle_weight is not None
            else existing["vehicle_weight"]
        )

        conn.execute(
            """
            UPDATE vehicle_profiles
            SET
                vehicle_type=?,
                weighing_fee=?,
                vehicle_weight=?,
                updated_at=?
            WHERE vehicle_key=?
            """,
            (
                vehicle_type,
                fee_value,
                weight_value,
                now,
                key,
            ),
        )

    else:
        conn.execute(
            """
            INSERT INTO vehicle_profiles
            (
                vehicle_type,
                vehicle_key,
                weighing_fee,
                vehicle_weight,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                vehicle_type,
                key,
                weighing_fee,
                vehicle_weight,
                now,
            ),
        )

    conn.commit()
    conn.close()


# ============================================================
# PLATE
# ============================================================

def parse_iran_plate(plate):
    if not plate:
        return None

    match = re.fullmatch(
        r"(\d{2})([^\d\-]+)(\d{3})-(\d{2})",
        str(plate).strip(),
    )

    if not match:
        return None

    return {
        "first": match.group(1),
        "letter": match.group(2),
        "middle": match.group(3),
        "city": match.group(4),
    }


def normalize_plate_search(value):
    return (
        str(value)
        .strip()
        .replace(" ", "")
        .replace("ـ", "")
    )


# ============================================================
# SCALE
# ============================================================

def get_scale_state():
    conn = db()

    row = conn.execute(
        """
        SELECT *
        FROM scale_state
        WHERE id=1
        """
    ).fetchone()

    conn.close()

    return row


def validate_live_scale(state):
    if not state:
        return "scale"

    weight = float(
        state["weight"]
    )

    if not (
        -1000000
        <= weight
        <= 1000000
    ):
        return "weight"

    if TEST_MODE:
        return None

    if not bool(
        state["stable"]
    ):
        return "unstable"

    try:
        age = (
            datetime.now(
                timezone.utc
            )
            - parse_datetime(
                str(
                    state["updated_at"]
                )
            )
        ).total_seconds()

        if age > MAX_SCALE_AGE_SEC:
            return "stale"

    except Exception:
        return "stale"

    return None


# ============================================================
# DEVICE
# ============================================================

def load_device_config():
    conn = db()

    row = conn.execute(
        """
        SELECT *
        FROM device_config
        WHERE id=1
        """
    ).fetchone()

    conn.close()

    return DeviceConfig(
        enabled=bool(
            row["enabled"]
        ),

        port=str(
            row["port"]
            or ""
        ),

        baud=int(
            row["baud"]
        ),

        indicator=str(
            row["indicator"]
        ),

        stable_tol=float(
            row["stable_tol"]
        ),

        stable_seconds=float(
            row["stable_seconds"]
        ),

        send_every_sec=float(
            row["send_every_sec"]
        ),

        scale_id=str(
            row["scale_id"]
            or "SCALE-01"
        ),
    )


def save_device_config(cfg):
    conn = db()

    conn.execute(
        """
        UPDATE device_config
        SET
            enabled=?,
            port=?,
            baud=?,
            indicator=?,
            stable_tol=?,
            stable_seconds=?,
            send_every_sec=?,
            scale_id=?,
            updated_at=?
        WHERE id=1
        """,
        (
            1 if cfg.enabled else 0,
            cfg.port,
            cfg.baud,
            cfg.indicator,
            cfg.stable_tol,
            cfg.stable_seconds,
            cfg.send_every_sec,
            cfg.scale_id,
            datetime.now(
                timezone.utc
            ).isoformat(),
        ),
    )

    conn.commit()
    conn.close()


def update_scale_state(
    weight,
    stable,
    scale_id,
):
    conn = db()

    conn.execute(
        """
        UPDATE scale_state
        SET
            scale_id=?,
            weight=?,
            stable=?,
            updated_at=?
        WHERE id=1
        """,
        (
            scale_id,
            float(weight),
            1 if stable else 0,
            datetime.now(
                timezone.utc
            ).isoformat(),
        ),
    )

    conn.commit()
    conn.close()


# ============================================================
# STARTUP / SHUTDOWN
# ============================================================

@app.on_event("startup")
def startup():
    cfg = load_device_config()

    serial_mgr.set_config(cfg)

    if (
        SERIAL_MODE == "local"
        and cfg.enabled
    ):
        serial_mgr.start(
            update_scale_state
        )


@app.on_event("shutdown")
def shutdown():
    if SERIAL_MODE == "local":
        serial_mgr.stop()


# ============================================================
# AUTH PAGES
# ============================================================

@app.get("/")
async def home(request: Request):
    if not logged_in(request):
        return RedirectResponse(
            "/login",
            status_code=303,
        )

    return RedirectResponse(
        "/dashboard",
        status_code=303,
    )


@app.get(
    "/login",
    response_class=HTMLResponse,
)
async def login_page(
    request: Request,
):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": None,
        },
    )


@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if (
        username == USERNAME
        and password == PASSWORD
    ):
        request.session["user"] = username

        return RedirectResponse(
            "/dashboard",
            status_code=303,
        )

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": translate(
                request.state.lang,
                "login_error",
            ),
        },
        status_code=401,
    )


@app.get("/logout")
async def logout(
    request: Request,
):
    request.session.clear()

    return RedirectResponse(
        "/login",
        status_code=303,
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.get(
    "/dashboard",
    response_class=HTMLResponse,
)
async def dashboard(
    request: Request,
):
    require_login(request)

    conn = db()

    rows = conn.execute(
        """
        SELECT *
        FROM weighments
        ORDER BY id DESC
        LIMIT 20
        """
    ).fetchall()

    state = conn.execute(
        """
        SELECT *
        FROM scale_state
        WHERE id=1
        """
    ).fetchone()

    total = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM weighments
        WHERE status != 'WAITING_SECOND'
        """
    ).fetchone()["c"]

    total_weight = conn.execute(
        """
        SELECT
            COALESCE(
                SUM(
                    CASE
                        WHEN weighing_mode='DOUBLE'
                            THEN COALESCE(net_weight,0)
                        ELSE weight
                    END
                ),
                0
            ) AS total
        FROM weighments
        WHERE status != 'WAITING_SECOND'
        """
    ).fetchone()["total"]

    conn.close()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "rows": rows,
            "state": state,
            "total": total,
            "total_weight": round(
                total_weight,
                2,
            ),
            "user":
                request.session["user"],
        },
    )


# ============================================================
# VEHICLE PROFILE MANAGEMENT
# ============================================================

@app.get(
    "/vehicle-profiles",
    response_class=HTMLResponse,
)
async def vehicle_profiles_page(
    request: Request,
):
    require_login(request)

    conn = db()

    profiles = conn.execute(
        """
        SELECT *
        FROM vehicle_profiles
        ORDER BY vehicle_type COLLATE NOCASE
        """
    ).fetchall()

    conn.close()

    return templates.TemplateResponse(
        "vehicle_profiles.html",
        {
            "request": request,
            "profiles": profiles,
            "user":
                request.session["user"],
        },
    )


@app.post(
    "/vehicle-profiles/save"
)
async def vehicle_profile_save(
    request: Request,

    vehicle_type: str = Form(...),

    weighing_fee: str = Form(
        ""
    ),

    vehicle_weight: str = Form(
        ""
    ),
):
    require_login(request)

    vehicle_type = clean_text(
        vehicle_type
    )

    if not vehicle_type:
        return RedirectResponse(
            "/vehicle-profiles",
            status_code=303,
        )

    fee = clean_optional_float(
        weighing_fee
    )

    ref_weight = (
        clean_optional_float(
            vehicle_weight
        )
    )

    if (
        weighing_fee.strip()
        and fee is None
    ):
        return RedirectResponse(
            "/vehicle-profiles?error=fee",
            status_code=303,
        )

    if (
        vehicle_weight.strip()
        and ref_weight is None
    ):
        return RedirectResponse(
            "/vehicle-profiles?error=weight",
            status_code=303,
        )

    if (
        fee is not None
        and fee < 0
    ):
        return RedirectResponse(
            "/vehicle-profiles?error=fee",
            status_code=303,
        )

    if (
        ref_weight is not None
        and ref_weight < 0
    ):
        return RedirectResponse(
            "/vehicle-profiles?error=weight",
            status_code=303,
        )

    save_vehicle_profile(
        vehicle_type,
        fee,
        ref_weight,
    )

    return RedirectResponse(
        "/vehicle-profiles?saved=1",
        status_code=303,
    )


@app.post(
    "/vehicle-profiles/{profile_id}/delete"
)
async def vehicle_profile_delete(
    request: Request,
    profile_id: int,
):
    require_login(request)

    conn = db()

    conn.execute(
        """
        DELETE
        FROM vehicle_profiles
        WHERE id=?
        """,
        (profile_id,),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        "/vehicle-profiles",
        status_code=303,
    )


@app.get(
    "/api/vehicle-profile"
)
async def vehicle_profile_api(
    request: Request,
    vehicle_type: str = "",
):
    require_login(request)

    row = get_vehicle_profile(
        vehicle_type
    )

    if not row:
        return {
            "found": False,
        }

    return {
        "found": True,
        "vehicle_type":
            row["vehicle_type"],
        "weighing_fee":
            row["weighing_fee"],
        "vehicle_weight":
            row["vehicle_weight"],
    }


# ============================================================
# WEIGH PAGE
# ============================================================

@app.get(
    "/weigh",
    response_class=HTMLResponse,
)
async def weigh_page(
    request: Request,
):
    require_login(request)

    conn = db()

    state = conn.execute(
        """
        SELECT *
        FROM scale_state
        WHERE id=1
        """
    ).fetchone()

    waiting_rows = conn.execute(
        """
        SELECT *
        FROM weighments
        WHERE
            weighing_mode='DOUBLE'
            AND status='WAITING_SECOND'
            AND second_weight IS NULL
        ORDER BY id DESC
        """
    ).fetchall()

    profiles = conn.execute(
        """
        SELECT
            vehicle_type,
            weighing_fee,
            vehicle_weight
        FROM vehicle_profiles
        ORDER BY vehicle_type COLLATE NOCASE
        """
    ).fetchall()

    conn.close()

    waiting = [
        {
            "row": row,
            "plate_parts":
                parse_iran_plate(
                    row["plate"]
                ),
        }
        for row in waiting_rows
    ]

    vehicle_profiles = [
        {
            "vehicle_type":
                p["vehicle_type"],

            "weighing_fee":
                p["weighing_fee"],

            "vehicle_weight":
                p["vehicle_weight"],
        }
        for p in profiles
    ]

    return templates.TemplateResponse(
        "weigh.html",
        {
            "request": request,
            "state": state,
            "waiting": waiting,
            "vehicle_profiles":
                vehicle_profiles,
            "user":
                request.session["user"],
        },
    )


# ============================================================
# CREATE WEIGHMENT
# ============================================================

@app.post("/weigh")
async def create_weighment(

    request: Request,

    plate: str = Form(...),

    weighing_mode: str = Form(
        "SINGLE"
    ),

    weight: float | None = Form(
        None
    ),

    manual_weight: str = Form(
        "0"
    ),

    vehicle_type: str | None = Form(
        None
    ),

    weighing_fee: str | None = Form(
        None
    ),

    vehicle_weight: str | None = Form(
        None
    ),

    driver_name: str | None = Form(
        None
    ),

    driver_phone: str | None = Form(
        None
    ),

    cargo_type: str | None = Form(
        None
    ),

    cargo_owner: str | None = Form(
        None
    ),

    origin: str | None = Form(
        None
    ),

    destination: str | None = Form(
        None
    ),

    document_no: str | None = Form(
        None
    ),

    notes: str | None = Form(
        None
    ),

    photo: list[UploadFile] | None = File(
        None
    ),
):
    require_login(request)

    plate = str(plate).strip()

    if not plate:
        return RedirectResponse(
            "/weigh?error=plate",
            status_code=303,
        )

    weighing_mode = (
        str(weighing_mode)
        .strip()
        .upper()
    )

    if weighing_mode not in {
        "SINGLE",
        "DOUBLE",
    }:
        weighing_mode = "SINGLE"

    fee = clean_optional_float(
        weighing_fee
    )

    ref_vehicle_weight = (
        clean_optional_float(
            vehicle_weight
        )
    )

    if (
        weighing_fee
        and str(
            weighing_fee
        ).strip()
        and fee is None
    ):
        return RedirectResponse(
            "/weigh?error=invalid_fee",
            status_code=303,
        )

    if (
        vehicle_weight
        and str(
            vehicle_weight
        ).strip()
        and ref_vehicle_weight is None
    ):
        return RedirectResponse(
            "/weigh?error=invalid_vehicle_weight",
            status_code=303,
        )

    if (
        fee is not None
        and fee < 0
    ):
        return RedirectResponse(
            "/weigh?error=invalid_fee",
            status_code=303,
        )

    if (
        ref_vehicle_weight is not None
        and ref_vehicle_weight < 0
    ):
        return RedirectResponse(
            "/weigh?error=invalid_vehicle_weight",
            status_code=303,
        )

    if weighing_mode == "DOUBLE":

        conn = db()

        existing = conn.execute(
            """
            SELECT ticket_number
            FROM weighments
            WHERE
                plate=?
                AND weighing_mode='DOUBLE'
                AND status='WAITING_SECOND'
                AND second_weight IS NULL
            LIMIT 1
            """,
            (plate,),
        ).fetchone()

        conn.close()

        if existing:
            return RedirectResponse(
                f"/weigh?error=open_double&ticket={existing['ticket_number']}",
                status_code=303,
            )

    is_manual_weight = form_bool(
        manual_weight
    )

    scale = get_scale_state()

    if is_manual_weight:

        actual_weight = (
            validate_manual_weight(
                weight
            )
        )

        if actual_weight is None:
            return RedirectResponse(
                "/weigh?error=invalid_manual_weight",
                status_code=303,
            )

        scale_id = (
            str(scale["scale_id"])
            if scale
            else "SCALE-01"
        )

    else:

        scale_error = (
            validate_live_scale(
                scale
            )
        )

        if scale_error:
            return RedirectResponse(
                f"/weigh?error={scale_error}",
                status_code=303,
            )

        actual_weight = float(
            scale["weight"]
        )

        scale_id = str(
            scale["scale_id"]
        )

    now = datetime.now(
        timezone.utc
    ).isoformat()

    operator = (
        request.session["user"]
    )

    vehicle_type = clean_text(
        vehicle_type
    )

    driver_name = clean_text(
        driver_name
    )

    driver_phone = clean_text(
        driver_phone
    )

    cargo_type = clean_text(
        cargo_type
    )

    cargo_owner = clean_text(
        cargo_owner
    )

    origin = clean_text(
        origin
    )

    destination = clean_text(
        destination
    )

    document_no = clean_text(
        document_no
    )

    notes = clean_text(
        notes
    )

    save_vehicle_profile(
        vehicle_type,
        fee,
        ref_vehicle_weight,
    )

    filenames = []

    if photo:
        allowed = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        }

        for upload in photo[:10]:

            if (
                not upload
                or not upload.filename
            ):
                continue

            ext = Path(
                upload.filename
            ).suffix.lower()

            if ext not in allowed:
                return RedirectResponse(
                    "/weigh?error=photo",
                    status_code=303,
                )

            content = (
                await upload.read()
            )

            if (
                len(content)
                > 10 * 1024 * 1024
            ):
                return RedirectResponse(
                    "/weigh?error=photo_size",
                    status_code=303,
                )

            filename = (
                uuid.uuid4().hex
                + ext
            )

            (
                UPLOAD_DIR / filename
            ).write_bytes(content)

            filenames.append(
                filename
            )

    first_photo = (
        filenames[0]
        if filenames
        else None
    )

    status = (
        "SAVED"
        if weighing_mode == "SINGLE"
        else "WAITING_SECOND"
    )

    conn = db()

    ticket = next_ticket(conn)

    cursor = conn.execute(
        """
        INSERT INTO weighments
        (
            ticket_number,
            plate,
            weight,
            unit,
            photo_filename,
            scale_id,
            operator,
            created_at,
            status,

            vehicle_type,
            weighing_fee,
            vehicle_weight,

            driver_name,
            driver_phone,
            cargo_type,
            cargo_owner,
            origin,
            destination,
            document_no,
            notes,

            weighing_mode,

            first_weight,
            first_weighed_at,
            first_operator,

            second_weight,
            second_weighed_at,
            second_operator,

            net_weight,

            first_weight_manual,
            second_weight_manual
        )

        VALUES
        (
            ?, ?, ?, 'kg',
            ?, ?, ?, ?, ?,

            ?, ?, ?,

            ?, ?, ?, ?, ?, ?, ?, ?,

            ?,

            ?, ?, ?,

            ?, ?, ?,

            ?,

            ?, ?
        )
        """,
        (
            ticket,
            plate,
            actual_weight,
            first_photo,
            scale_id,
            operator,
            now,
            status,

            vehicle_type,
            fee,
            ref_vehicle_weight,

            driver_name,
            driver_phone,
            cargo_type,
            cargo_owner,
            origin,
            destination,
            document_no,
            notes,

            weighing_mode,

            actual_weight,
            now,
            operator,

            None,
            None,
            None,

            None,

            1 if is_manual_weight else 0,
            0,
        ),
    )

    weighment_id = (
        cursor.lastrowid
    )

    for filename in filenames:

        conn.execute(
            """
            INSERT INTO weighment_photos
            (
                weighment_id,
                filename,
                created_at
            )
            VALUES (?, ?, ?)
            """,
            (
                weighment_id,
                filename,
                now,
            ),
        )

    conn.commit()
    conn.close()

    if weighing_mode == "DOUBLE":
        return RedirectResponse(
            f"/weighments/{ticket}?first_saved=1",
            status_code=303,
        )

    return RedirectResponse(
        f"/weighments/{ticket}?saved=1",
        status_code=303,
    )


# ============================================================
# SECOND WEIGH
# ============================================================

@app.post(
    "/weighments/{ticket}/second-weigh"
)
async def second_weigh(
    request: Request,
    ticket: int,

    manual_weight: str = Form(
        "0"
    ),

    weight: float | None = Form(
        None
    ),
):
    require_login(request)

    is_manual_weight = form_bool(
        manual_weight
    )

    if is_manual_weight:

        second_weight = (
            validate_manual_weight(
                weight
            )
        )

        if second_weight is None:
            return RedirectResponse(
                f"/weigh?error=invalid_manual_weight&ticket={ticket}",
                status_code=303,
            )

    else:

        scale = get_scale_state()

        scale_error = (
            validate_live_scale(
                scale
            )
        )

        if scale_error:
            return RedirectResponse(
                f"/weigh?error={scale_error}&ticket={ticket}",
                status_code=303,
            )

        second_weight = float(
            scale["weight"]
        )

    second_at = datetime.now(
        timezone.utc
    ).isoformat()

    second_operator = (
        request.session["user"]
    )

    conn = db()

    row = conn.execute(
        """
        SELECT *
        FROM weighments
        WHERE
            ticket_number=?
            AND weighing_mode='DOUBLE'
            AND status='WAITING_SECOND'
            AND second_weight IS NULL
        """,
        (ticket,),
    ).fetchone()

    if not row:
        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Open double weighment not found",
        )

    net = calculate_net_weight(
        row["first_weight"],
        second_weight,
    )

    conn.execute(
        """
        UPDATE weighments
        SET
            second_weight=?,
            second_weighed_at=?,
            second_operator=?,
            second_weight_manual=?,
            net_weight=?,
            weight=?,
            status='SAVED'
        WHERE id=?
        """,
        (
            second_weight,
            second_at,
            second_operator,
            1 if is_manual_weight else 0,
            net,
            net,
            row["id"],
        ),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        f"/weighments/{ticket}?second_saved=1",
        status_code=303,
    )


# ============================================================
# DETAIL
# ============================================================

@app.get(
    "/weighments/{ticket}",
    response_class=HTMLResponse,
)
async def detail(
    request: Request,
    ticket: int,
):
    require_login(request)

    conn = db()

    row = conn.execute(
        """
        SELECT *
        FROM weighments
        WHERE ticket_number=?
        """,
        (ticket,),
    ).fetchone()

    if not row:
        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    photo_rows = conn.execute(
        """
        SELECT filename
        FROM weighment_photos
        WHERE weighment_id=?
        ORDER BY id ASC
        """,
        (row["id"],),
    ).fetchall()

    photos = [
        p["filename"]
        for p in photo_rows
    ]

    if (
        not photos
        and row["photo_filename"]
    ):
        photos = [
            row["photo_filename"]
        ]

    plate_parts = (
        parse_iran_plate(
            row["plate"]
        )
    )

    conn.close()

    return templates.TemplateResponse(
        "detail.html",
        {
            "request": request,
            "row": row,
            "photos": photos,
            "plate_parts":
                plate_parts,
            "user":
                request.session["user"],
        },
    )


# ============================================================
# RECORDS
# ============================================================

@app.get(
    "/records",
    response_class=HTMLResponse,
)
async def records(
    request: Request,
    q: str = "",
):
    require_login(request)

    conn = db()

    q = q.strip()

    if q:
        like = f"%{q}%"

        normalized_like = (
            "%"
            + normalize_plate_search(q)
            + "%"
        )

        rows = conn.execute(
            """
            SELECT *
            FROM weighments
            WHERE
                plate LIKE ?

                OR REPLACE(
                    plate,
                    ' ',
                    ''
                ) LIKE ?

                OR CAST(
                    ticket_number
                    AS TEXT
                ) LIKE ?

                OR vehicle_type LIKE ?
                OR driver_name LIKE ?
                OR driver_phone LIKE ?
                OR cargo_type LIKE ?
                OR cargo_owner LIKE ?
                OR origin LIKE ?
                OR destination LIKE ?
                OR document_no LIKE ?
                OR notes LIKE ?

            ORDER BY id DESC
            """,
            (
                like,
                normalized_like,
                like,
                like,
                like,
                like,
                like,
                like,
                like,
                like,
                like,
                like,
            ),
        ).fetchall()

    else:
        rows = conn.execute(
            """
            SELECT *
            FROM weighments
            ORDER BY id DESC
            """
        ).fetchall()

    conn.close()

    plate_parts_map = {
        row["id"]:
            parse_iran_plate(
                row["plate"]
            )
        for row in rows
    }

    return templates.TemplateResponse(
        "records.html",
        {
            "request": request,
            "rows": rows,
            "q": q,
            "plate_parts_map":
                plate_parts_map,
            "user":
                request.session["user"],
        },
    )


# ============================================================
# DELETE WEIGHMENT
# ============================================================

@app.post(
    "/weighments/{ticket}/delete"
)
async def delete_weighment(
    request: Request,
    ticket: int,
    next: str = Form(
        "/records"
    ),
):
    require_login(request)

    if not next.startswith("/"):
        next = "/records"

    conn = db()

    row = conn.execute(
        """
        SELECT *
        FROM weighments
        WHERE ticket_number=?
        """,
        (ticket,),
    ).fetchone()

    if not row:
        conn.close()

        return RedirectResponse(
            next,
            status_code=303,
        )

    filenames = [
        p["filename"]
        for p in conn.execute(
            """
            SELECT filename
            FROM weighment_photos
            WHERE weighment_id=?
            """,
            (row["id"],),
        ).fetchall()
    ]

    conn.execute(
        """
        DELETE FROM weighment_photos
        WHERE weighment_id=?
        """,
        (row["id"],),
    )

    conn.execute(
        """
        DELETE FROM weighments
        WHERE id=?
        """,
        (row["id"],),
    )

    conn.commit()
    conn.close()

    for filename in filenames:
        try:
            path = (
                UPLOAD_DIR / filename
            )

            if path.exists():
                path.unlink()

        except Exception:
            pass

    return RedirectResponse(
        next,
        status_code=303,
    )


# ============================================================
# DEVICE PAGE
# ============================================================

@app.get(
    "/device",
    response_class=HTMLResponse,
)
async def device_page(
    request: Request,
):
    require_login(request)

    if SERIAL_MODE == "agent":
        cfg = load_device_config()
        ports = []

    else:
        cfg = serial_mgr.get_config()
        ports = serial_mgr.list_ports()

    return templates.TemplateResponse(
        "device.html",
        {
            "request": request,
            "cfg": cfg,
            "ports": ports,
            "serial_mode":
                SERIAL_MODE,
            "user":
                request.session["user"],
        },
    )


@app.post("/device/save")
async def device_save(
    request: Request,
    enabled: str = Form("0"),
    port: str = Form(""),
    baud: int = Form(2400),
    indicator: str = Form(
        "GENERIC_SIGNED_5_6"
    ),
    stable_tol: float = Form(
        1.0
    ),
    stable_seconds: float = Form(
        1.2
    ),
    send_every_sec: float = Form(
        0.3
    ),
    scale_id: str = Form(
        "SCALE-01"
    ),
    action: str = Form(
        "save"
    ),
):
    require_login(request)

    cfg = DeviceConfig(
        enabled=(
            enabled == "1"
        ),

        port=(
            port or ""
        ).strip(),

        baud=int(baud),

        indicator=str(
            indicator
        ),

        stable_tol=float(
            stable_tol
        ),

        stable_seconds=float(
            stable_seconds
        ),

        send_every_sec=float(
            send_every_sec
        ),

        scale_id=(
            scale_id
            or "SCALE-01"
        ).strip(),
    )

    if action == "stop":
        cfg.enabled = False

    elif action == "start":
        cfg.enabled = True

    elif (
        action == "autodetect"
        and SERIAL_MODE == "local"
    ):
        cfg.port = (
            serial_mgr.auto_detect_port()
        )

    save_device_config(cfg)
    serial_mgr.set_config(cfg)

    if SERIAL_MODE == "local":
        serial_mgr.stop()

        if cfg.enabled:
            serial_mgr.start(
                update_scale_state
            )

    return RedirectResponse(
        "/device",
        status_code=303,
    )


# ============================================================
# DEVICE STATUS
# ============================================================

@app.get("/api/device/status")
async def device_status(
    request: Request,
):
    require_login(request)

    if SERIAL_MODE == "agent":
        cfg = load_device_config()

        age = (
            time.time()
            - agent_state[
                "last_seen_ts"
            ]
            if agent_state[
                "last_seen_ts"
            ]
            else None
        )

        online = (
            age is not None
            and age < 5
        )

        return JSONResponse(
            {
                "mode": "agent",

                "running":
                    online
                    and agent_state[
                        "running"
                    ],

                "agent_online":
                    online,

                "cfg": {
                    "enabled":
                        cfg.enabled,
                    "port":
                        cfg.port,
                    "baud":
                        cfg.baud,
                    "indicator":
                        cfg.indicator,
                    "stable_tol":
                        cfg.stable_tol,
                    "stable_seconds":
                        cfg.stable_seconds,
                    "send_every_sec":
                        cfg.send_every_sec,
                    "scale_id":
                        cfg.scale_id,
                },

                "last_error":
                    agent_state[
                        "last_error"
                    ],

                "last_raw":
                    agent_state[
                        "last_raw"
                    ],

                "last_weight":
                    agent_state[
                        "last_weight"
                    ],

                "last_stable":
                    agent_state[
                        "last_stable"
                    ],

                "last_seen_ts":
                    agent_state[
                        "last_seen_ts"
                    ],

                "raw_lines":
                    agent_state[
                        "raw_lines"
                    ],
            }
        )

    cfg = serial_mgr.get_config()

    return JSONResponse(
        {
            "mode": "local",

            "running":
                serial_mgr.is_running(),

            "agent_online":
                False,

            "cfg": {
                "enabled":
                    cfg.enabled,
                "port":
                    cfg.port,
                "baud":
                    cfg.baud,
                "indicator":
                    cfg.indicator,
                "stable_tol":
                    cfg.stable_tol,
                "stable_seconds":
                    cfg.stable_seconds,
                "send_every_sec":
                    cfg.send_every_sec,
                "scale_id":
                    cfg.scale_id,
            },

            "last_error":
                serial_mgr.last_error,

            "last_raw":
                serial_mgr.last_raw,

            "last_weight":
                serial_mgr.last_weight,

            "last_stable":
                serial_mgr.last_stable,

            "last_seen_ts":
                serial_mgr.last_seen_ts,

            "raw_lines":
                list(
                    serial_mgr.raw_lines
                ),
        }
    )


# ============================================================
# AGENT
# ============================================================

def require_device_token(
    request: Request,
):
    token = request.headers.get(
        "X-Device-Token"
    )

    if token != DEVICE_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid device token",
        )


@app.get("/api/agent/config")
async def agent_config(
    request: Request,
):
    require_device_token(request)

    cfg = load_device_config()

    return {
        "enabled": cfg.enabled,
        "port": cfg.port,
        "baud": cfg.baud,
        "indicator": cfg.indicator,
        "stable_tol":
            cfg.stable_tol,
        "stable_seconds":
            cfg.stable_seconds,
        "send_every_sec":
            cfg.send_every_sec,
        "scale_id": cfg.scale_id,
    }


@app.post("/api/agent/status")
async def agent_status(
    request: Request,
):
    require_device_token(request)

    body = (
        await request.json()
    )

    agent_state["running"] = bool(
        body.get(
            "running",
            False,
        )
    )

    agent_state["last_error"] = str(
        body.get(
            "error",
            "",
        )
    )

    raw = str(
        body.get(
            "raw",
            "",
        )
    )

    agent_state["last_raw"] = raw

    agent_state["last_weight"] = (
        body.get("weight")
    )

    agent_state["last_stable"] = bool(
        body.get(
            "stable",
            False,
        )
    )

    agent_state["last_seen_ts"] = (
        time.time()
    )

    if raw:
        lines = agent_state[
            "raw_lines"
        ]

        if (
            not lines
            or lines[0] != raw
        ):
            lines.insert(
                0,
                raw,
            )

        del lines[80:]

    return {
        "ok": True
    }


# ============================================================
# SCALE API
# ============================================================

@app.get("/api/scale/weight")
async def get_scale_weight(
    request: Request,
):
    conn = db()

    row = conn.execute(
        """
        SELECT *
        FROM scale_state
        WHERE id=1
        """
    ).fetchone()

    conn.close()

    return JSONResponse(
        {
            "scale_id":
                row["scale_id"],

            "weight":
                row["weight"],

            "unit":
                "kg",

            "stable":
                bool(
                    row["stable"]
                ),

            "updated_at":
                row["updated_at"],
        }
    )


@app.post("/api/scale/weight")
async def set_scale_weight(
    request: Request,
):
    require_device_token(request)

    body = (
        await request.json()
    )

    try:
        weight = float(
            body["weight"]
        )

        stable = bool(
            body.get(
                "stable",
                False,
            )
        )

        scale_id = str(
            body.get(
                "scale_id",
                "SCALE-01",
            )
        )

    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON",
        )

    if not (
        -1000000
        <= weight
        <= 1000000
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid weight",
        )

    update_scale_state(
        weight,
        stable,
        scale_id,
    )

    return {
        "ok": True,
        "weight": weight,
        "stable": stable,
        "scale_id": scale_id,
    }
