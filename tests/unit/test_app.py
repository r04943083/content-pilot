"""Tests for the core App orchestrator."""

from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content_pilot.content.generator import GeneratedContent


@pytest.fixture
def mock_settings(tmp_path):
    """Create mock settings with temp DB path."""
    from content_pilot.config.settings import Settings

    s = Settings()
    s.database.path = str(tmp_path / "test.db")
    s.browser.user_data_dir = str(tmp_path / "browser")
    s.general.data_dir = str(tmp_path / "data")
    return s


@pytest.fixture
def app(mock_settings, monkeypatch):
    """Create an App instance with mocked settings."""
    monkeypatch.setattr("content_pilot.config.get_settings", lambda: mock_settings)
    monkeypatch.setattr("content_pilot.app.get_settings", lambda: mock_settings)
    from content_pilot.app import App

    return App()


class TestPublishedAtTimestamp:
    @pytest.mark.asyncio
    async def test_publish_sets_iso_timestamp(self, app, monkeypatch):
        """Published posts get an ISO-format published_at timestamp."""
        await app.db.connect()
        try:
            post_id = await app.db.create_post(
                platform="xiaohongshu",
                title="Test",
                content="Hello",
                tags=json.dumps(["tag1"]),
                images="[]",
                status="approved",
            )

            mock_result = MagicMock()
            mock_result.success = True
            mock_result.post_id = "ext_123"
            mock_result.url = "https://example.com/123"

            mock_context = AsyncMock()
            mock_connector = AsyncMock()
            mock_connector.check_session.return_value = True
            mock_connector.publish_text_image.return_value = mock_result

            monkeypatch.setattr(app.browser, "get_context", AsyncMock(return_value=mock_context))
            monkeypatch.setattr(app.browser, "save_session", AsyncMock())

            with patch("content_pilot.app.PlatformRegistry") as mock_registry:
                mock_registry.create.return_value = mock_connector
                monkeypatch.setattr(app.rate_limiter, "can_publish", AsyncMock(return_value=(True, "OK")))

                result = await app.publish(post_id)

            assert result is True
            post = await app.db.get_post(post_id)
            assert post["status"] == "published"
            assert post["published_at"] is not None
            # Verify it's valid ISO format
            datetime.fromisoformat(post["published_at"])
        finally:
            await app.db.close()


