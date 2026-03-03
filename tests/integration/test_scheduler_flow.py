"""Integration tests for scheduler flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from content_pilot.database import Database
from content_pilot.scheduler.engine import SchedulerEngine


@pytest.fixture
def scheduler(db, mock_settings, monkeypatch):
    monkeypatch.setattr("content_pilot.scheduler.engine.get_settings", lambda: mock_settings)
    return SchedulerEngine(db)


class TestSchedulerFlow:
    @pytest.mark.asyncio
    async def test_create_fire_verify_db(self, scheduler, db):
        """Create schedule, fire it, verify DB is updated."""
        gen_callback = AsyncMock()
        pub_callback = AsyncMock()
        scheduler.set_generate_callback(gen_callback)
        scheduler.set_publish_callback(pub_callback)

        sid = await scheduler.add_schedule(
            name="Integration Test",
            platform="xiaohongshu",
            cron_expression="0 20 * * *",
            topic="Test Topic",
            style="tutorial",
        )

        # Simulate execution
        schedule = {
            "id": sid,
            "name": "Integration Test",
            "platform": "xiaohongshu",
            "topic": "Test Topic",
            "style": "tutorial",
            "cron_expression": "0 20 * * *",
        }
        await scheduler._execute_schedule(schedule)

        gen_callback.assert_awaited_once_with(schedule)
        pub_callback.assert_awaited_once_with(schedule)

        # Verify last_run_at was updated
        schedules = await db.get_schedules()
        assert len(schedules) == 1
        assert schedules[0]["last_run_at"] is not None

    @pytest.mark.asyncio
    async def test_pause_resume_cycle(self, scheduler, db):
        """Create, pause, resume, verify state at each step."""
        sid = await scheduler.add_schedule(
            name="Pausable",
            platform="xiaohongshu",
            cron_expression="0 20 * * *",
        )

        # Initially enabled
        enabled = await db.get_schedules(enabled_only=True)
        assert len(enabled) == 1

        # Pause
        await scheduler.pause_schedule(sid)
        enabled = await db.get_schedules(enabled_only=True)
        assert len(enabled) == 0

        # Resume
        await scheduler.resume_schedule(sid)
        enabled = await db.get_schedules(enabled_only=True)
        assert len(enabled) == 1

    @pytest.mark.asyncio
    async def test_multiple_schedules(self, scheduler, db):
        """Multiple schedules can coexist."""
        s1 = await scheduler.add_schedule(
            name="Schedule 1",
            platform="xiaohongshu",
            cron_expression="0 9 * * *",
        )
        s2 = await scheduler.add_schedule(
            name="Schedule 2",
            platform="douyin",
            cron_expression="0 12 * * *",
        )
        s3 = await scheduler.add_schedule(
            name="Schedule 3",
            platform="bilibili",
            cron_expression="0 18 * * *",
        )

        schedules = await db.get_schedules()
        assert len(schedules) == 3

        # Remove one
        await scheduler.remove_schedule(s2)
        schedules = await db.get_schedules()
        assert len(schedules) == 2

    @pytest.mark.asyncio
    async def test_load_and_fire(self, scheduler, db):
        """Load schedules from DB, then fire one."""
        await db.create_schedule(
            name="DB Schedule",
            platform="xiaohongshu",
            cron_expression="0 20 * * *",
            topic="Loaded Topic",
        )

        count = await scheduler.load_schedules()
        assert count == 1

        gen_cb = AsyncMock()
        scheduler.set_generate_callback(gen_cb)

        schedules = await db.get_schedules(enabled_only=True)
        await scheduler._execute_schedule(schedules[0])
        gen_cb.assert_awaited_once()
