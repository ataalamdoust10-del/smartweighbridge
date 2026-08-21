import os
import re
import time
import sqlite3
import uuid
import secrets
import string

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
from passlib.context import CryptContext

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
    os.getenv("SWB_MAX_SCALE_AGE_SEC", "5")
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

# این نسخه Local است.
APP_MODE = "local"

# هر مرورگر/دستگاه یک شناسه مستقل دریافت می‌کند.
DEVICE_COOKIE = "swb_device_id"

# اگر در این تعداد ثانیه heartbeat دریافت شده باشد دستگاه آنلاین است.
ONLINE_SEC = 35

pwd_ctx = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

LICENSE_ALPHABET = (
    string.ascii_uppercase
    + string.digits
)


def now_iso():
    return datetime.now(
        timezone.utc
    ).isoformat()


def parse_datetime(value):
    dt = datetime.fromisoformat(
        str(value).replace(
            "Z",
            "+00:00",
        )
    )

    if dt.tzinfo is None:
        dt = dt.replace(
            tzinfo=timezone.utc
        )

    return dt


def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    try:
        return pwd_ctx.verify(
            password,
            password_hash,
        )
    except Exception:
        return False


def make_license(length: int = 10) -> str:
    return "".join(
        secrets.choice(
            LICENSE_ALPHABET
        )
        for _ in range(length)
    )


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
    same_site="lax",
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

templates.env.globals["APP_MODE"] = APP_MODE

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


@app.middleware("http")
async def ensure_device_id(
    request: Request,
    call_next,
):
    device_id = request.cookies.get(
        DEVICE_COOKIE
    )

    created = False

    if not device_id:
        device_id = uuid.uuid4().hex
        created = True

    request.state.device_id = device_id

    response = await call_next(
        request
    )

    if created:
        response.set_cookie(
            DEVICE_COOKIE,
            device_id,
            max_age=60 * 60 * 24 * 365 * 5,
            samesite="lax",
            httponly=True,
        )

    return response


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

    return translate(
        lang,
        key,
    )


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

    conn.execute(
        "PRAGMA busy_timeout = 30000"
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

        "density":
            "density REAL",

        "unit_price":
            "unit_price REAL",

        "cargo_value":
            "cargo_value REAL",
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

            updated_at TEXT NOT NULL
                DEFAULT(datetime('now'))
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

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT NOT NULL UNIQUE,

            password_hash TEXT NOT NULL,

            role TEXT NOT NULL
                CHECK(role IN ('admin','operator')),

            is_active INTEGER NOT NULL DEFAULT 1,

            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS user_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            device_id TEXT NOT NULL,

            device_name TEXT,

            is_active INTEGER NOT NULL DEFAULT 1,

            activated_at TEXT NOT NULL,

            last_seen_at TEXT,

            last_ip TEXT,

            last_user_agent TEXT,

            revoked_at TEXT,

            UNIQUE(user_id, device_id),

            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS activation_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            device_id TEXT NOT NULL,

            license_code TEXT NOT NULL UNIQUE,

            created_at TEXT NOT NULL,

            used_at TEXT,

            status TEXT NOT NULL DEFAULT 'PENDING'
                CHECK(
                    status IN (
                        'PENDING',
                        'USED',
                        'REVOKED'
                    )
                ),

            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS
            idx_users_username
        ON users(username);

        CREATE INDEX IF NOT EXISTS
            idx_user_devices_user
        ON user_devices(user_id);

        CREATE INDEX IF NOT EXISTS
            idx_user_devices_last_seen
        ON user_devices(last_seen_at);

        CREATE INDEX IF NOT EXISTS
            idx_activation_requests_user
        ON activation_requests(user_id);
        """
    )

    ensure_weighment_columns(
        conn
    )

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
            OR weighing_mode=''
            OR first_weight IS NULL
            OR first_weight_manual IS NULL
            OR second_weight_manual IS NULL
        """
    )

    conn.commit()
    conn.close()


def ensure_admin_seed():
    conn = db()

    try:
        row = conn.execute(
            """
            SELECT *
            FROM users
            WHERE username=?
            """,
            (USERNAME,),
        ).fetchone()

        if not row:
            conn.execute(
                """
                INSERT INTO users(
                    username,
                    password_hash,
                    role,
                    is_active,
                    created_at
                )
                VALUES(
                    ?,
                    ?,
                    'admin',
                    1,
                    ?
                )
                """,
                (
                    USERNAME,
                    hash_password(PASSWORD),
                    now_iso(),
                ),
            )

            conn.commit()
            return

        if row["role"] != "admin":
            raise RuntimeError(
                "SWB_USERNAME belongs to a non-admin user."
            )

        updates = []
        params = []

        if not bool(
            row["is_active"]
        ):
            updates.append(
                "is_active=1"
            )

        if not verify_password(
            PASSWORD,
            row["password_hash"],
        ):
            updates.append(
                "password_hash=?"
            )

            params.append(
                hash_password(PASSWORD)
            )

        if updates:
            params.append(
                int(row["id"])
            )

            conn.execute(
                f"""
                UPDATE users
                SET {", ".join(updates)}
                WHERE id=?
                """,
                tuple(params),
            )

            conn.commit()

    finally:
        conn.close()


