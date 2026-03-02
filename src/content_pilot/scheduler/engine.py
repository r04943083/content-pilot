"""APScheduler-based task scheduler with SQLite job persistence."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from content_pilot.config import get_settings
from content_pilot.database import Database

logger = logging.getLogger(__name__)


class SchedulerEngine:
    """Manages scheduled content generation and publishing."""

    def __init__(self, db: Database) -> None:
        self._db = db
        self._settings = get_settings()
        self._scheduler = AsyncIOScheduler(
            job_defaults={
                "coalesce": self._settings.scheduler.coalesce,
                "max_instances": self._settings.scheduler.max_instances,
                "misfire_grace_time": self._settings.scheduler.misfire_grace_time,
            },
        )
        self._publish_callback = None
        self._generate_callback = None

    def set_publish_callback(self, callback) -> None:
        """Set callback for publish jobs: async def callback(schedule: dict)."""
        self._publish_callback = callback

    def set_generate_callback(self, callback) -> None:
        """Set callback for generate jobs: async def callback(schedule: dict)."""
        self._generate_callback = callback

    async def load_schedules(self) -> int:
        """Load all enabled schedules from database and register as jobs."""
        schedules = await self._db.get_schedules(enabled_only=True)
        count = 0
        for sched in schedules:
            self._add_job(sched)
            count += 1
        logger.info("Loaded %d schedules", count)
        return count

    def _add_job(self, schedule: dict) -> None:
        """Add a schedule as an APScheduler job."""
        job_id = f"schedule_{schedule['id']}"
        trigger = CronTrigger.from_crontab(schedule["cron_expression"])

        self._scheduler.add_job(
            self._execute_schedule,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            kwargs={"schedule": schedule},
        )

    async def _execute_schedule(self, schedule: dict) -> None:
        """Execute a scheduled job (generate + publish)."""
        logger.info(
            "Executing schedule '%s' for %s",
            schedule["name"], schedule["platform"],
        )
        try:
            if self._generate_callback:
                await self._generate_callback(schedule)
            if self._publish_callback:
                await self._publish_callback(schedule)

            await self._db.update_schedule(
                schedule["id"], last_run_at=datetime.now().isoformat()
            )
        except Exception:
            logger.exception("Schedule '%s' failed", schedule["name"])

    async def add_schedule(
        self,
        name: str,
        platform: str,
        cron_expression: str,
        topic: str = "",
        style: str = "tutorial",
    ) -> int:
        """Create a new schedule and register it."""
        schedule_id = await self._db.create_schedule(
            name=name,
            platform=platform,
            topic=topic,
            style=style,
            cron_expression=cron_expression,
        )
        schedule = {
            "id": schedule_id,
            "name": name,
            "platform": platform,
            "topic": topic,
            "style": style,
            "cron_expression": cron_expression,
        }
        self._add_job(schedule)
        return schedule_id

    async def remove_schedule(self, schedule_id: int) -> None:
        job_id = f"schedule_{schedule_id}"
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)
        await self._db.delete_schedule(schedule_id)

    async def pause_schedule(self, schedule_id: int) -> None:
        job_id = f"schedule_{schedule_id}"
        if self._scheduler.get_job(job_id):
            self._scheduler.pause_job(job_id)
        await self._db.update_schedule(schedule_id, enabled=0)

    async def resume_schedule(self, schedule_id: int) -> None:
        job_id = f"schedule_{schedule_id}"
        if self._scheduler.get_job(job_id):
            self._scheduler.resume_job(job_id)
        await self._db.update_schedule(schedule_id, enabled=1)

    def start(self) -> None:
        """Start the scheduler."""
        self._scheduler.start()
        logger.info("Scheduler started")

    def stop(self) -> None:
        """Stop the scheduler if it is running."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")

    async def run_forever(self) -> None:
        """Start scheduler and run until interrupted."""
        await self.load_schedules()
        self.start()
        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, asyncio.CancelledError):
            self.stop()
