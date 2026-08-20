import os

from datetime import (
    datetime,
    timezone,
)

import psycopg

from psycopg.rows import (
    dict_row,
)


# ============================================================
# CONFIG
# ============================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "",
).strip()


# ============================================================
# CONNECTION
# ============================================================

def available():

    return bool(
        DATABASE_URL
    )


def connect():

    if not DATABASE_URL:

        raise RuntimeError(
            "DATABASE_URL is not configured"
        )

    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row,
        connect_timeout=5,
    )


# ============================================================
# HELPERS
# ============================================================

def table_columns(
    conn,
    table_name,
):

    with conn.cursor() as cur:

        cur.execute(
            """
            SELECT column_name

            FROM information_schema.columns

            WHERE
                table_schema='public'
                AND table_name=%s
            """,
            (
                table_name,
            ),
        )

        return {
            row[
                "column_name"
            ]

            for row
            in cur.fetchall()
        }


def ensure_cloud_columns(
    conn
):

    existing = table_columns(
        conn,
        "cloud_weighments",
    )


    additions = {
        "cancelled_at":
            "TEXT",

        "cancelled_by":
            "TEXT",

        "cancel_reason":
            "TEXT",
    }


    with conn.cursor() as cur:

        for name, ddl in (
            additions.items()
        ):

            if name not in existing:

                cur.execute(
                    f"""
                    ALTER TABLE
                        cloud_weighments

                    ADD COLUMN
                        {name} {ddl}
                    """
                )


# ============================================================
# INIT
# ============================================================

def init_cloud_db():

    if not available():
        return


    conn = connect()


    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS
                    cloud_weighments
                (
                    record_uuid TEXT
                        PRIMARY KEY,

                    ticket_number BIGINT,

                    plate TEXT
                        NOT NULL,

                    weight
                        DOUBLE PRECISION,

                    unit TEXT,

                    scale_id TEXT,

                    operator TEXT,

                    created_at TEXT,

                    status TEXT,

                    vehicle_type TEXT,

                    weighing_fee
                        DOUBLE PRECISION,

                    vehicle_weight
                        DOUBLE PRECISION,

                    driver_name TEXT,

                    driver_phone TEXT,

                    cargo_type TEXT,

                    cargo_owner TEXT,

                    origin TEXT,

                    destination TEXT,

                    document_no TEXT,

                    notes TEXT,

                    weighing_mode TEXT,

                    first_weight
                        DOUBLE PRECISION,

                    first_weighed_at TEXT,

                    first_operator TEXT,

                    second_weight
                        DOUBLE PRECISION,

                    second_weighed_at TEXT,

                    second_operator TEXT,

                    net_weight
                        DOUBLE PRECISION,

                    first_weight_manual
                        INTEGER
                        NOT NULL
                        DEFAULT 0,

                    second_weight_manual
                        INTEGER
                        NOT NULL
                        DEFAULT 0,

                    density
                        DOUBLE PRECISION,

                    unit_price
                        DOUBLE PRECISION,

                    cargo_value
                        DOUBLE PRECISION,

                    record_updated_at TEXT,

                    cancelled_at TEXT,

                    cancelled_by TEXT,

                    cancel_reason TEXT,

                    received_at TEXT
                        NOT NULL
                )
                """
            )


        ensure_cloud_columns(
            conn
        )


        with conn.cursor() as cur:

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_cloud_weighments_ticket

                ON cloud_weighments(
                    ticket_number
                )
                """
            )


            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_cloud_weighments_plate

                ON cloud_weighments(
                    plate
                )
                """
            )


            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_cloud_weighments_created

                ON cloud_weighments(
                    created_at
                )
                """
            )


            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_cloud_weighments_status

                ON cloud_weighments(
                    status
                )
                """
            )


            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_cloud_weighments_updated

                ON cloud_weighments(
                    record_updated_at
                )
                """
            )


        conn.commit()


    finally:

        conn.close()


