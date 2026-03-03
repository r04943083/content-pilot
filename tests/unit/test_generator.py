"""Tests for content generator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content_pilot.content.generator import ContentGenerator, GeneratedContent


@pytest.fixture
def mock_settings():
    from content_pilot.config.settings import Settings

    s = Settings()
    s.ai.provider = "claude"
    s.ai.anthropic_api_key = "sk-test-key-123"
    return s


@pytest.fixture
def generator(mock_settings, monkeypatch):
    monkeypatch.setattr("content_pilot.content.generator.get_settings", lambda: mock_settings)
    monkeypatch.setattr("content_pilot.config.get_settings", lambda: mock_settings)
    return ContentGenerator()


class TestApiKeyValidation:
    def test_empty_api_key_raises(self, monkeypatch):
        from content_pilot.config.settings import Settings

        s = Settings()
        s.ai.provider = "claude"
        s.ai.anthropic_api_key = ""
        monkeypatch.setattr("content_pilot.content.generator.get_settings", lambda: s)
        monkeypatch.setattr("content_pilot.config.get_settings", lambda: s)

        gen = ContentGenerator()
        with pytest.raises(RuntimeError, match="API key not set"):
            gen._check_api_key()

    def test_whitespace_api_key_raises(self, monkeypatch):
        from content_pilot.config.settings import Settings

        s = Settings()
        s.ai.provider = "openai"
        s.ai.openai_api_key = "   "
        monkeypatch.setattr("content_pilot.content.generator.get_settings", lambda: s)
        monkeypatch.setattr("content_pilot.config.get_settings", lambda: s)

        gen = ContentGenerator()
        with pytest.raises(RuntimeError, match="API key not set"):
            gen._check_api_key()

    def test_valid_api_key_no_raise(self, generator):
        """Valid API key should not raise."""
        generator._check_api_key()  # Should not raise

    def test_missing_provider_key(self, monkeypatch):
        """Each provider checks its own key."""
        from content_pilot.config.settings import Settings

        for provider, key_field in [
            ("claude", "anthropic_api_key"),
            ("openai", "openai_api_key"),
            ("qwen", "qwen_api_key"),
            ("glm", "glm_api_key"),
        ]:
            s = Settings()
            s.ai.provider = provider
            setattr(s.ai, key_field, "")
            monkeypatch.setattr("content_pilot.content.generator.get_settings", lambda: s)
            monkeypatch.setattr("content_pilot.config.get_settings", lambda: s)

            gen = ContentGenerator()
            with pytest.raises(RuntimeError, match="API key not set"):
                gen._check_api_key()


class TestProviderSelection:
    @pytest.mark.asyncio
    async def test_claude_provider(self, generator, monkeypatch):
        """Claude provider calls _generate_claude."""
        generator._settings.ai.provider = "claude"
        mock_gen = AsyncMock(return_value="标题: Test Title\nSome content\n标签: #test")
        monkeypatch.setattr(generator, "_generate_claude", mock_gen)

        result = await generator.generate("test", "xiaohongshu", "tutorial")
        mock_gen.assert_awaited_once()
        assert isinstance(result, GeneratedContent)

    @pytest.mark.asyncio
    async def test_openai_provider(self, generator, monkeypatch):
        generator._settings.ai.provider = "openai"
        generator._settings.ai.openai_api_key = "sk-test"
        mock_gen = AsyncMock(return_value="标题: Test\nContent\n标签: #test")
        monkeypatch.setattr(generator, "_generate_openai", mock_gen)

        result = await generator.generate("test", "xiaohongshu", "tutorial")
        mock_gen.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_qwen_provider(self, generator, monkeypatch):
        generator._settings.ai.provider = "qwen"
        generator._settings.ai.qwen_api_key = "sk-test"
        mock_gen = AsyncMock(return_value="标题: Test\nContent\n标签: #test")
        monkeypatch.setattr(generator, "_generate_qwen", mock_gen)

        result = await generator.generate("test", "xiaohongshu", "tutorial")
        mock_gen.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_glm_provider(self, generator, monkeypatch):
        generator._settings.ai.provider = "glm"
        generator._settings.ai.glm_api_key = "sk-test"
        mock_gen = AsyncMock(return_value="标题: Test\nContent\n标签: #test")
        monkeypatch.setattr(generator, "_generate_glm", mock_gen)

        result = await generator.generate("test", "xiaohongshu", "tutorial")
        mock_gen.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unknown_provider_raises(self, generator, monkeypatch):
        generator._settings.ai.provider = "unknown"
        with pytest.raises(ValueError, match="Unknown AI provider"):
            await generator.generate("test", "xiaohongshu", "tutorial")


class TestParseResponse:
    def test_parse_with_title_and_tags(self, generator):
        raw = "标题: Python学习技巧\n\n正文内容在这里。\n\n标签: #Python #学习"
        result = generator._parse_response(raw, "xiaohongshu", "tutorial")
        assert result.title == "Python学习技巧"
        assert "正文内容在这里" in result.content
        assert "Python" in result.tags
        assert result.platform == "xiaohongshu"
        assert result.style == "tutorial"

    def test_parse_english_headers(self, generator):
        raw = "Title: My Great Post\n\nContent goes here.\n\nTags: #tech #ai"
        result = generator._parse_response(raw, "weibo", "review")
        assert result.title == "My Great Post"
        assert "tech" in result.tags

    def test_parse_no_title_uses_first_line(self, generator):
        raw = "Short Title\n\nThis is the content body."
        result = generator._parse_response(raw, "xiaohongshu", "tutorial")
        assert result.title == "Short Title"
        assert "content body" in result.content

    def test_parse_no_title_long_first_line(self, generator):
        """First line longer than 50 chars should not be used as title."""
        raw = "A" * 60 + "\n\nContent."
        result = generator._parse_response(raw, "xiaohongshu", "tutorial")
        assert result.title == ""

    def test_parse_empty_response(self, generator):
        result = generator._parse_response("", "xiaohongshu", "tutorial")
        assert result.title == ""
        assert result.content == ""
        assert result.tags == []


class TestPromptTemplateRendering:
    def test_prompt_contains_topic(self, generator, monkeypatch):
        """Generated prompt should contain the topic."""
        from content_pilot.content.templates import get_prompt

        prompt = get_prompt("xiaohongshu", "tutorial", "Python编程")
        assert "Python编程" in prompt

    def test_prompt_has_output_format(self, generator, monkeypatch):
        from content_pilot.content.templates import get_prompt

        prompt = get_prompt("xiaohongshu", "tutorial", "test")
        assert "标题" in prompt
        assert "标签" in prompt
