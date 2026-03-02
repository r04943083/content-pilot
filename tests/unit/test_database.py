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
