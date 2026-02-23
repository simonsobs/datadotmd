"""Background scheduler for auto-scanning directories."""

import threading
import time
from typing import Optional

import schedule
from structlog import get_logger

from datadotmd.system.sync import scan_and_update_database
from datadotmd.database.service import get_session


logger = get_logger()


class DirectoryScanScheduler:
    """
    Background scheduler for scanning directories at regular intervals.

    Runs in a separate thread to avoid blocking the async event loop.
    """

    def __init__(self, interval_minutes: int = 60):
        """
        Initialize the scheduler.

        Parameters
        ----------
        interval_minutes : int
            Interval in minutes between scans
        """
        self.interval_minutes = interval_minutes
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()

    def start(self):
        """Start the background scheduler thread."""
        with self._lock:
            if self._running:
                logger.warning("Scheduler already running")
                return

            self._running = True
            self._thread = threading.Thread(
                target=self._run_scheduler,
                daemon=True,
                name="DirectoryScanScheduler",
            )
            self._thread.start()
            logger.info(
                "Directory scan scheduler started",
                interval_minutes=self.interval_minutes,
            )

    def stop(self):
        """Stop the background scheduler thread."""
        with self._lock:
            if not self._running:
                logger.warning("Scheduler not running")
                return

            self._running = False

        # Wait for thread to finish (with timeout)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
            logger.info("Directory scan scheduler stopped")

    def _run_scheduler(self):
        """Main scheduler loop (runs in background thread)."""
        # Schedule the scan job
        schedule.every(self.interval_minutes).minutes.do(self._scan_job)

        # Run the scheduler loop
        while self._running:
            try:
                schedule.run_pending()
                time.sleep(1)  # Check every second if something needs to run
            except Exception as e:
                logger.exception("Error in scheduler loop", error=str(e))
                time.sleep(10)  # Back off on error

    def _scan_job(self):
        """Job that runs on schedule to scan the directory."""
        try:
            logger.info("Starting scheduled directory scan")
            with get_session() as session:
                scan_and_update_database(session=session)
            logger.info("Completed scheduled directory scan")
        except Exception as e:
            logger.exception("Error during scheduled scan", error=str(e))
