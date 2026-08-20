import os
import time
import shutil
import sqlite3
import threading

from pathlib import Path
from datetime import datetime, timezone


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

DB_PATH = (
    BASE_DIR
    / "weighbridge.db"
)

BACKUP_DIR = (
    BASE_DIR
    / "backups"
)

BACKUP_DIR.mkdir(
    exist_ok=True
)


BACKUP_INTERVAL = int(
    os.getenv(
        "SWB_BACKUP_INTERVAL_SEC",
        "3600",
    )
)


BACKUP_RETENTION_DAYS = int(
    os.getenv(
        "SWB_BACKUP_RETENTION_DAYS",
        "30",
    )
)


# ============================================================
# BACKUP MANAGER
# ============================================================

class BackupManager:

    def __init__(
        self,
        db_path=DB_PATH,
        backup_dir=BACKUP_DIR,
    ):
        self.db_path = Path(
            db_path
        )

        self.backup_dir = Path(
            backup_dir
        )

        self.backup_dir.mkdir(
            exist_ok=True
        )

        self._thread = None

        self._stop_event = (
            threading.Event()
        )

        self.running = False

        self.last_backup = None
        self.last_backup_file = None
        self.last_error = ""


    # ========================================================
    # START
    # ========================================================

    def start(self):

        if (
            self._thread
            and self._thread.is_alive()
        ):
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            name="swb-backup-worker",
            daemon=True,
        )

        self._thread.start()


    # ========================================================
    # STOP
    # ========================================================

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

            # در Startup یک Backup ایجاد می‌کنیم.
            try:
                self.create_backup()

            except Exception as exc:
                self.last_error = str(
                    exc
                )[:500]


            while not self._stop_event.wait(
                BACKUP_INTERVAL
            ):

                try:

                    self.create_backup()

                    self.cleanup_old_backups()

                except Exception as exc:

                    self.last_error = str(
                        exc
                    )[:500]

        finally:

            self.running = False


    # ========================================================
    # SAFE SQLITE BACKUP
    # ========================================================

    def create_backup(self):

        if not self.db_path.exists():

            raise RuntimeError(
                "Local database does not exist"
            )


        now = datetime.now(
            timezone.utc
        )


        filename = (
            "weighbridge_"
            + now.strftime(
                "%Y-%m-%d_%H-%M-%S"
            )
            + ".db"
        )


        destination = (
            self.backup_dir
            / filename
        )


        source_conn = sqlite3.connect(
            self.db_path,
            timeout=30,
        )


        destination_conn = (
            sqlite3.connect(
                destination,
                timeout=30,
            )
        )


        try:

            source_conn.backup(
                destination_conn
            )

        finally:

            destination_conn.close()
            source_conn.close()


        self.last_backup = (
            now.isoformat()
        )

        self.last_backup_file = (
            filename
        )

        self.last_error = ""


        self.cleanup_old_backups()


        return destination


    # ========================================================
    # CLEAN OLD BACKUPS
    # ========================================================

    def cleanup_old_backups(self):

        if BACKUP_RETENTION_DAYS <= 0:
            return


        cutoff = (
            time.time()
            -
            (
                BACKUP_RETENTION_DAYS
                * 24
                * 60
                * 60
            )
        )


        for path in (
            self.backup_dir
            .glob(
                "weighbridge_*.db"
            )
        ):

            try:

                if (
                    path.stat().st_mtime
                    < cutoff
                ):
                    path.unlink()

            except Exception:
                pass


    # ========================================================
    # STATUS
    # ========================================================

    def status(self):

        count = 0

        try:

            count = len(
                list(
                    self.backup_dir.glob(
                        "weighbridge_*.db"
                    )
                )
            )

        except Exception:
            count = 0


        return {
            "running":
                self.running,

            "last_backup":
                self.last_backup,

            "last_backup_file":
                self.last_backup_file,

            "backup_count":
                count,

            "retention_days":
                BACKUP_RETENTION_DAYS,

            "interval_seconds":
                BACKUP_INTERVAL,

            "last_error":
                self.last_error,
        }