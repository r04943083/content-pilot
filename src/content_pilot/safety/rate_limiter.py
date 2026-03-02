"""Token bucket rate limiter for publish frequency control."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from content_pilot.config import get_settings
from content_pilot.database import Database


@dataclass
class PlatformBucket:
    """Tracks publish rate for a single platform."""
    last_publish_time: float = 0.0
    daily_count: int = 0
    daily_reset_date: str = ""


class RateLimiter:
    """Enforces rate limits on publishing to prevent detection."""

    def __init__(self, db: Database) -> None:
        self._db = db
        self._settings = get_settings()
        self._buckets: dict[str, PlatformBucket] = {}

    def _get_bucket(self, platform: str) -> PlatformBucket:
        if platform not in self._buckets:
            self._buckets[platform] = PlatformBucket()
        return self._buckets[platform]

    async def can_publish(self, platform: str) -> tuple[bool, str]:
        """Check if publishing is allowed. Returns (allowed, reason)."""
        settings = self._settings.safety

        # Check daily limit
        today_count = await self._db.count_posts_today(platform)
        if today_count >= settings.max_posts_per_day:
            return False, (
                f"Daily limit reached: {today_count}/{settings.max_posts_per_day} "
                f"posts today on {platform}"
            )

        # Check minimum interval
        bucket = self._get_bucket(platform)
        elapsed = time.time() - bucket.last_publish_time
        min_interval = settings.min_interval_minutes * 60
        if bucket.last_publish_time > 0 and elapsed < min_interval:
            remaining = int((min_interval - elapsed) / 60)
            return False, (
                f"Rate limited: wait {remaining} more minutes "
                f"(min interval: {settings.min_interval_minutes}min)"
            )

        return True, "OK"

    def record_publish(self, platform: str) -> None:
        """Record a successful publish."""
        bucket = self._get_bucket(platform)
        bucket.last_publish_time = time.time()
        bucket.daily_count += 1