# ============================================================
# UPSERT
# ============================================================

def upsert_weighment(
    data,
):

    record_uuid = str(
        data.get(
            "record_uuid",
            "",
        )
    ).strip()


    if not record_uuid:

        raise ValueError(
            "record_uuid is required"
        )


    plate = str(
        data.get(
            "plate",
            "",
        )
    ).strip()


    if not plate:

        raise ValueError(
            "plate is required"
        )


    now = datetime.now(
        timezone.utc
    ).isoformat()


    values = {

        "record_uuid":
            record_uuid,

        "ticket_number":
            data.get(
                "ticket_number"
            ),

        "plate":
            plate,

        "weight":
            data.get(
                "weight"
            ),

        "unit":
            data.get(
                "unit"
            ),

        "scale_id":
            data.get(
                "scale_id"
            ),

        "operator":
            data.get(
                "operator"
            ),

        "created_at":
            data.get(
                "created_at"
            ),

        "status":
            data.get(
                "status"
            ),

        "vehicle_type":
            data.get(
                "vehicle_type"
            ),

        "weighing_fee":
            data.get(
                "weighing_fee"
            ),

        "vehicle_weight":
            data.get(
                "vehicle_weight"
            ),

        "driver_name":
            data.get(
                "driver_name"
            ),

        "driver_phone":
            data.get(
                "driver_phone"
            ),

        "cargo_type":
            data.get(
                "cargo_type"
            ),

        "cargo_owner":
            data.get(
                "cargo_owner"
            ),

        "origin":
            data.get(
                "origin"
            ),

        "destination":
            data.get(
                "destination"
            ),

        "document_no":
            data.get(
                "document_no"
            ),

        "notes":
            data.get(
                "notes"
            ),

        "weighing_mode":
            data.get(
                "weighing_mode"
            ),

        "first_weight":
            data.get(
                "first_weight"
            ),

        "first_weighed_at":
            data.get(
                "first_weighed_at"
            ),

        "first_operator":
            data.get(
                "first_operator"
            ),

        "second_weight":
            data.get(
                "second_weight"
            ),

        "second_weighed_at":
            data.get(
                "second_weighed_at"
            ),

        "second_operator":
            data.get(
                "second_operator"
            ),

        "net_weight":
            data.get(
                "net_weight"
            ),

        "first_weight_manual":
            (
                1
                if data.get(
                    "first_weight_manual"
                )
                else 0
            ),

        "second_weight_manual":
            (
                1
                if data.get(
                    "second_weight_manual"
                )
                else 0
            ),

        "density":
            data.get(
                "density"
            ),

        "unit_price":
            data.get(
                "unit_price"
            ),

        "cargo_value":
            data.get(
                "cargo_value"
            ),

        "record_updated_at":
            data.get(
                "record_updated_at"
            ),

        "cancelled_at":
            data.get(
                "cancelled_at"
            ),

        "cancelled_by":
            data.get(
                "cancelled_by"
            ),

        "cancel_reason":
            data.get(
                "cancel_reason"
            ),

        "received_at":
            now,
    }


    conn = connect()


    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO cloud_weighments
                (
                    record_uuid,
                    ticket_number,
                    plate,
                    weight,
                    unit,
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
                    cargo_value,

                    record_updated_at,

                    cancelled_at,
                    cancelled_by,
                    cancel_reason,

                    received_at
                )

                VALUES
                (
                    %(record_uuid)s,
                    %(ticket_number)s,
                    %(plate)s,
                    %(weight)s,
                    %(unit)s,
                    %(scale_id)s,
                    %(operator)s,
                    %(created_at)s,
                    %(status)s,

                    %(vehicle_type)s,
                    %(weighing_fee)s,
                    %(vehicle_weight)s,

                    %(driver_name)s,
                    %(driver_phone)s,

                    %(cargo_type)s,
                    %(cargo_owner)s,

                    %(origin)s,
                    %(destination)s,
                    %(document_no)s,
                    %(notes)s,

                    %(weighing_mode)s,

                    %(first_weight)s,
                    %(first_weighed_at)s,
                    %(first_operator)s,

                    %(second_weight)s,
                    %(second_weighed_at)s,
                    %(second_operator)s,

                    %(net_weight)s,

                    %(first_weight_manual)s,
                    %(second_weight_manual)s,

                    %(density)s,
                    %(unit_price)s,
                    %(cargo_value)s,

                    %(record_updated_at)s,

                    %(cancelled_at)s,
                    %(cancelled_by)s,
                    %(cancel_reason)s,

                    %(received_at)s
                )

                ON CONFLICT(
                    record_uuid
                )

                DO UPDATE SET

                    ticket_number =
                        EXCLUDED.ticket_number,

                    plate =
                        EXCLUDED.plate,

                    weight =
                        EXCLUDED.weight,

                    unit =
                        EXCLUDED.unit,

                    scale_id =
                        EXCLUDED.scale_id,

                    operator =
                        EXCLUDED.operator,

                    created_at =
                        EXCLUDED.created_at,

                    status =
                        EXCLUDED.status,

                    vehicle_type =
                        EXCLUDED.vehicle_type,

                    weighing_fee =
                        EXCLUDED.weighing_fee,

                    vehicle_weight =
                        EXCLUDED.vehicle_weight,

                    driver_name =
                        EXCLUDED.driver_name,

                    driver_phone =
                        EXCLUDED.driver_phone,

                    cargo_type =
                        EXCLUDED.cargo_type,

                    cargo_owner =
                        EXCLUDED.cargo_owner,

                    origin =
                        EXCLUDED.origin,

                    destination =
                        EXCLUDED.destination,

                    document_no =
                        EXCLUDED.document_no,

                    notes =
                        EXCLUDED.notes,

                    weighing_mode =
                        EXCLUDED.weighing_mode,

                    first_weight =
                        EXCLUDED.first_weight,

                    first_weighed_at =
                        EXCLUDED.first_weighed_at,

                    first_operator =
                        EXCLUDED.first_operator,

                    second_weight =
                        EXCLUDED.second_weight,

                    second_weighed_at =
                        EXCLUDED.second_weighed_at,

                    second_operator =
                        EXCLUDED.second_operator,

                    net_weight =
                        EXCLUDED.net_weight,

                    first_weight_manual =
                        EXCLUDED.first_weight_manual,

                    second_weight_manual =
                        EXCLUDED.second_weight_manual,

                    density =
                        EXCLUDED.density,

                    unit_price =
                        EXCLUDED.unit_price,

                    cargo_value =
                        EXCLUDED.cargo_value,

                    record_updated_at =
                        EXCLUDED.record_updated_at,

                    cancelled_at =
                        EXCLUDED.cancelled_at,

                    cancelled_by =
                        EXCLUDED.cancelled_by,

                    cancel_reason =
                        EXCLUDED.cancel_reason,

                    received_at =
                        EXCLUDED.received_at
                """,
                values,
            )


        conn.commit()


    finally:

        conn.close()


# ============================================================
# COUNT
# ============================================================

def count_weighments():

    if not available():
        return 0


    conn = connect()


    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT COUNT(*) AS c
                FROM cloud_weighments
                """
            )


            row = (
                cur.fetchone()
            )


            return int(
                row[
                    "c"
                ]
            )


    finally:

        conn.close()


