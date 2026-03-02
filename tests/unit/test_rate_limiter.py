"""Tests for rate limiter."""

import pytest

from content_pilot.database import Database
from content_pilot.safety.rate_limiter import RateLimiter


@pytest.fixture
async def db(tmp_path):
    database = Database(tmp_path / "test.db")
    await database.connect()
    yield database
    await database.close()


@pytest.mark.asyncio
async def test_can_publish_initially(db):
    limiter = RateLimiter(db)
    allowed, reason = await limiter.can_publish("xiaohongshu")
    assert allowed
    assert reason == "OK"


@pytest.mark.asyncio
async def test_rate_limit_after_publish(db):
    limiter = RateLimiter(db)
    limiter.record_publish("xiaohongshu")

    allowed, reason = await limiter.can_publish("xiaohongshu")
    assert not allowed
    assert "wait" in reason.lower()