init_db()
ensure_admin_seed()


# ============================================================
# AUTH HELPERS
# ============================================================

def get_user_by_username(
    conn,
    username,
):
    return conn.execute(
        """
        SELECT *
        FROM users
        WHERE username=?
        """,
        (
            str(username).strip(),
        ),
    ).fetchone()


def get_user_by_id(
    conn,
    user_id,
):
    return conn.execute(
        """
        SELECT *
        FROM users
        WHERE id=?
        """,
        (
            int(user_id),
        ),
    ).fetchone()


def logged_in(request):
    return bool(
        request.session.get(
            "user_id"
        )
    )


def device_is_activated(
    conn,
    user_id,
    device_id,
):
    row = conn.execute(
        """
        SELECT 1
        FROM user_devices

        WHERE
            user_id=?
            AND device_id=?
            AND is_active=1
        """,
        (
            int(user_id),
            str(device_id),
        ),
    ).fetchone()

    return bool(row)


def touch_operator_device(
    conn,
    user_id,
    device_id,
    request,
):
    ip = (
        request.client.host
        if request.client
        else None
    )

    user_agent = request.headers.get(
        "user-agent",
        "",
    )

    conn.execute(
        """
        UPDATE user_devices

        SET
            last_seen_at=?,
            last_ip=?,
            last_user_agent=?

        WHERE
            user_id=?
            AND device_id=?
            AND is_active=1
        """,
        (
            now_iso(),
            ip,
            user_agent,
            int(user_id),
            str(device_id),
        ),
    )


def require_login(request):
    user_id = request.session.get(
        "user_id"
    )

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Login required",
        )

    conn = db()

    user = get_user_by_id(
        conn,
        user_id,
    )

    if (
        not user
        or not bool(
            user["is_active"]
        )
    ):
        conn.close()

        request.session.clear()

        raise HTTPException(
            status_code=401,
            detail="Inactive user",
        )

    if user["role"] == "operator":

        if not device_is_activated(
            conn,
            user["id"],
            request.state.device_id,
        ):
            conn.close()

            request.session.clear()

            raise HTTPException(
                status_code=401,
                detail="Device authorization revoked",
            )

        touch_operator_device(
            conn,
            user["id"],
            request.state.device_id,
            request,
        )

        conn.commit()

    conn.close()

    request.state.user = user

    return user


def require_roles(
    request,
    *roles,
):
    user = require_login(
        request
    )

    if user["role"] not in roles:
        raise HTTPException(
            status_code=403,
            detail="Forbidden",
        )

    return user


def is_online(last_seen_at):
    if not last_seen_at:
        return False

    try:
        age = (
            datetime.now(
                timezone.utc
            )
            - parse_datetime(
                last_seen_at
            )
        ).total_seconds()

        return age <= ONLINE_SEC

    except Exception:
        return False


# ============================================================
# GENERAL HELPERS
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

    return int(
        row["n"]
    )


def clean_text(value):
    if value is None:
        return None

    value = str(
        value
    ).strip()

    return (
        value
        if value
        else None
    )


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


def calculate_net_weight(
    first_weight,
    second_weight,
):
    return abs(
        abs(float(first_weight))
        -
        abs(float(second_weight))
    )


def calculate_cargo_value(
    weight,
    unit_price,
):
    if (
        weight is None
        or unit_price is None
    ):
        return None

    return (
        abs(float(weight))
        * float(unit_price)
    )


def validate_manual_weight(value):
    if value is None:
        return None

    try:
        number = float(value)

    except (
        TypeError,
        ValueError,
    ):
        return None

    if not (
        0 <= number <= 1000000
    ):
        return None

    return number


# ============================================================
# VEHICLE PROFILES HELPERS
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


def get_vehicle_profile(
    vehicle_type,
):
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

    conn = db()

    existing = conn.execute(
        """
        SELECT *
        FROM vehicle_profiles
        WHERE vehicle_key=?
        """,
        (key,),
    ).fetchone()

    now = now_iso()

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
            INSERT INTO vehicle_profiles(
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


def maybe_save_vehicle_profile(
    request,
    vehicle_type,
    fee,
    vehicle_weight,
):
    role = request.session.get(
        "role"
    )

    if role == "admin":
        save_vehicle_profile(
            vehicle_type,
            fee,
            vehicle_weight,
        )

        return

    if (
        role == "operator"
        and vehicle_type
        and not get_vehicle_profile(
            vehicle_type
        )
    ):
        save_vehicle_profile(
            vehicle_type,
            fee,
            vehicle_weight,
        )


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
        "first":
            match.group(1),

        "letter":
            match.group(2),

        "middle":
            match.group(3),

        "city":
            match.group(4),
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
                state["updated_at"]
            )
        ).total_seconds()

        if age > MAX_SCALE_AGE_SEC:
            return "stale"

    except Exception:
        return "stale"

    return None