class TestPublishFlow:
    @pytest.mark.asyncio
    async def test_publish_not_found(self, app):
        """Publishing a non-existent post returns False."""
        await app.db.connect()
        try:
            result = await app.publish(999)
            assert result is False
        finally:
            await app.db.close()

    @pytest.mark.asyncio
    async def test_publish_rate_limited(self, app, monkeypatch):
        """Publishing when rate-limited returns False."""
        await app.db.connect()
        try:
            post_id = await app.db.create_post(
                platform="xiaohongshu",
                title="Test",
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
        finally:
            await app.db.close()

    @pytest.mark.asyncio
    async def test_publish_dry_run(self, app, monkeypatch):
        """Dry run returns True without actually publishing."""
        await app.db.connect()
        try:
            post_id = await app.db.create_post(
                platform="xiaohongshu",
                title="Test",
                content="Content",
                status="approved",
            )
            monkeypatch.setattr(
                app.rate_limiter,
                "can_publish",
                AsyncMock(return_value=(True, "OK")),
            )
            result = await app.publish(post_id, dry_run=True)
            assert result is True
            post = await app.db.get_post(post_id)
            # Status should not have changed
            assert post["status"] == "approved"
        finally:
            await app.db.close()

    @pytest.mark.asyncio
    async def test_publish_session_expired(self, app, monkeypatch):
        """Session expired results in 'failed' status."""
        await app.db.connect()
        try:
            post_id = await app.db.create_post(
                platform="xiaohongshu",
                title="Test",
                content="Content",
                tags="[]",
                images="[]",
                status="approved",
            )
            monkeypatch.setattr(
                app.rate_limiter,
                "can_publish",
                AsyncMock(return_value=(True, "OK")),
            )
            mock_context = AsyncMock()
            monkeypatch.setattr(app.browser, "get_context", AsyncMock(return_value=mock_context))

            mock_connector = AsyncMock()
            mock_connector.check_session.return_value = False

            with patch("content_pilot.app.PlatformRegistry") as mock_registry:
                mock_registry.create.return_value = mock_connector
                result = await app.publish(post_id)

            assert result is False
            post = await app.db.get_post(post_id)
            assert post["status"] == "failed"
            assert "Session expired" in post["error_message"]
        finally:
            await app.db.close()


class TestGenerateFlow:
    @pytest.mark.asyncio
    async def test_generate_content_saves_draft(self, app, monkeypatch):
        """generate_content creates a draft post in the DB."""
        await app.db.connect()
        try:
            mock_content = GeneratedContent(
                title="AI Title",
                content="AI Content",
                tags=["python", "ai"],
                style="tutorial",
                platform="xiaohongshu",
            )
            monkeypatch.setattr(
                app.generator,
                "generate",
                AsyncMock(return_value=mock_content),
            )
            post_id, content, images = await app.generate_content(
                "test topic", "xiaohongshu", "tutorial"
            )
            assert post_id > 0
            assert content.title == "AI Title"
            assert images == []

            post = await app.db.get_post(post_id)
            assert post["status"] == "draft"
            assert post["platform"] == "xiaohongshu"
        finally:
            await app.db.close()

    @pytest.mark.asyncio
    async def test_generate_content_with_images(self, app, monkeypatch):
        """generate_content can auto-generate card images."""
        await app.db.connect()
        try:
            mock_content = GeneratedContent(
                title="Title",
                content="Some content " * 20,
                tags=["tag1"],
                style="tutorial",
                platform="xiaohongshu",
            )
            monkeypatch.setattr(
                app.generator,
                "generate",
                AsyncMock(return_value=mock_content),
            )
            # Return fake PNG bytes
            fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
            monkeypatch.setattr(
                app.generator,
                "generate_image_from_code",
                AsyncMock(return_value=fake_png),
            )
            post_id, content, images = await app.generate_content(
                "test topic",
                "xiaohongshu",
                "tutorial",
                auto_generate_images=True,
                image_count=2,
            )
            assert len(images) == 2
            for img_path in images:
                assert img_path.endswith(".png")
        finally:
            await app.db.close()


class TestLoginFlow:
    @pytest.mark.asyncio
    async def test_login_success(self, app, monkeypatch):
        """Successful login saves session and upserts account."""
        await app.db.connect()
        try:
            mock_context = AsyncMock()
            monkeypatch.setattr(app.browser, "get_context", AsyncMock(return_value=mock_context))
            monkeypatch.setattr(app.browser, "save_session", AsyncMock())
            monkeypatch.setattr(app.browser, "_state_path", lambda self_or_p: MagicMock(__str__=lambda s: "/tmp/state.json") if not isinstance(self_or_p, str) else MagicMock(__str__=lambda s: "/tmp/state.json"))

            mock_info = MagicMock()
            mock_info.username = "user1"
            mock_info.nickname = "User One"
            mock_info.avatar_url = "https://example.com/avatar.jpg"
            mock_info.follower_count = 100
            mock_info.following_count = 50

            mock_connector = AsyncMock()
            mock_connector.login.return_value = True
            mock_connector.get_account_info.return_value = mock_info

            with patch("content_pilot.app.PlatformRegistry") as mock_registry:
                mock_registry.create.return_value = mock_connector
                # Patch _state_path on the browser instance
                app.browser._state_path = lambda p: MagicMock(__str__=lambda s: "/tmp/state.json")
                result = await app.login("xiaohongshu")

            assert result is True
            account = await app.db.get_account("xiaohongshu")
            assert account is not None
            assert account["username"] == "user1"
        finally:
            await app.db.close()

    @pytest.mark.asyncio
    async def test_login_failure(self, app, monkeypatch):
        """Failed login returns False and doesn't save account."""
        await app.db.connect()
        try:
            mock_context = AsyncMock()
            monkeypatch.setattr(app.browser, "get_context", AsyncMock(return_value=mock_context))

            mock_connector = AsyncMock()
            mock_connector.login.return_value = False

            with patch("content_pilot.app.PlatformRegistry") as mock_registry:
                mock_registry.create.return_value = mock_connector
                result = await app.login("xiaohongshu")

            assert result is False
            account = await app.db.get_account("xiaohongshu")
            assert account is None
        finally:
            await app.db.close()
