"""Tests for database operations."""

import pytest

from content_pilot.database import Database


@pytest.fixture
async def db(tmp_path):
    database = Database(tmp_path / "test.db")
    await database.connect()
    yield database
    await database.close()


@pytest.mark.asyncio
async def test_upsert_account(db):
    account_id = await db.upsert_account(
        platform="xiaohongshu",
        username="testuser",
        nickname="Test User",
        follower_count=100,
        login_state="active",
    )
    assert account_id > 0

    # Upsert same account updates it
    account_id2 = await db.upsert_account(
        platform="xiaohongshu",
        username="testuser",
        follower_count=200,
    )
    assert account_id2 == account_id

    account = await db.get_account("xiaohongshu")
    assert account is not None
    assert account["follower_count"] == 200


@pytest.mark.asyncio
async def test_create_and_get_post(db):
    post_id = await db.create_post(
        platform="xiaohongshu",
        title="Test Post",
        content="Hello world",
        status="draft",
    )
    assert post_id > 0

    post = await db.get_post(post_id)
    assert post is not None
    assert post["title"] == "Test Post"
    assert post["status"] == "draft"


@pytest.mark.asyncio
async def test_update_post(db):
    post_id = await db.create_post(
        platform="xiaohongshu",
        title="Original",
        content="Content",
        status="draft",
    )
    await db.update_post(post_id, status="published", title="Updated")

    post = await db.get_post(post_id)
    assert post["status"] == "published"
    assert post["title"] == "Updated"


@pytest.mark.asyncio
async def test_get_posts_filter(db):
    await db.create_post(platform="xiaohongshu", content="A", status="draft")
    await db.create_post(platform="xiaohongshu", content="B", status="published")
    await db.create_post(platform="douyin", content="C", status="draft")

    xhs_posts = await db.get_posts(platform="xiaohongshu")
    assert len(xhs_posts) == 2

    published = await db.get_posts(status="published")
    assert len(published) == 1


@pytest.mark.asyncio
async def test_schedule_crud(db):
    sid = await db.create_schedule(
        name="Daily Post",
        platform="xiaohongshu",
        cron_expression="0 20 * * *",
        topic="Python Tips",
    )
    assert sid > 0

    schedules = await db.get_schedules()
    assert len(schedules) == 1
    assert schedules[0]["name"] == "Daily Post"

    await db.update_schedule(sid, enabled=0)
    enabled = await db.get_schedules(enabled_only=True)
    assert len(enabled) == 0

    await db.delete_schedule(sid)
    all_scheds = await db.get_schedules()
    assert len(all_scheds) == 0


@pytest.mark.asyncio
async def test_count_posts_today(db):
    count = await db.count_posts_today("xiaohongshu")
    assert count == 0


@pytest.mark.asyncio
async def test_count_posts_today_with_published(db):
    """count_posts_today counts posts published today (UTC)."""
    from datetime import datetime, timezone

    # Use UTC time since SQLite DATE('now') is UTC
    utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    await db.create_post(
        platform="xiaohongshu",
        content="Published today",
        status="published",
        published_at=utc_now,
    )
    await db.create_post(
        platform="xiaohongshu",
        content="Draft",
        status="draft",
    )
    count = await db.count_posts_today("xiaohongshu")
    assert count == 1


@pytest.mark.asyncio
async def test_count_posts_today_different_platforms(db):
    """count_posts_today is platform-specific."""
    from datetime import datetime, timezone

    utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    await db.create_post(
        platform="xiaohongshu",
        content="XHS",
        status="published",
        published_at=utc_now,
    )
    await db.create_post(
        platform="douyin",
        content="DY",
        status="published",
        published_at=utc_now,
    )
    assert await db.count_posts_today("xiaohongshu") == 1
    assert await db.count_posts_today("douyin") == 1


@pytest.mark.asyncio
async def test_execute_rollback_on_error(db):
    """execute() rolls back on error."""
    with pytest.raises(Exception):
        await db.execute("INSERT INTO nonexistent_table VALUES (?)", (1,))
    # DB should still be usable
    count = await db.count_posts_today("xiaohongshu")
    assert count == 0


@pytest.mark.asyncio
async def test_conn_property_raises_when_not_connected(tmp_path):
    """Accessing conn before connect() raises RuntimeError."""
    database = Database(tmp_path / "test2.db")
    with pytest.raises(RuntimeError, match="not connected"):
        _ = database.conn


@pytest.mark.asyncio
async def test_delete_post(db):
    post_id = await db.create_post(
        platform="xiaohongshu", content="To Delete", status="draft"
    )
    await db.delete_post(post_id)
    post = await db.get_post(post_id)
    assert post is None


@pytest.mark.asyncio
async def test_get_post_not_found(db):
    post = await db.get_post(99999)
    assert post is None


@pytest.mark.asyncio
async def test_connection_lifecycle(tmp_path):
    """Database can be connected and closed multiple times."""
    database = Database(tmp_path / "lifecycle.db")
    await database.connect()
    await database.close()

    # Can reconnect
    await database.connect()
    count = await database.count_posts_today("xiaohongshu")
    assert count == 0
    await database.close()


@pytest.mark.asyncio
async def test_analytics_recording(db):
    """Analytics can be recorded and retrieved."""
    post_id = await db.create_post(
        platform="xiaohongshu", content="Test", status="published"
    )
    await db.record_analytics(
        post_id=post_id,
        platform="xiaohongshu",
        views=100,
        likes=50,
        comments=10,
        shares=5,
        favorites=20,
    )
    data = await db.get_post_analytics(post_id)
    assert len(data) == 1
    assert data[0]["views"] == 100


@pytest.mark.asyncio
async def test_fetch_one_returns_none_for_no_match(db):
    result = await db.fetch_one(
        "SELECT * FROM posts WHERE id = ?", (99999,)
    )
    assert result is None


@pytest.mark.asyncio
async def test_fetch_all_returns_empty_list(db):
    result = await db.fetch_all("SELECT * FROM posts WHERE 1=0")
    assert result == []
