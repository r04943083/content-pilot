"""Tests for analytics collector."""

from __future__ import annotations

from datetime import date

import pytest

from content_pilot.analytics.collector import AnalyticsCollector
from content_pilot.database import Database


@pytest.fixture
async def db(tmp_path):
    database = Database(tmp_path / "test.db")
    await database.connect()
    yield database
    await database.close()


@pytest.fixture
def collector(db):
    return AnalyticsCollector(db)


class TestGetSummary:
    @pytest.mark.asyncio
    async def test_empty_db_summary(self, collector):
        """Summary on empty DB returns zero/None values."""
        summary = await collector.get_summary()
        assert summary["total_posts"] == 0
        # published_posts may be None when no rows (SUM on empty set)
        assert summary["published_posts"] in (0, None)
        assert summary["total_views"] == 0
        assert summary["total_likes"] == 0
        assert summary["total_comments"] == 0
        assert summary["total_shares"] == 0
        assert summary["total_favorites"] == 0

    @pytest.mark.asyncio
    async def test_summary_with_data(self, collector, db):
        """Summary aggregates data correctly."""
        post_id = await db.create_post(
            platform="xiaohongshu",
            title="Test",
            content="Hello",
            status="published",
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
        await db.record_analytics(
            post_id=post_id,
            platform="xiaohongshu",
            views=200,
            likes=80,
            comments=15,
            shares=8,
            favorites=30,
        )

        summary = await collector.get_summary()
        assert summary["total_posts"] == 1
        assert summary["published_posts"] == 1
        assert summary["total_views"] == 300
        assert summary["total_likes"] == 130
        assert summary["total_comments"] == 25

    @pytest.mark.asyncio
    async def test_summary_platform_filter(self, collector, db):
        """Summary filters by platform correctly."""
        p1 = await db.create_post(
            platform="xiaohongshu", content="A", status="published"
        )
        p2 = await db.create_post(
            platform="douyin", content="B", status="published"
        )
        await db.record_analytics(
            post_id=p1, platform="xiaohongshu", views=100, likes=10,
            comments=0, shares=0, favorites=0,
        )
        await db.record_analytics(
            post_id=p2, platform="douyin", views=200, likes=20,
            comments=0, shares=0, favorites=0,
        )

        xhs_summary = await collector.get_summary(platform="xiaohongshu")
        assert xhs_summary["total_views"] == 100
        assert xhs_summary["total_likes"] == 10

        dy_summary = await collector.get_summary(platform="douyin")
        assert dy_summary["total_views"] == 200

        all_summary = await collector.get_summary()
        assert all_summary["total_views"] == 300


class TestDailyMetrics:
    @pytest.mark.asyncio
    async def test_record_daily_metrics_first_day(self, collector, db):
        """First day of metrics should have zero delta."""
        account_id = await db.upsert_account(
            platform="xiaohongshu",
            username="testuser",
            login_state="active",
        )
        await collector.record_daily_metrics(account_id, "xiaohongshu", 1000)

        growth = await db.get_growth_data(account_id, days=1)
        assert len(growth) == 1
        assert growth[0]["follower_count"] == 1000
        assert growth[0]["follower_delta"] == 0

    @pytest.mark.asyncio
    async def test_record_daily_metrics_delta_calc(self, collector, db):
        """Delta should be calculated from previous record."""
        account_id = await db.upsert_account(
            platform="xiaohongshu",
            username="testuser",
            login_state="active",
        )
        # Simulate a previous day's data
        await db.record_account_metrics(
            account_id=account_id,
            platform="xiaohongshu",
            follower_count=1000,
            follower_delta=0,
            recorded_date="2026-03-01",
        )

        # record_daily_metrics will read the previous data and calc delta
        await collector.record_daily_metrics(account_id, "xiaohongshu", 1050)

        growth = await db.get_growth_data(account_id, days=5)
        # The latest record should have delta = 1050 - 1000 = 50
        # (growth is ordered by recorded_date DESC, so index 0 is today)
        today_record = None
        for g in growth:
            if g["recorded_date"] == date.today().isoformat():
                today_record = g
                break
        assert today_record is not None
        assert today_record["follower_delta"] == 50


class TestCollectPostAnalytics:
    @pytest.mark.asyncio
    async def test_collect_stores_snapshot(self, collector, db):
        """collect_post_analytics stores a new analytics snapshot."""
        post_id = await db.create_post(
            platform="xiaohongshu", content="Test", status="published"
        )
        await collector.collect_post_analytics(
            post_id=post_id,
            platform="xiaohongshu",
            platform_post_id="ext_123",
            data={"views": 500, "likes": 100, "comments": 20, "shares": 10, "favorites": 50},
        )

        analytics = await db.get_post_analytics(post_id)
        assert len(analytics) == 1
        assert analytics[0]["views"] == 500
        assert analytics[0]["likes"] == 100
        assert analytics[0]["platform_post_id"] == "ext_123"


class TestGrowthTrend:
    @pytest.mark.asyncio
    async def test_growth_trend_no_account(self, collector, db):
        """Growth trend returns empty list for unknown platform."""
        result = await collector.get_growth_trend("nonexistent_platform")
        assert result == []

    @pytest.mark.asyncio
    async def test_growth_trend_with_data(self, collector, db):
        """Growth trend returns data for known account."""
        account_id = await db.upsert_account(
            platform="xiaohongshu",
            username="testuser",
            login_state="active",
        )
        await db.record_account_metrics(
            account_id=account_id,
            platform="xiaohongshu",
            follower_count=1000,
            follower_delta=10,
            recorded_date="2026-03-01",
        )
        result = await collector.get_growth_trend("xiaohongshu", days=30)
        assert len(result) == 1
        assert result[0]["follower_count"] == 1000
