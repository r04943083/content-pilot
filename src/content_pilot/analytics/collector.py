"""Analytics data collector for post and account metrics."""

from __future__ import annotations

import logging
from datetime import date

from content_pilot.database import Database

logger = logging.getLogger(__name__)


class AnalyticsCollector:
    """Collects and aggregates analytics data."""

    def __init__(self, db: Database) -> None:
        self._db = db

    async def collect_post_analytics(
        self, post_id: int, platform: str, platform_post_id: str, data: dict
    ) -> None:
        """Store analytics snapshot for a post."""
        await self._db.record_analytics(
            post_id=post_id,
            platform=platform,
            platform_post_id=platform_post_id,
            views=data.get("views", 0),
            likes=data.get("likes", 0),
            comments=data.get("comments", 0),
            shares=data.get("shares", 0),
            favorites=data.get("favorites", 0),
        )

    async def record_daily_metrics(
        self, account_id: int, platform: str, follower_count: int
    ) -> None:
        """Record daily account metrics including follower delta."""
        today = date.today().isoformat()

        # Get yesterday's data to calculate delta
        growth_data = await self._db.get_growth_data(account_id, days=2)
        previous_count = 0
        if growth_data:
            previous_count = growth_data[0].get("follower_count", 0)
        delta = follower_count - previous_count if previous_count else 0

        await self._db.record_account_metrics(
            account_id=account_id,
            platform=platform,
            follower_count=follower_count,
            follower_delta=delta,
            recorded_date=today,
        )

    async def get_summary(self, platform: str | None = None) -> dict:
        """Get analytics summary across all posts."""
        where = ""
        params: tuple = ()
        if platform:
            where = "WHERE platform = ?"
            params = (platform,)

        total = await self._db.fetch_one(
            f"SELECT COUNT(*) as cnt, "
            f"SUM(views) as total_views, SUM(likes) as total_likes, "
            f"SUM(comments) as total_comments, SUM(shares) as total_shares, "
            f"SUM(favorites) as total_favorites "
            f"FROM analytics {where}",
            params,
        )

        posts = await self._db.fetch_one(
            f"SELECT COUNT(*) as total_posts, "
            f"SUM(CASE WHEN status='published' THEN 1 ELSE 0 END) as published "
            f"FROM posts {where}",
            params,
        )

        return {
            "total_posts": posts["total_posts"] if posts else 0,
            "published_posts": posts["published"] if posts else 0,
            "total_views": total["total_views"] or 0 if total else 0,
            "total_likes": total["total_likes"] or 0 if total else 0,
            "total_comments": total["total_comments"] or 0 if total else 0,
            "total_shares": total["total_shares"] or 0 if total else 0,
            "total_favorites": total["total_favorites"] or 0 if total else 0,
        }

    async def get_growth_trend(
        self, platform: str, days: int = 30
    ) -> list[dict]:
        """Get follower growth trend for a platform."""
        account = await self._db.get_account(platform)
        if not account:
            return []
        return await self._db.get_growth_data(account["id"], days)
