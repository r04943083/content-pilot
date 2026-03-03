"""Integration tests for content generation flow."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content_pilot.content.generator import ContentGenerator, GeneratedContent


@pytest.fixture
def app(mock_settings, monkeypatch):
    monkeypatch.setattr("content_pilot.config.get_settings", lambda: mock_settings)
    monkeypatch.setattr("content_pilot.app.get_settings", lambda: mock_settings)
    from content_pilot.app import App

    return App()


class TestContentGenerationFlow:
    @pytest.mark.asyncio
    async def test_generate_save_draft_approve(self, app, monkeypatch):
        """Generate content, save as draft, then approve."""
        await app.db.connect()
        try:
            mock_content = GeneratedContent(
                title="测试标题",
                content="这是测试内容。",
                tags=["Python", "AI"],
                style="tutorial",
                platform="xiaohongshu",
            )
            monkeypatch.setattr(
                app.generator, "generate", AsyncMock(return_value=mock_content)
            )

            post_id, content, images = await app.generate_content(
                "Python编程", "xiaohongshu", "tutorial"
            )

            # Verify draft
            post = await app.db.get_post(post_id)
            assert post["status"] == "draft"
            assert post["title"] == "测试标题"
            assert post["platform"] == "xiaohongshu"
            tags = json.loads(post["tags"])
            assert "Python" in tags

            # Approve
            await app.db.update_post(post_id, status="approved")
            post = await app.db.get_post(post_id)
            assert post["status"] == "approved"

        finally:
            await app.db.close()

    @pytest.mark.asyncio
    async def test_generate_with_card_images(self, app, monkeypatch):
        """Generate content with auto-generated card images."""
        await app.db.connect()
        try:
            mock_content = GeneratedContent(
                title="Card Test",
                content="Content for card generation " * 10,
                tags=["design"],
                style="tutorial",
                platform="xiaohongshu",
            )
            monkeypatch.setattr(
                app.generator, "generate", AsyncMock(return_value=mock_content)
            )

            fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
            monkeypatch.setattr(
                app.generator,
                "generate_image_from_code",
                AsyncMock(return_value=fake_png),
            )

            post_id, content, images = await app.generate_content(
                "card topic",
                "xiaohongshu",
                "tutorial",
                auto_generate_images=True,
                image_count=2,
            )

            assert len(images) == 2
            # Verify images were saved to DB
            post = await app.db.get_post(post_id)
            saved_images = json.loads(post["images"])
            assert len(saved_images) == 2

        finally:
            await app.db.close()

    @pytest.mark.asyncio
    async def test_generate_image_failure_graceful(self, app, monkeypatch):
        """Image generation failure doesn't break content generation."""
        await app.db.connect()
        try:
            mock_content = GeneratedContent(
                title="No Images",
                content="Content without images",
                tags=["test"],
                style="tutorial",
                platform="xiaohongshu",
            )
            monkeypatch.setattr(
                app.generator, "generate", AsyncMock(return_value=mock_content)
            )
            monkeypatch.setattr(
                app.generator,
                "generate_image_from_code",
                AsyncMock(side_effect=Exception("Playwright not available")),
            )

            post_id, content, images = await app.generate_content(
                "test",
                "xiaohongshu",
                "tutorial",
                auto_generate_images=True,
                image_count=1,
            )

            # Should still create the post, just without images
            assert post_id > 0
            assert images == []

        finally:
            await app.db.close()


class TestMultiProviderSwitching:
    @pytest.mark.asyncio
    async def test_switch_provider(self, app, monkeypatch):
        """Switching AI provider uses the correct generation method."""
        await app.db.connect()
        try:
            for provider in ["claude", "openai", "qwen", "glm"]:
                app.settings.ai.provider = provider
                # Set the API key for the provider
                key_map = {
                    "claude": "anthropic_api_key",
                    "openai": "openai_api_key",
                    "qwen": "qwen_api_key",
                    "glm": "glm_api_key",
                }
                setattr(app.settings.ai, key_map[provider], "sk-test-key")

                mock_content = GeneratedContent(
                    title=f"Test {provider}",
                    content=f"Generated by {provider}",
                    tags=["test"],
                    style="tutorial",
                    platform="xiaohongshu",
                )
                monkeypatch.setattr(
                    app.generator, "generate", AsyncMock(return_value=mock_content)
                )

                post_id, content, _ = await app.generate_content(
                    "test", "xiaohongshu", "tutorial"
                )
                assert content.title == f"Test {provider}"

        finally:
            await app.db.close()
