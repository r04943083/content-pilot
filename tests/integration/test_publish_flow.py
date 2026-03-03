"""Integration tests for the generate -> approve -> publish flow."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content_pilot.content.generator import GeneratedContent


@pytest.fixture
def app(mock_settings, monkeypatch):
    monkeypatch.setattr("content_pilot.config.get_settings", lambda: mock_settings)
    monkeypatch.setattr("content_pilot.app.get_settings", lambda: mock_settings)
    from content_pilot.app import App

    return App()


class TestEndToEndPublishFlow:
    @pytest.mark.asyncio
    async def test_generate_approve_publish(self, app, monkeypatch):
        """Full flow: generate content, approve it, publish it."""
        await app.db.connect()
        try:
            # Step 1: Generate content
            mock_content = GeneratedContent(
                title="Integration Test Post",
                content="This is integration test content.",
                tags=["test", "integration"],
                style="tutorial",
                platform="xiaohongshu",
            )
            monkeypatch.setattr(
                app.generator, "generate", AsyncMock(return_value=mock_content)
            )

            post_id, content, images = await app.generate_content(
                "test topic", "xiaohongshu", "tutorial"
            )
            assert post_id > 0

            # Verify DB state: draft
            post = await app.db.get_post(post_id)
            assert post["status"] == "draft"

            # Step 2: Approve
            await app.db.update_post(post_id, status="approved")
            post = await app.db.get_post(post_id)
            assert post["status"] == "approved"

            # Step 3: Publish
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.post_id = "ext_456"
            mock_result.url = "https://www.xiaohongshu.com/post/456"

            mock_context = AsyncMock()
            mock_connector = AsyncMock()
            mock_connector.check_session.return_value = True
            mock_connector.publish_text_image.return_value = mock_result

            monkeypatch.setattr(
                app.browser, "get_context", AsyncMock(return_value=mock_context)
            )
            monkeypatch.setattr(app.browser, "save_session", AsyncMock())
            monkeypatch.setattr(
                app.rate_limiter, "can_publish", AsyncMock(return_value=(True, "OK"))
            )

            with patch("content_pilot.app.PlatformRegistry") as mock_registry:
                mock_registry.create.return_value = mock_connector
                result = await app.publish(post_id)

            assert result is True

            # Verify DB state: published
            post = await app.db.get_post(post_id)
            assert post["status"] == "published"
            assert post["platform_post_id"] == "ext_456"
            assert post["platform_url"] == "https://www.xiaohongshu.com/post/456"
            assert post["published_at"] is not None

        finally:
            await app.db.close()

    @pytest.mark.asyncio
    async def test_publish_failure_sets_failed_status(self, app, monkeypatch):
        """When publish fails, post status becomes 'failed'."""
        await app.db.connect()
        try:
            post_id = await app.db.create_post(
                platform="xiaohongshu",
                title="Fail Test",
                content="Content",
                tags=json.dumps(["test"]),
                images="[]",
                status="approved",
            )

            mock_result = MagicMock()
            mock_result.success = False
            mock_result.error = "Network error"

            mock_context = AsyncMock()
            mock_connector = AsyncMock()
            mock_connector.check_session.return_value = True
            mock_connector.publish_text_image.return_value = mock_result

            monkeypatch.setattr(
                app.browser, "get_context", AsyncMock(return_value=mock_context)
            )
            monkeypatch.setattr(
                app.rate_limiter, "can_publish", AsyncMock(return_value=(True, "OK"))
            )

            with patch("content_pilot.app.PlatformRegistry") as mock_registry:
                mock_registry.create.return_value = mock_connector
                result = await app.publish(post_id)

            assert result is False
            post = await app.db.get_post(post_id)
            assert post["status"] == "failed"
            assert "Network error" in post["error_message"]

        finally:
            await app.db.close()

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_publish(self, app, monkeypatch):
        """Rate limiter prevents publishing."""
        await app.db.connect()
        try:
            post_id = await app.db.create_post(
                platform="xiaohongshu",
                title="Rate Limited",
                content="Content",
                status="approved",
            )

            monkeypatch.setattr(
                app.rate_limiter,
                "can_publish",
                AsyncMock(return_value=(False, "Daily limit reached")),
            )

            result = await app.publish(post_id)
            assert result is False

            # Status should remain approved (not changed to failed)
            post = await app.db.get_post(post_id)
            assert post["status"] == "approved"

        finally:
            await app.db.close()