# ============================================================
# DASHBOARD
# ============================================================

def dashboard_data(
    limit=20,
):

    conn = connect()


    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT *
                FROM cloud_weighments

                ORDER BY
                    created_at
                        DESC
                        NULLS LAST,

                    received_at
                        DESC

                LIMIT %s
                """,
                (
                    int(
                        limit
                    ),
                ),
            )


            rows = (
                cur.fetchall()
            )


            cur.execute(
                """
                SELECT
                    COUNT(*) AS total,

                    COALESCE(
                        SUM(
                            CASE

                                WHEN
                                    weighing_mode='DOUBLE'
                                THEN
                                    COALESCE(
                                        net_weight,
                                        0
                                    )

                                ELSE
                                    COALESCE(
                                        weight,
                                        0
                                    )

                            END
                        ),
                        0
                    ) AS total_weight

                FROM cloud_weighments

                WHERE
                    (
                        status
                        NOT IN (
                            'WAITING_SECOND',
                            'CANCELLED'
                        )
                    )
                    OR status IS NULL
                """
            )


            summary = (
                cur.fetchone()
            )


            return {

                "rows":
                    rows,

                "total":
                    int(
                        summary[
                            "total"
                        ]
                    ),

                "total_weight":
                    float(
                        summary[
                            "total_weight"
                        ]
                        or 0
                    ),
            }


    finally:

        conn.close()


# ============================================================
# LIST / SEARCH
# ============================================================

def list_weighments(
    query="",
):

    query = str(
        query
        or ""
    ).strip()


    conn = connect()


    try:

        with conn.cursor() as cur:


            if query:

                like = (
                    "%"
                    + query
                    + "%"
                )


                cur.execute(
                    """
                    SELECT *
                    FROM cloud_weighments

                    WHERE
                        plate
                            ILIKE %(q)s

                        OR CAST(
                            ticket_number
                            AS TEXT
                        )
                            ILIKE %(q)s

                        OR COALESCE(
                            vehicle_type,
                            ''
                        )
                            ILIKE %(q)s

                        OR COALESCE(
                            driver_name,
                            ''
                        )
                            ILIKE %(q)s

                        OR COALESCE(
                            driver_phone,
                            ''
                        )
                            ILIKE %(q)s

                        OR COALESCE(
                            cargo_type,
                            ''
                        )
                            ILIKE %(q)s

                        OR COALESCE(
                            cargo_owner,
                            ''
                        )
                            ILIKE %(q)s

                        OR COALESCE(
                            origin,
                            ''
                        )
                            ILIKE %(q)s

                        OR COALESCE(
                            destination,
                            ''
                        )
                            ILIKE %(q)s

                        OR COALESCE(
                            document_no,
                            ''
                        )
                            ILIKE %(q)s

                        OR COALESCE(
                            notes,
                            ''
                        )
                            ILIKE %(q)s

                        OR COALESCE(
                            cancel_reason,
                            ''
                        )
                            ILIKE %(q)s

                        OR COALESCE(
                            cancelled_by,
                            ''
                        )
                            ILIKE %(q)s

                    ORDER BY
                        created_at
                            DESC
                            NULLS LAST,

                        received_at
                            DESC
                    """,
                    {
                        "q":
                            like
                    },
                )


            else:

                cur.execute(
                    """
                    SELECT *
                    FROM cloud_weighments

                    ORDER BY
                        created_at
                            DESC
                            NULLS LAST,

                        received_at
                            DESC
                    """
                )


            return (
                cur.fetchall()
            )


    finally:

        conn.close()


# ============================================================
# DETAIL
# ============================================================

def get_by_ticket(
    ticket_number,
):

    conn = connect()


    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT *
                FROM cloud_weighments

                WHERE
                    ticket_number=%s

                ORDER BY
                    received_at DESC

                LIMIT 1
                """,
                (
                    int(
                        ticket_number
                    ),
                ),
            )


            return (
                cur.fetchone()
            )


    finally:

        conn.close()


# ============================================================
# UUID
# ============================================================

def get_by_uuid(
    record_uuid,
):

    conn = connect()


    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT *
                FROM cloud_weighments

                WHERE
                    record_uuid=%s

                LIMIT 1
                """,
                (
                    str(
                        record_uuid
                    ),
                ),
            )


            return (
                cur.fetchone()
            )


    finally:

        conn.close()
