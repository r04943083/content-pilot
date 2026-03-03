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
    """Rate limiter blocks when recent publish exists in DB."""
    from datetime import datetime

    limiter = RateLimiter(db)

    # Create a post that was just published (now)
    await db.create_post(
        platform="xiaohongshu",
        content="Just published",
        status="published",
        published_at=datetime.now().isoformat(),
    )

    allowed, reason = await limiter.can_publish("xiaohongshu")
    assert not allowed
    assert "wait" in reason.lower() or "limit" in reason.lower()


@pytest.mark.asyncio
async def test_daily_limit_reached(db):
    """Rate limiter blocks when daily post limit is reached."""
    from datetime import datetime

    limiter = RateLimiter(db)

    # Create max_posts_per_day published posts for today
    max_posts = limiter._settings.safety.max_posts_per_day
    for i in range(max_posts):
        await db.create_post(
            platform="xiaohongshu",
            content=f"Post {i}",
            status="published",
            published_at=datetime.now().isoformat(),
        )

    allowed, reason = await limiter.can_publish("xiaohongshu")
    assert not allowed
    assert "limit" in reason.lower()


@pytest.mark.asyncio
async def test_multi_platform_isolation(db):
    """Rate limits are per-platform."""
    from datetime import datetime

    limiter = RateLimiter(db)

    # Publish to xiaohongshu
    await db.create_post(
        platform="xiaohongshu",
        content="XHS post",
        status="published",
        published_at=datetime.now().isoformat(),
    )

    # Douyin should still be allowed
    allowed, reason = await limiter.can_publish("douyin")
    assert allowed
    assert reason == "OK"


@pytest.mark.asyncio
async def test_record_publish_updates_bucket(db):
    """record_publish updates the in-memory bucket."""
    limiter = RateLimiter(db)
    limiter.record_publish("xiaohongshu")

    bucket = limiter._get_bucket("xiaohongshu")
    assert bucket.daily_count == 1
    assert bucket.last_publish_time > 0


@pytest.mark.asyncio
async def test_can_publish_no_recent_posts(db):
    """Can publish when no posts exist."""
    limiter = RateLimiter(db)
    allowed, reason = await limiter.can_publish("douyin")
    assert allowed
    assert reason == "OK"
