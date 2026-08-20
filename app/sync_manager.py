import os
import time
import threading
from datetime import datetime, timezone

import httpx


APP_MODE = os.getenv(
    "SWB_APP_MODE",
    "local",
).strip().lower()

CLOUD_URL = os.getenv(
    "SWB_CLOUD_URL",
    "",
).strip().rstrip("/")

SYNC_TOKEN = os.getenv(
    "SWB_SYNC_TOKEN",
    "",
).strip()

SYNC_INTERVAL = float(
    os.getenv(
        "SWB_SYNC_INTERVAL",
        "10",
    )
)


class SyncManager:

    def __init__(
        self,
        db_factory,
    ):
        self.db_factory = db_factory

        self._thread = None
        self._stop_event = (
            threading.Event()
        )

        self.last_success = None
        self.last_error = ""

        self.cloud_online = False
        self.running = False


    # ========================================================
    # STATUS
    # ========================================================

    def get_pending_count(self):

        if APP_MODE != "local":
            return 0

        conn = self.db_factory()

        try:
            row = conn.execute(
                """
                SELECT COUNT(*) AS c
                FROM weighments
                WHERE sync_status='PENDING'
                """
            ).fetchone()

            return int(
                row["c"]
            )

        except Exception:
            return 0

        finally:
            conn.close()


    def status(self):

        return {
            "mode":
                APP_MODE,

            "running":
                self.running,

            "cloud_online":
                self.cloud_online,

            "pending":
                self.get_pending_count(),

            "last_success":
                self.last_success,

            "last_error":
                self.last_error,
        }


    # ========================================================
    # START / STOP
    # ========================================================

    def start(self):

        if APP_MODE != "local":
            return

        if not CLOUD_URL:
            self.last_error = (
                "SWB_CLOUD_URL is not configured"
            )
            return

        if not SYNC_TOKEN:
            self.last_error = (
                "SWB_SYNC_TOKEN is not configured"
            )
            return

        if (
            self._thread
            and self._thread.is_alive()
        ):
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            name="swb-sync-worker",
            daemon=True,
        )

        self._thread.start()


    def stop(self):

        self._stop_event.set()

        if (
            self._thread
            and self._thread.is_alive()
        ):
            self._thread.join(
                timeout=3
            )


    # ========================================================
    # WORKER
    # ========================================================

    def _run(self):

        self.running = True

        try:

            while not self._stop_event.is_set():

                try:
                    self.sync_once()

                except Exception as exc:
                    self.cloud_online = False

                    self.last_error = str(
                        exc
                    )[:500]

                self._stop_event.wait(
                    SYNC_INTERVAL
                )

        finally:
            self.running = False


    # ========================================================
    # GET PENDING ROWS
    # ========================================================

    def _pending_rows(self):

        conn = self.db_factory()

        try:

            rows = conn.execute(
                """
                SELECT *
                FROM weighments

                WHERE sync_status='PENDING'

                ORDER BY id ASC

                LIMIT 50
                """
            ).fetchall()

            return [
                dict(row)
                for row in rows
            ]

        finally:
            conn.close()


    # ========================================================
    # MARK SYNCED
    # ========================================================

    def _mark_synced(
        self,
        record_uuid,
    ):

        conn = self.db_factory()

        try:

            conn.execute(
                """
                UPDATE weighments

                SET
                    sync_status='SYNCED',
                    synced_at=?

                WHERE record_uuid=?
                """,
                (
                    datetime.now(
                        timezone.utc
                    ).isoformat(),

                    record_uuid,
                ),
            )

            conn.commit()

        finally:
            conn.close()


    # ========================================================
    # SERIALIZE
    # ========================================================

    def _serialize_row(
        self,
        row,
    ):

        fields = [
            "record_uuid",
            "ticket_number",
            "plate",
            "weight",
            "unit",
            "scale_id",
            "operator",
            "created_at",
            "status",

            "vehicle_type",
            "weighing_fee",
            "vehicle_weight",

            "driver_name",
            "driver_phone",

            "cargo_type",
            "cargo_owner",

            "origin",
            "destination",
            "document_no",
            "notes",

            "weighing_mode",

            "first_weight",
            "first_weighed_at",
            "first_operator",

            "second_weight",
            "second_weighed_at",
            "second_operator",

            "net_weight",

            "first_weight_manual",
            "second_weight_manual",

            "density",
            "unit_price",
            "cargo_value",

            "record_updated_at",
        ]

        result = {}

        for field in fields:
            result[field] = (
                row.get(field)
            )

        return result


    # ========================================================
    # SYNC ONCE
    # ========================================================

    def sync_once(self):

        if APP_MODE != "local":
            return

        if (
            not CLOUD_URL
            or not SYNC_TOKEN
        ):
            return

        url = (
            CLOUD_URL
            + "/api/sync/weighments"
        )

        rows = (
            self._pending_rows()
        )

        # حتی اگر رکورد Pending وجود ندارد
        # با health endpoint وضعیت Cloud را بررسی می‌کنیم.

        if not rows:

            health_url = (
                CLOUD_URL
                + "/api/sync/health"
            )

            try:

                response = httpx.get(
                    health_url,
                    headers={
                        "X-Sync-Token":
                            SYNC_TOKEN
                    },
                    timeout=5.0,
                )

                response.raise_for_status()

                self.cloud_online = True
                self.last_error = ""

            except Exception as exc:

                self.cloud_online = False
                self.last_error = str(
                    exc
                )[:500]

            return


        for row in rows:

            if (
                self._stop_event
                .is_set()
            ):
                return

            record_uuid = (
                row.get(
                    "record_uuid"
                )
            )

            if not record_uuid:
                continue


            payload = (
                self._serialize_row(
                    row
                )
            )


            try:

                response = httpx.post(
                    url,
                    json=payload,
                    headers={
                        "X-Sync-Token":
                            SYNC_TOKEN
                    },
                    timeout=10.0,
                )

                response.raise_for_status()

                data = (
                    response.json()
                )


                if not data.get(
                    "ok"
                ):
                    raise RuntimeError(
                        "Cloud rejected record"
                    )


                self._mark_synced(
                    record_uuid
                )


                self.cloud_online = True

                self.last_success = (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                )

                self.last_error = ""


            except Exception as exc:

                self.cloud_online = False

                self.last_error = str(
                    exc
                )[:500]

                # اگر Cloud قطع باشد،
                # باقی رکوردها برای دور بعد
                # PENDING می‌مانند.
                break