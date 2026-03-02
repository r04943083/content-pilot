"""Core application orchestrator."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from content_pilot.analytics import AnalyticsCollector
from content_pilot.browser import BrowserManager
from content_pilot.config import get_settings
from content_pilot.content import ContentGenerator, GeneratedContent
from content_pilot.database import Database
from content_pilot.platforms import PlatformRegistry
from content_pilot.platforms.base import PostContent
from content_pilot.safety import ContentValidator, RateLimiter
from content_pilot.scheduler import SchedulerEngine

# Ensure all platform connectors are registered
import content_pilot.platforms.xiaohongshu  # noqa: F401
import content_pilot.platforms.douyin  # noqa: F401
import content_pilot.platforms.bilibili  # noqa: F401
import content_pilot.platforms.weibo  # noqa: F401

logger = logging.getLogger(__name__)


class App:
    """Central application orchestrator."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.db = Database(self.settings.database.path)
        self.browser = BrowserManager()
        self.generator = ContentGenerator()
        self.validator = ContentValidator()
        self.rate_limiter = RateLimiter(self.db)
        self.analytics = AnalyticsCollector(self.db)
        self.scheduler = SchedulerEngine(self.db)

    async def startup(self) -> None:
        await self.db.connect()
        await self.browser.start()

    async def shutdown(self) -> None:
        self.scheduler.stop()
        await self.browser.stop()
        await self.db.close()

    # --- Login ---

    async def login(self, platform: str) -> bool:
        """Login to a platform via QR code scan."""
        context = await self.browser.get_context(platform, headless=False)
        try:
            connector = PlatformRegistry.create(platform, context)
            success = await connector.login()
            if success:
                await self.browser.save_session(context, platform)
                info = await connector.get_account_info()
                await self.db.upsert_account(
                    platform=platform,
                    username=info.username or info.nickname or platform,
                    nickname=info.nickname,
                    avatar_url=info.avatar_url,
                    follower_count=info.follower_count,
                    following_count=info.following_count,
                    login_state="active",
                    session_path=str(self.browser._state_path(platform)),
                )
            return success
        finally:
            await context.close()

    async def login_all(self) -> dict[str, bool]:
        """Login to all enabled platforms sequentially."""
        results = {}
        for platform in self.settings.platforms.enabled:
            results[platform] = await self.login(platform)
        return results

    # --- Status ---

    async def get_status(self) -> list[dict]:
        """Get status of all accounts."""
        accounts = await self.db.get_all_accounts()
        statuses = []
        for account in accounts:
            platform = account["platform"]
            context = await self.browser.get_context(platform, headless=True)
            try:
                connector = PlatformRegistry.create(platform, context)
                session_valid = await connector.check_session()
                statuses.append({
                    **account,
                    "session_valid": session_valid,
                })
            finally:
                await context.close()
        return statuses

    # --- Content Generation ---

    async def generate_content(
        self, topic: str, platform: str, style: str = "tutorial"
    ) -> tuple[int, GeneratedContent]:
        """Generate content and save as draft."""
        content = await self.generator.generate(topic, platform, style)

        # Validate
        result = self.validator.validate(
            platform,
            title=content.title,
            content=content.content,
            tags=content.tags,
        )
        if not result.valid:
            for err in result.errors:
                logger.warning("Validation: %s", err)

        # Save to database
        post_id = await self.db.create_post(
            platform=platform,
            title=content.title,
            content=content.content,
            tags=json.dumps(content.tags, ensure_ascii=False),
            style=style,
            status="draft",
        )
        return post_id, content

    # --- Publishing ---

    async def publish(self, post_id: int, dry_run: bool = False) -> bool:
        """Publish a post by its ID."""
        post = await self.db.get_post(post_id)
        if not post:
            logger.error("Post %d not found", post_id)
            return False

        platform = post["platform"]

        # Rate limit check
        allowed, reason = await self.rate_limiter.can_publish(platform)
        if not allowed:
            logger.warning("Rate limited: %s", reason)
            return False

        if dry_run:
            logger.info("[DRY RUN] Would publish post %d to %s", post_id, platform)
            return True

        # Update status
        await self.db.update_post(post_id, status="publishing")

        context = await self.browser.get_context(platform, headless=True)
        try:
            connector = PlatformRegistry.create(platform, context)

            # Check session
            if not await connector.check_session():
                logger.error("Session expired for %s. Please login again.", platform)
                await self.db.update_post(
                    post_id, status="failed", error_message="Session expired"
                )
                return False

            # Build post content
            tags = json.loads(post["tags"]) if post["tags"] else []
            images = json.loads(post["images"]) if post["images"] else []
            post_content = PostContent(
                title=post["title"],
                content=post["content"],
                tags=tags,
                images=[Path(p) for p in images],
                video_path=Path(post["video_path"]) if post["video_path"] else None,
            )

            # Publish
            if post["video_path"]:
                result = await connector.publish_video(post_content)
            else:
                result = await connector.publish_text_image(post_content)

            if result.success:
                await self.db.update_post(
                    post_id,
                    status="published",
                    platform_post_id=result.post_id,
                    platform_url=result.url,
                    published_at="CURRENT_TIMESTAMP",
                )
                self.rate_limiter.record_publish(platform)
                await self.browser.save_session(context, platform)
                logger.info("Published post %d to %s", post_id, platform)
                return True
            else:
                await self.db.update_post(
                    post_id, status="failed", error_message=result.error
                )
                logger.error("Publish failed: %s", result.error)
                return False
        finally:
            await context.close()

    # --- Scheduler ---

    async def run_daemon(self) -> None:
        """Start the scheduling daemon."""
        self.scheduler.set_generate_callback(self._on_scheduled_generate)
        self.scheduler.set_publish_callback(self._on_scheduled_publish)
        logger.info("Starting Content Pilot daemon...")
        await self.scheduler.run_forever()

    async def _on_scheduled_generate(self, schedule: dict) -> None:
        """Callback when scheduler triggers content generation."""
        topic = schedule.get("topic", "")
        platform = schedule.get("platform", "")
        style = schedule.get("style", "tutorial")
        if topic:
            post_id, content = await self.generate_content(topic, platform, style)
            logger.info(
                "Generated post %d: %s", post_id, content.title
            )

    async def _on_scheduled_publish(self, schedule: dict) -> None:
        """Callback when scheduler triggers publishing."""
        platform = schedule.get("platform", "")
        # Find latest approved post for this platform
        posts = await self.db.get_posts(platform=platform, status="approved", limit=1)
        if posts:
            await self.publish(posts[0]["id"])