# ============================================================
# DEVICE CONFIG
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
            now_iso(),
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
            now_iso(),
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

    serial_mgr.set_config(
        cfg
    )

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
# AUTH ROUTES
# ============================================================

@app.get("/")
async def home(
    request: Request,
):
    if not logged_in(
        request
    ):
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
    # هر Login قبلی را پاک می‌کنیم.
    request.session.clear()

    conn = db()

    user = get_user_by_username(
        conn,
        username,
    )

    if (
        not user
        or not bool(
            user["is_active"]
        )
        or not verify_password(
            password,
            user["password_hash"],
        )
    ):
        conn.close()

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

    # Admin هیچ Activation لازم ندارد.
    if user["role"] == "admin":
        request.session[
            "user_id"
        ] = int(
            user["id"]
        )

        request.session[
            "user"
        ] = str(
            user["username"]
        )

        request.session[
            "role"
        ] = "admin"

        conn.close()

        return RedirectResponse(
            "/dashboard",
            status_code=303,
        )

    device_id = (
        request.state.device_id
    )

    # اگر این دستگاه قبلاً فعال شده، مستقیم Login.
    if device_is_activated(
        conn,
        user["id"],
        device_id,
    ):
        touch_operator_device(
            conn,
            user["id"],
            device_id,
            request,
        )

        conn.commit()
        conn.close()

        request.session[
            "user_id"
        ] = int(
            user["id"]
        )

        request.session[
            "user"
        ] = str(
            user["username"]
        )

        request.session[
            "role"
        ] = "operator"

        return RedirectResponse(
            "/dashboard",
            status_code=303,
        )

    # دستگاه جدید:
    # یک درخواست Pending موجود را دوباره استفاده می‌کنیم.
    pending = conn.execute(
        """
        SELECT *
        FROM activation_requests

        WHERE
            user_id=?
            AND device_id=?
            AND status='PENDING'

        ORDER BY id DESC
        LIMIT 1
        """,
        (
            int(user["id"]),
            str(device_id),
        ),
    ).fetchone()

    if not pending:

        # احتمال collision تقریباً صفر است؛
        # با این حال uniqueness دیتابیس هم داریم.
        while True:
            code = make_license(10)

            exists = conn.execute(
                """
                SELECT 1
                FROM activation_requests
                WHERE license_code=?
                """,
                (code,),
            ).fetchone()

            if not exists:
                break

        conn.execute(
            """
            INSERT INTO activation_requests(
                user_id,
                device_id,
                license_code,
                created_at,
                status
            )

            VALUES(
                ?,
                ?,
                ?,
                ?,
                'PENDING'
            )
            """,
            (
                int(user["id"]),
                str(device_id),
                code,
                now_iso(),
            ),
        )

        conn.commit()

    conn.close()

    request.session[
        "preauth_user_id"
    ] = int(
        user["id"]
    )

    request.session[
        "preauth_username"
    ] = str(
        user["username"]
    )

    return RedirectResponse(
        "/activate",
        status_code=303,
    )


@app.get(
    "/activate",
    response_class=HTMLResponse,
)
async def activate_page(
    request: Request,
):
    if not request.session.get(
        "preauth_user_id"
    ):
        return RedirectResponse(
            "/login",
            status_code=303,
        )

    return templates.TemplateResponse(
        "activate.html",
        {
            "request": request,

            "error": None,

            "username":
                request.session.get(
                    "preauth_username"
                ),
        },
    )


