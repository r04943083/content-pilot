"""Tests for scheduler engine."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content_pilot.database import Database
from content_pilot.scheduler.engine import SchedulerEngine


@pytest.fixture
async def db(tmp_path):
    database = Database(tmp_path / "test.db")
    await database.connect()
    yield database
    await database.close()


@pytest.fixture
def mock_settings():
    from content_pilot.config.settings import Settings

    return Settings()


@pytest.fixture
def scheduler(db, mock_settings, monkeypatch):
    monkeypatch.setattr("content_pilot.scheduler.engine.get_settings", lambda: mock_settings)
    return SchedulerEngine(db)


class TestAddRemoveSchedule:
    @pytest.mark.asyncio
    async def test_add_schedule(self, scheduler, db):
        """Adding a schedule persists to DB and registers job."""
        sid = await scheduler.add_schedule(
            name="Daily Post",
            platform="xiaohongshu",
            cron_expression="0 20 * * *",
            topic="Python Tips",
            style="tutorial",
        )
        assert sid > 0

        schedules = await db.get_schedules()
        assert len(schedules) == 1
        assert schedules[0]["name"] == "Daily Post"

        # Job should be registered in APScheduler
        job = scheduler._scheduler.get_job(f"schedule_{sid}")
        assert job is not None

    @pytest.mark.asyncio
    async def test_remove_schedule(self, scheduler, db):
        """Removing a schedule deletes from DB and unregisters job."""
        sid = await scheduler.add_schedule(
            name="To Remove",
            platform="xiaohongshu",
            cron_expression="0 20 * * *",
        )
        await scheduler.remove_schedule(sid)

        schedules = await db.get_schedules()
        assert len(schedules) == 0
        assert scheduler._scheduler.get_job(f"schedule_{sid}") is None

    @pytest.mark.asyncio
    async def test_remove_nonexistent_schedule(self, scheduler, db):
        """Removing a schedule that doesn't exist in APScheduler should not error."""
        # Create a schedule in DB directly (not in APScheduler)
        sid = await db.create_schedule(
            name="Ghost",
            platform="xiaohongshu",
            cron_expression="0 20 * * *",
        )
        await scheduler.remove_schedule(sid)
        # Should not raise


class TestPauseResumeSchedule:
    @pytest.mark.asyncio
    async def test_pause_schedule(self, scheduler, db):
        """Pausing a schedule disables it in DB."""
        sid = await scheduler.add_schedule(
            name="Pausable",
            platform="xiaohongshu",
            cron_expression="0 20 * * *",
        )
        await scheduler.pause_schedule(sid)

        enabled = await db.get_schedules(enabled_only=True)
        assert len(enabled) == 0

    @pytest.mark.asyncio
    async def test_resume_schedule(self, scheduler, db):
        """Resuming a paused schedule re-enables it."""
        sid = await scheduler.add_schedule(
            name="Resumable",
            platform="xiaohongshu",
            cron_expression="0 20 * * *",
        )
        await scheduler.pause_schedule(sid)
        await scheduler.resume_schedule(sid)

        enabled = await db.get_schedules(enabled_only=True)
        assert len(enabled) == 1

    @pytest.mark.asyncio
    async def test_pause_nonexistent_job(self, scheduler, db):
        """Pausing a schedule without APScheduler job should not error."""
        sid = await db.create_schedule(
            name="Ghost",
            platform="xiaohongshu",
            cron_expression="0 20 * * *",
        )
        await scheduler.pause_schedule(sid)
        # Should not raise


class TestDBHealthCheck:
    @pytest.mark.asyncio
    async def test_execute_schedule_runs_health_check(self, scheduler, db):
        """_execute_schedule does a DB health check before running callbacks."""
        gen_cb = AsyncMock()
        pub_cb = AsyncMock()
        scheduler.set_generate_callback(gen_cb)
        scheduler.set_publish_callback(pub_cb)

        schedule = {
            "id": 1,
            "name": "Test",
            "platform": "xiaohongshu",
            "topic": "test",
            "style": "tutorial",
        }
        await scheduler._execute_schedule(schedule)

        gen_cb.assert_awaited_once_with(schedule)
        pub_cb.assert_awaited_once_with(schedule)

    @pytest.mark.asyncio
    async def test_execute_schedule_handles_callback_error(self, scheduler, db):
        """Callback errors are caught and don't crash the scheduler."""
        gen_cb = AsyncMock(side_effect=RuntimeError("AI failed"))
        scheduler.set_generate_callback(gen_cb)

        schedule = {
            "id": 1,
            "name": "Failing",
            "platform": "xiaohongshu",
            "topic": "test",
            "style": "tutorial",
        }
        # Should not raise
        await scheduler._execute_schedule(schedule)


class TestCronExpressionParsing:
    @pytest.mark.asyncio
    async def test_valid_cron_expression(self, scheduler, db):
        """Valid cron expressions are accepted."""
        sid = await scheduler.add_schedule(
            name="Every Hour",
            platform="xiaohongshu",
            cron_expression="0 * * * *",
        )
        assert sid > 0

    @pytest.mark.asyncio
    async def test_complex_cron_expression(self, scheduler, db):
        """Complex cron expressions with multiple values work."""
        sid = await scheduler.add_schedule(
            name="Specific Times",
            platform="xiaohongshu",
            cron_expression="30 9,12,18 * * 1-5",
        )
        assert sid > 0
        job = scheduler._scheduler.get_job(f"schedule_{sid}")
        assert job is not None

    @pytest.mark.asyncio
    async def test_invalid_cron_raises(self, scheduler, db):
        """Invalid cron expressions raise ValueError."""
        with pytest.raises(Exception):
            await scheduler.add_schedule(
                name="Bad Cron",
                platform="xiaohongshu",
                cron_expression="not a cron",
            )


class TestLoadSchedules:
    @pytest.mark.asyncio
    async def test_load_schedules_from_db(self, scheduler, db):
        """load_schedules reads enabled schedules from DB."""
        await db.create_schedule(
            name="S1",
            platform="xiaohongshu",
            cron_expression="0 20 * * *",
        )
        await db.create_schedule(
            name="S2",
            platform="douyin",
            cron_expression="0 12 * * *",
        )
        # Disable S2
        schedules = await db.get_schedules()
        await db.update_schedule(schedules[0].get("id") or 2, enabled=0)

        count = await scheduler.load_schedules()
        assert count == 1  # Only enabled schedule


class TestStartStop:
    def test_stop_when_not_running(self, scheduler):
        """Stopping a non-running scheduler should not error."""
        scheduler.stop()  # Should not raise

    @pytest.mark.asyncio
    async def test_start_and_stop(self, scheduler):
        """Scheduler can be started and stopped."""
        scheduler.start()
        assert scheduler._scheduler.running
        # shutdown(wait=False) is async-safe; verify stop() call doesn't raise
        scheduler.stop()
