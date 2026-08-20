import os
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "",
).strip()


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


def init_cloud_db():
    if not available():
        return

    conn = connect()

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS cloud_weighments
                (
                    record_uuid TEXT PRIMARY KEY,

                    ticket_number BIGINT,

                    plate TEXT NOT NULL,

                    weight DOUBLE PRECISION,

                    unit TEXT,

                    scale_id TEXT,

                    operator TEXT,

                    created_at TEXT,

                    status TEXT,

                    vehicle_type TEXT,

                    weighing_fee DOUBLE PRECISION,

                    vehicle_weight DOUBLE PRECISION,

                    driver_name TEXT,

                    driver_phone TEXT,

                    cargo_type TEXT,

                    cargo_owner TEXT,

                    origin TEXT,

                    destination TEXT,

                    document_no TEXT,

                    notes TEXT,

                    weighing_mode TEXT,

                    first_weight DOUBLE PRECISION,

                    first_weighed_at TEXT,

                    first_operator TEXT,

                    second_weight DOUBLE PRECISION,

                    second_weighed_at TEXT,

                    second_operator TEXT,

                    net_weight DOUBLE PRECISION,

                    first_weight_manual INTEGER
                        NOT NULL DEFAULT 0,

                    second_weight_manual INTEGER
                        NOT NULL DEFAULT 0,

                    density DOUBLE PRECISION,

                    unit_price DOUBLE PRECISION,

                    cargo_value DOUBLE PRECISION,

                    record_updated_at TEXT,

                    received_at TEXT NOT NULL
                )
                """
            )

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

        conn.commit()

    finally:
        conn.close()


def upsert_weighment(
    data,
):
    record_uuid = str(
        data.get(
            "record_uuid",
            ""
        )
    ).strip()

    if not record_uuid:
        raise ValueError(
            "record_uuid is required"
        )

    plate = str(
        data.get(
            "plate",
            ""
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
            1
            if data.get(
                "first_weight_manual"
            )
            else 0,

        "second_weight_manual":
            1
            if data.get(
                "second_weight_manual"
            )
            else 0,

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

                    received_at =
                        EXCLUDED.received_at
                """,
                values,
            )

        conn.commit()

    finally:
        conn.close()


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

            row = cur.fetchone()

            return int(
                row["c"]
            )

    finally:
        conn.close()