@app.post("/activate")
async def activate_submit(
    request: Request,

    license_code: str = Form(...),

    device_name: str = Form(""),
):
    user_id = request.session.get(
        "preauth_user_id"
    )

    if not user_id:
        return RedirectResponse(
            "/login",
            status_code=303,
        )

    code = (
        str(license_code)
        .strip()
        .upper()
    )

    device_id = (
        request.state.device_id
    )

    device_name = clean_text(
        device_name
    )

    conn = db()

    user = get_user_by_id(
        conn,
        user_id,
    )

    if (
        not user
        or user["role"] != "operator"
        or not bool(
            user["is_active"]
        )
    ):
        conn.close()

        request.session.clear()

        return RedirectResponse(
            "/login",
            status_code=303,
        )

    reqrow = conn.execute(
        """
        SELECT *
        FROM activation_requests

        WHERE
            user_id=?
            AND device_id=?
            AND license_code=?
            AND status='PENDING'

        ORDER BY id DESC
        LIMIT 1
        """,
        (
            int(user_id),
            str(device_id),
            code,
        ),
    ).fetchone()

    if not reqrow:
        conn.close()

        return templates.TemplateResponse(
            "activate.html",
            {
                "request": request,

                "error":
                    "کد فعال‌سازی نامعتبر است.",

                "username":
                    request.session.get(
                        "preauth_username"
                    ),
            },
            status_code=400,
        )

    now = now_iso()

    ip = (
        request.client.host
        if request.client
        else None
    )

    user_agent = request.headers.get(
        "user-agent",
        "",
    )

    conn.execute(
        """
        INSERT INTO user_devices(
            user_id,
            device_id,
            device_name,
            is_active,
            activated_at,
            last_seen_at,
            last_ip,
            last_user_agent,
            revoked_at
        )

        VALUES(
            ?,
            ?,
            ?,
            1,
            ?,
            ?,
            ?,
            ?,
            NULL
        )

        ON CONFLICT(user_id, device_id)
        DO UPDATE SET
            device_name=
                COALESCE(
                    excluded.device_name,
                    user_devices.device_name
                ),

            is_active=1,

            activated_at=
                excluded.activated_at,

            last_seen_at=
                excluded.last_seen_at,

            last_ip=
                excluded.last_ip,

            last_user_agent=
                excluded.last_user_agent,

            revoked_at=NULL
        """,
        (
            int(user_id),
            str(device_id),
            device_name,
            now,
            now,
            ip,
            user_agent,
        ),
    )

    conn.execute(
        """
        UPDATE activation_requests

        SET
            status='USED',
            used_at=?

        WHERE id=?
        """,
        (
            now,
            int(reqrow["id"]),
        ),
    )

    conn.commit()
    conn.close()

    request.session.pop(
        "preauth_user_id",
        None,
    )

    request.session.pop(
        "preauth_username",
        None,
    )

    request.session[
        "user_id"
    ] = int(
        user["id"]
    )

    request.session[
        "user"
    ] = str(
        user["username"]
    )

    request.session[
        "role"
    ] = "operator"

    return RedirectResponse(
        "/dashboard",
        status_code=303,
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


@app.post("/api/heartbeat")
async def heartbeat(
    request: Request,
):
    user = require_login(
        request
    )

    return {
        "ok": True,
        "role": user["role"],
    }


# base.html فعلی این Endpoint را صدا می‌زند.
# Sync در این نسخه عمداً غیرفعال است.
@app.get("/api/sync/status")
async def local_sync_status(
    request: Request,
):
    require_roles(
        request,
        "admin",
        "operator",
    )

    return JSONResponse(
        {
            "mode": "local",
            "running": True,
            "cloud_online": False,
            "pending": 0,
            "last_success": None,
            "last_error": "",
            "cloud_records": 0,
        }
    )


# ============================================================
# ADMIN / OPERATOR MANAGEMENT
# ============================================================

@app.get("/admin")
async def admin_home(
    request: Request,
):
    require_roles(
        request,
        "admin",
    )

    return RedirectResponse(
        "/admin/operators",
        status_code=303,
    )


@app.get(
    "/admin/operators",
    response_class=HTMLResponse,
)
async def admin_operators(
    request: Request,
):
    require_roles(
        request,
        "admin",
    )

    conn = db()

    operators = conn.execute(
        """
        SELECT
            id,
            username,
            is_active,
            created_at

        FROM users

        WHERE role='operator'

        ORDER BY id DESC
        """
    ).fetchall()

    devices = conn.execute(
        """
        SELECT *
        FROM user_devices
        ORDER BY id DESC
        """
    ).fetchall()

    pending = conn.execute(
        """
        SELECT *
        FROM activation_requests

        WHERE status='PENDING'

        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    devices_by_user = {}

    for device in devices:

        item = {
            "device_id":
                device["device_id"],

            "device_name":
                device["device_name"],

            "is_active":
                bool(
                    device["is_active"]
                ),

            "activated_at":
                device["activated_at"],

            "last_seen_at":
                device["last_seen_at"],

            "online":
                (
                    bool(
                        device["is_active"]
                    )
                    and is_online(
                        device["last_seen_at"]
                    )
                ),

            "revoked_at":
                device["revoked_at"],
        }

        devices_by_user.setdefault(
            int(
                device["user_id"]
            ),
            [],
        ).append(item)

    pending_by_user = {}

    for req in pending:
        pending_by_user.setdefault(
            int(
                req["user_id"]
            ),
            [],
        ).append(
            {
                "id":
                    int(req["id"]),

                "device_id":
                    req["device_id"],

                "license_code":
                    req["license_code"],

                "created_at":
                    req["created_at"],
            }
        )

    online_map = {}

    for operator in operators:
        uid = int(
            operator["id"]
        )

        online_map[uid] = any(
            item["online"]
            for item in devices_by_user.get(
                uid,
                [],
            )
        )

    return templates.TemplateResponse(
        "admin_operators.html",
        {
            "request": request,

            "ops": operators,

            "devices_by_user":
                devices_by_user,

            "pending_by_user":
                pending_by_user,

            "online_map":
                online_map,

            # برای compatibility با template.
            # محدودیت تعداد دستگاه نداریم.
            "max_devices": None,

            "user":
                request.session.get(
                    "user"
                ),

            "role":
                request.session.get(
                    "role"
                ),
        },
    )


@app.post(
    "/admin/operators/create"
)
async def admin_create_operator(
    request: Request,

    username: str = Form(...),

    password: str = Form(...),
):
    require_roles(
        request,
        "admin",
    )

    username = (
        str(username)
        .strip()
    )

    if (
        len(username) < 3
        or len(username) > 50
        or len(password) < 4
    ):
        return RedirectResponse(
            "/admin/operators?error=invalid",
            status_code=303,
        )

    conn = db()

    try:
        conn.execute(
            """
            INSERT INTO users(
                username,
                password_hash,
                role,
                is_active,
                created_at
            )

            VALUES(
                ?,
                ?,
                'operator',
                1,
                ?
            )
            """,
            (
                username,
                hash_password(
                    password
                ),
                now_iso(),
            ),
        )

        conn.commit()

    except sqlite3.IntegrityError:
        conn.close()

        return RedirectResponse(
            "/admin/operators?error=username_exists",
            status_code=303,
        )

    conn.close()

    return RedirectResponse(
        "/admin/operators?created=1",
        status_code=303,
    )


@app.post(
    "/admin/operators/{user_id}/disable"
)
async def admin_disable_operator(
    request: Request,
    user_id: int,
):
    require_roles(
        request,
        "admin",
    )

    now = now_iso()

    conn = db()

    conn.execute(
        """
        UPDATE users

        SET is_active=0

        WHERE
            id=?
            AND role='operator'
        """,
        (int(user_id),),
    )

    # Disable شدن اپراتور تمام دستگاه‌های فعلی‌اش را هم باطل می‌کند.
    conn.execute(
        """
        UPDATE user_devices

        SET
            is_active=0,
            revoked_at=?

        WHERE user_id=?
        """,
        (
            now,
            int(user_id),
        ),
    )

    conn.execute(
        """
        UPDATE activation_requests

        SET status='REVOKED'

        WHERE
            user_id=?
            AND status='PENDING'
        """,
        (int(user_id),),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        "/admin/operators",
        status_code=303,
    )


@app.post(
    "/admin/operators/{user_id}/enable"
)
async def admin_enable_operator(
    request: Request,
    user_id: int,
):
    require_roles(
        request,
        "admin",
    )

    conn = db()

    conn.execute(
        """
        UPDATE users

        SET is_active=1

        WHERE
            id=?
            AND role='operator'
        """,
        (int(user_id),),
    )

    conn.commit()
    conn.close()

    # دستگاه‌های revoke شده خودکار برنمی‌گردند.
    # ورود بعدی درخواست Activation جدید می‌سازد.
    return RedirectResponse(
        "/admin/operators",
        status_code=303,
    )


@app.post(
    "/admin/operators/{user_id}/delete"
)
async def admin_delete_operator(
    request: Request,
    user_id: int,
):
    require_roles(
        request,
        "admin",
    )

    conn = db()

    conn.execute(
        """
        DELETE FROM users

        WHERE
            id=?
            AND role='operator'
        """,
        (int(user_id),),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        "/admin/operators",
        status_code=303,
    )


@app.post(
    "/admin/operators/{user_id}/devices/{device_id}/revoke"
)
async def admin_revoke_device(
    request: Request,
    user_id: int,
    device_id: str,
):
    require_roles(
        request,
        "admin",
    )

    now = now_iso()

    conn = db()

    conn.execute(
        """
        UPDATE user_devices

        SET
            is_active=0,
            revoked_at=?

        WHERE
            user_id=?
            AND device_id=?
        """,
        (
            now,
            int(user_id),
            str(device_id),
        ),
    )

    conn.execute(
        """
        UPDATE activation_requests

        SET status='REVOKED'

        WHERE
            user_id=?
            AND device_id=?
            AND status='PENDING'
        """,
        (
            int(user_id),
            str(device_id),
        ),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        "/admin/operators",
        status_code=303,
    )


@app.post(
    "/admin/activation/{req_id}/revoke"
)
async def admin_revoke_activation(
    request: Request,
    req_id: int,
):
    require_roles(
        request,
        "admin",
    )

    conn = db()

    conn.execute(
        """
        UPDATE activation_requests

        SET status='REVOKED'

        WHERE
            id=?
            AND status='PENDING'
        """,
        (int(req_id),),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        "/admin/operators",
        status_code=303,
    )


# ============================================================
# OPEN DOUBLE HELPERS
# ============================================================

def get_open_double_by_plate(
    plate,
):
    conn = db()

    row = conn.execute(
        """
        SELECT *
        FROM weighments

        WHERE
            plate=?
            AND weighing_mode='DOUBLE'
            AND status='WAITING_SECOND'
            AND second_weight IS NULL

        ORDER BY id DESC
        LIMIT 1
        """,
        (
            str(plate).strip(),
        ),
    ).fetchone()

    conn.close()

    return row
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
    require_roles(
        request,
        "admin",
        "operator",
    )

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
                float(
                    total_weight or 0
                ),
                2,
            ),

            "user":
                request.session["user"],

            "app_mode":
                APP_MODE,
        },
    )


# ============================================================
# VEHICLE PROFILES
# ============================================================

@app.get(
    "/vehicle-profiles",
    response_class=HTMLResponse,
)
async def vehicle_profiles_page(
    request: Request,
):
    require_roles(
        request,
        "admin",
        "operator",
    )

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

    weighing_fee: str = Form(""),

    vehicle_weight: str = Form(""),
):
    user = require_roles(
        request,
        "admin",
        "operator",
    )

    vehicle_type = clean_text(
        vehicle_type
    )

    if not vehicle_type:
        return RedirectResponse(
            "/vehicle-profiles",
            status_code=303,
        )

    # Operator فقط اجازه افزودن پروفایل جدید دارد.
    if user["role"] == "operator":

        existing = get_vehicle_profile(
            vehicle_type
        )

        if existing:
            return RedirectResponse(
                "/vehicle-profiles?error=no_edit_permission",
                status_code=303,
            )

    fee = clean_optional_float(
        weighing_fee
    )

    ref_weight = clean_optional_float(
        vehicle_weight
    )

    if (
        str(weighing_fee).strip()
        and fee is None
    ):
        return RedirectResponse(
            "/vehicle-profiles?error=fee",
            status_code=303,
        )

    if (
        str(vehicle_weight).strip()
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
    # حذف تعرفه فقط Admin.
    require_roles(
        request,
        "admin",
    )

    conn = db()

    conn.execute(
        """
        DELETE
        FROM vehicle_profiles
        WHERE id=?
        """,
        (
            int(profile_id),
        ),
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
    require_roles(
        request,
        "admin",
        "operator",
    )

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
# OPEN DOUBLE API
# ============================================================

@app.get(
    "/api/open-weighment"
)
async def open_weighment_api(
    request: Request,
    plate: str = "",
):
    require_roles(
        request,
        "admin",
        "operator",
    )

    plate = str(
        plate
    ).strip()

    if not plate:
        return {
            "found": False,
        }

    row = get_open_double_by_plate(
        plate
    )

    if not row:
        return {
            "found": False,
        }

    return {
        "found": True,

        "ticket_number":
            row["ticket_number"],

        "plate":
            row["plate"],

        "first_weight":
            row["first_weight"],

        "first_weight_manual":
            bool(
                row["first_weight_manual"]
            ),

        "first_weighed_at":
            row["first_weighed_at"],

        "first_operator":
            row["first_operator"],

        "vehicle_type":
            row["vehicle_type"],

        "weighing_fee":
            row["weighing_fee"],

        "vehicle_weight":
            row["vehicle_weight"],

        "driver_name":
            row["driver_name"],

        "driver_phone":
            row["driver_phone"],

        "cargo_type":
            row["cargo_type"],

        "cargo_owner":
            row["cargo_owner"],

        "density":
            row["density"],

        "unit_price":
            row["unit_price"],

        "origin":
            row["origin"],

        "destination":
            row["destination"],

        "document_no":
            row["document_no"],

        "notes":
            row["notes"],
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
    require_roles(
        request,
        "admin",
        "operator",
    )

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
                profile[
                    "vehicle_type"
                ],

            "weighing_fee":
                profile[
                    "weighing_fee"
                ],

            "vehicle_weight":
                profile[
                    "vehicle_weight"
                ],
        }

        for profile in profiles
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
# CREATE / COMPLETE WEIGHMENT
# ============================================================

@app.post("/weigh")
async def create_weighment(

    request: Request,

    plate: str = Form(...),

    weighing_mode: str = Form(
        "SINGLE"
    ),

    open_ticket: str = Form(
        ""
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

    density: str | None = Form(
        None
    ),

    unit_price: str | None = Form(
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
    require_roles(
        request,
        "admin",
        "operator",
    )

    plate = str(
        plate
    ).strip()

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

    density_value = (
        clean_optional_float(
            density
        )
    )

    unit_price_value = (
        clean_optional_float(
            unit_price
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
        density
        and str(
            density
        ).strip()
        and density_value is None
    ):
        return RedirectResponse(
            "/weigh?error=invalid_density",
            status_code=303,
        )

    if (
        unit_price
        and str(
            unit_price
        ).strip()
        and unit_price_value is None
    ):
        return RedirectResponse(
            "/weigh?error=invalid_unit_price",
            status_code=303,
        )

    for (
        value,
        error_name,
    ) in (
        (
            fee,
            "invalid_fee",
        ),
        (
            ref_vehicle_weight,
            "invalid_vehicle_weight",
        ),
        (
            density_value,
            "invalid_density",
        ),
        (
            unit_price_value,
            "invalid_unit_price",
        ),
    ):

        if (
            value is not None
            and value < 0
        ):
            return RedirectResponse(
                f"/weigh?error={error_name}",
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
            str(
                scale["scale_id"]
            )
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

    now = now_iso()

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

    open_ticket_value = None

    if str(
        open_ticket
    ).strip():

        try:
            open_ticket_value = int(
                str(
                    open_ticket
                ).strip()
            )

        except ValueError:
            open_ticket_value = None


    # ========================================================
    # COMPLETE EXISTING DOUBLE
    # ========================================================

    if open_ticket_value is not None:

        conn = db()

        row = conn.execute(
            """
            SELECT *
            FROM weighments

            WHERE
                ticket_number=?
                AND plate=?
                AND weighing_mode='DOUBLE'
                AND status='WAITING_SECOND'
                AND second_weight IS NULL
            """,
            (
                open_ticket_value,
                plate,
            ),
        ).fetchone()

        if not row:

            conn.close()

            return RedirectResponse(
                "/weigh?error=open_double_not_found",
                status_code=303,
            )

        net = calculate_net_weight(
            row["first_weight"],
            actual_weight,
        )

        cargo_value = (
            calculate_cargo_value(
                net,
                unit_price_value,
            )
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
                status='SAVED',

                vehicle_type=?,
                weighing_fee=?,
                vehicle_weight=?,

                driver_name=?,
                driver_phone=?,

                cargo_type=?,
                cargo_owner=?,

                density=?,
                unit_price=?,
                cargo_value=?,

                origin=?,
                destination=?,
                document_no=?,
                notes=?,

                scale_id=?

            WHERE id=?
            """,
            (
                actual_weight,
                now,
                operator,

                (
                    1
                    if is_manual_weight
                    else 0
                ),

                net,
                net,

                vehicle_type,
                fee,
                ref_vehicle_weight,

                driver_name,
                driver_phone,

                cargo_type,
                cargo_owner,

                density_value,
                unit_price_value,
                cargo_value,

                origin,
                destination,
                document_no,
                notes,

                scale_id,

                row["id"],
            ),
        )

        conn.commit()
        conn.close()

        maybe_save_vehicle_profile(
            request,
            vehicle_type,
            fee,
            ref_vehicle_weight,
        )

        return RedirectResponse(
            f"/weighments/{open_ticket_value}?second_saved=1",
            status_code=303,
        )


    # ========================================================
    # PREVENT DUPLICATE OPEN DOUBLE
    # ========================================================

    if weighing_mode == "DOUBLE":

        existing = (
            get_open_double_by_plate(
                plate
            )
        )

        if existing:
            return RedirectResponse(
                (
                    "/weigh"
                    "?error=open_double"
                    f"&ticket={existing['ticket_number']}"
                ),
                status_code=303,
            )


    # ذخیره خودکار تعرفه:
    # Admin می‌تواند update کند، Operator فقط نوع جدید.
    maybe_save_vehicle_profile(
        request,
        vehicle_type,
        fee,
        ref_vehicle_weight,
    )


    # ========================================================
    # PHOTOS
    # ========================================================

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
                UPLOAD_DIR
                / filename
            ).write_bytes(
                content
            )

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

    cargo_value = (
        calculate_cargo_value(
            actual_weight,
            unit_price_value,
        )
        if weighing_mode == "SINGLE"
        else None
    )

    conn = db()

    ticket = next_ticket(
        conn
    )

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
            second_weight_manual,

            density,
            unit_price,
            cargo_value
        )

        VALUES
        (
            ?, ?, ?, 'kg',

            ?,

            ?, ?, ?, ?,

            ?, ?, ?,

            ?, ?,

            ?, ?,

            ?, ?,

            ?, ?,

            ?,

            ?, ?, ?,

            ?, ?, ?,

            ?,

            ?, ?,

            ?, ?, ?
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

            (
                1
                if is_manual_weight
                else 0
            ),

            0,

            density_value,
            unit_price_value,
            cargo_value,
        ),
    )

    weighment_id = (
        cursor.lastrowid
    )

    for filename in filenames:

        conn.execute(
            """
            INSERT INTO weighment_photos(
                weighment_id,
                filename,
                created_at
            )

            VALUES(
                ?,
                ?,
                ?
            )
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
    require_roles(
        request,
        "admin",
        "operator",
    )

    is_manual_weight = (
        form_bool(
            manual_weight
        )
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

    second_at = now_iso()

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
        (
            ticket,
        ),
    ).fetchone()

    if not row:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail=(
                "Open double weighment not found"
            ),
        )

    net = calculate_net_weight(
        row["first_weight"],
        second_weight,
    )

    cargo_value = (
        calculate_cargo_value(
            net,
            row["unit_price"],
        )
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
            cargo_value=?,
            weight=?,

            status='SAVED'

        WHERE id=?
        """,
        (
            second_weight,
            second_at,
            second_operator,

            (
                1
                if is_manual_weight
                else 0
            ),

            net,
            cargo_value,
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
    require_roles(
        request,
        "admin",
        "operator",
    )

    conn = db()

    row = conn.execute(
        """
        SELECT *
        FROM weighments
        WHERE ticket_number=?
        """,
        (
            ticket,
        ),
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
        (
            row["id"],
        ),
    ).fetchall()

    photos = [
        photo["filename"]
        for photo in photo_rows
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

            "app_mode":
                APP_MODE,
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
    require_roles(
        request,
        "admin",
        "operator",
    )

    conn = db()

    q = str(
        q
    ).strip()

    if q:

        like = (
            f"%{q}%"
        )

        normalized_like = (
            "%"
            + normalize_plate_search(
                q
            )
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

                OR CAST(
                    density
                    AS TEXT
                ) LIKE ?

                OR CAST(
                    unit_price
                    AS TEXT
                ) LIKE ?

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

            "app_mode":
                APP_MODE,
        },
    )


# ============================================================
# DELETE WEIGHMENT - ADMIN ONLY
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
    # مهم:
    # حتی با URL مستقیم Operator نمی‌تواند حذف کند.
    require_roles(
        request,
        "admin",
    )

    if not str(
        next
    ).startswith("/"):
        next = "/records"

    conn = db()

    row = conn.execute(
        """
        SELECT *
        FROM weighments
        WHERE ticket_number=?
        """,
        (
            ticket,
        ),
    ).fetchone()

    if not row:

        conn.close()

        return RedirectResponse(
            next,
            status_code=303,
        )

    filenames = [
        photo["filename"]

        for photo in conn.execute(
            """
            SELECT filename
            FROM weighment_photos
            WHERE weighment_id=?
            """,
            (
                row["id"],
            ),
        ).fetchall()
    ]

    # تصویر قدیمی ممکن است فقط در photo_filename باشد.
    if (
        row["photo_filename"]
        and row["photo_filename"]
        not in filenames
    ):
        filenames.append(
            row["photo_filename"]
        )

    conn.execute(
        """
        DELETE
        FROM weighment_photos
        WHERE weighment_id=?
        """,
        (
            row["id"],
        ),
    )

    conn.execute(
        """
        DELETE
        FROM weighments
        WHERE id=?
        """,
        (
            row["id"],
        ),
    )

    conn.commit()
    conn.close()

    for filename in filenames:

        try:

            path = (
                UPLOAD_DIR
                / filename
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
# DEVICE PAGE - ADMIN ONLY
# ============================================================

@app.get(
    "/device",
    response_class=HTMLResponse,
)
async def device_page(
    request: Request,
):
    require_roles(
        request,
        "admin",
    )

    if SERIAL_MODE == "agent":

        cfg = load_device_config()

        ports = []

    else:

        cfg = (
            serial_mgr.get_config()
        )

        ports = (
            serial_mgr.list_ports()
        )

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


@app.post(
    "/device/save"
)
async def device_save(

    request: Request,

    enabled: str = Form(
        "0"
    ),

    port: str = Form(
        ""
    ),

    baud: int = Form(
        2400
    ),

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
    require_roles(
        request,
        "admin",
    )

    cfg = DeviceConfig(
        enabled=(
            enabled == "1"
        ),

        port=(
            port
            or ""
        ).strip(),

        baud=int(
            baud
        ),

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

    save_device_config(
        cfg
    )

    serial_mgr.set_config(
        cfg
    )

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

@app.get(
    "/api/device/status"
)
async def device_status(
    request: Request,
):
    # Operator برای صفحه ثبت وزن نیاز دارد وضعیت باسکول را بخواند.
    # این Endpoint تنظیمات را تغییر نمی‌دهد.
    require_roles(
        request,
        "admin",
        "operator",
    )

    if SERIAL_MODE == "agent":

        cfg = (
            load_device_config()
        )

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
                "mode":
                    "agent",

                "running":
                    (
                        online
                        and agent_state[
                            "running"
                        ]
                    ),

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


    cfg = (
        serial_mgr.get_config()
    )

    return JSONResponse(
        {
            "mode":
                "local",

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
            detail=(
                "Invalid device token"
            ),
        )


@app.get(
    "/api/agent/config"
)
async def agent_config(
    request: Request,
):
    require_device_token(
        request
    )

    cfg = load_device_config()

    return {
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
    }


@app.post(
    "/api/agent/status"
)
async def agent_status(
    request: Request,
):
    require_device_token(
        request
    )

    body = (
        await request.json()
    )

    agent_state[
        "running"
    ] = bool(
        body.get(
            "running",
            False,
        )
    )

    agent_state[
        "last_error"
    ] = str(
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

    agent_state[
        "last_raw"
    ] = raw

    agent_state[
        "last_weight"
    ] = body.get(
        "weight"
    )

    agent_state[
        "last_stable"
    ] = bool(
        body.get(
            "stable",
            False,
        )
    )

    agent_state[
        "last_seen_ts"
    ] = time.time()

    if raw:

        lines = (
            agent_state[
                "raw_lines"
            ]
        )

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
        "ok": True,
    }


# ============================================================
# SCALE API
# ============================================================

@app.get(
    "/api/scale/weight"
)
async def get_scale_weight(
    request: Request,
):
    require_roles(
        request,
        "admin",
        "operator",
    )

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


@app.post(
    "/api/scale/weight"
)
async def set_scale_weight(
    request: Request,
):
    require_device_token(
        request
    )

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
        "ok":
            True,

        "weight":
            weight,

        "stable":
            stable,

        "scale_id":
            scale_id,
    }  
