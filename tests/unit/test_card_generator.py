"""Tests for card generator: HTML extraction and template rendering."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content_pilot.content.card_generator import CardGenerator, CARD_WIDTH, CARD_HEIGHT
from content_pilot.content.card_templates import (
    CARD_STYLES,
    get_card_prompt,
    get_fallback_html,
)


@pytest.fixture
def mock_settings():
    from content_pilot.config.settings import Settings

    return Settings()


@pytest.fixture
def generator(mock_settings):
    return CardGenerator(mock_settings)


class TestExtractHtml:
    def test_extract_full_doctype(self, generator):
        """Extract HTML from response containing full DOCTYPE."""
        raw = 'Some preamble\n<!DOCTYPE html>\n<html><body>hi</body></html>\nExtra text'
        result = generator._extract_html(raw)
        assert result is not None
        assert result.startswith("<!DOCTYPE html>")
        assert "</html>" in result

    def test_extract_html_tag_only(self, generator):
        """Extract HTML when only <html> tag present (no DOCTYPE)."""
        raw = '<html lang="zh"><body>hello</body></html>'
        result = generator._extract_html(raw)
        assert result is not None
        assert "<!DOCTYPE html>" in result
        assert "<body>hello</body>" in result

    def test_extract_starts_with_doctype(self, generator):
        """Return raw content that starts with DOCTYPE as-is."""
        raw = '<!DOCTYPE html>\n<html><body>test</body></html>'
        result = generator._extract_html(raw)
        assert result == raw

    def test_extract_starts_with_html(self, generator):
        """<html> tag gets DOCTYPE prepended by Pattern 2."""
        raw = '<html><body>test</body></html>'
        result = generator._extract_html(raw)
        assert result is not None
        assert "<!DOCTYPE html>" in result
        assert "<body>test</body>" in result

    def test_extract_no_html(self, generator):
        """Return None when no HTML is found."""
        raw = "Just some plain text without any HTML."
        result = generator._extract_html(raw)
        assert result is None

    def test_extract_html_in_markdown_block(self, generator):
        """Extract HTML even if wrapped in markdown code blocks."""
        raw = '```html\n<!DOCTYPE html>\n<html><body>test</body></html>\n```'
        result = generator._extract_html(raw)
        assert result is not None
        assert "<!DOCTYPE html>" in result

    def test_extract_case_insensitive(self, generator):
        """DOCTYPE matching should be case-insensitive."""
        raw = '<!doctype html>\n<HTML><BODY>test</BODY></HTML>'
        result = generator._extract_html(raw)
        assert result is not None


class TestGenerateCard:
    @pytest.mark.asyncio
    async def test_fallback_on_ai_failure(self, generator, monkeypatch):
        """Uses fallback template when AI generation fails."""
        monkeypatch.setattr(generator, "_generate_html", AsyncMock(return_value=None))
        monkeypatch.setattr(generator, "_render_to_image", AsyncMock(return_value=b"PNG_BYTES"))

        result = await generator.generate_card("Title", "Summary", ["tag1"])
        assert result == b"PNG_BYTES"

        # Verify fallback HTML was passed to render
        render_call = generator._render_to_image.call_args
        html_arg = render_call[0][0]
        assert "Title" in html_arg
        assert "Summary" in html_arg

    @pytest.mark.asyncio
    async def test_invalid_style_defaults_to_quote(self, generator, monkeypatch):
        """Invalid style falls back to 'quote'."""
        monkeypatch.setattr(generator, "_generate_html", AsyncMock(return_value=None))
        monkeypatch.setattr(generator, "_render_to_image", AsyncMock(return_value=b"PNG"))

        await generator.generate_card("T", "S", [], style="nonexistent")
        # Should not raise

    @pytest.mark.asyncio
    async def test_render_error_returns_none(self, generator, monkeypatch):
        """When rendering fails, return None."""
        monkeypatch.setattr(generator, "_generate_html", AsyncMock(return_value="<html></html>"))
        monkeypatch.setattr(
            generator, "_render_to_image", AsyncMock(return_value=None)
        )
        result = await generator.generate_card("T", "S", [])
        assert result is None


class TestCallAi:
    @pytest.mark.asyncio
    async def test_unknown_provider_returns_none(self, generator, monkeypatch):
        """Unknown provider returns None."""
        mock_ai = MagicMock()
        mock_ai.provider = "unknown_provider"
        generator._settings.ai = mock_ai

        result = await generator._call_ai("test prompt")
        assert result is None


class TestCardTemplates:
    def test_get_card_prompt_has_content(self):
        prompt = get_card_prompt("My Title", "Summary text", ["python", "ai"])
        assert "My Title" in prompt
        assert "Summary text" in prompt
        assert "#python" in prompt
        assert "#ai" in prompt

    def test_get_card_prompt_no_tags(self):
        prompt = get_card_prompt("Title", "Summary", [])
        assert "Title" in prompt

    def test_get_card_prompt_long_summary_truncated(self):
        long_summary = "A" * 500
        prompt = get_card_prompt("Title", long_summary, [])
        # Summary should be truncated to 300 chars in the prompt
        assert "A" * 300 in prompt

    def test_get_fallback_html_valid(self):
        html = get_fallback_html("Test Title", "Test Summary", ["tag1", "tag2"])
        assert "<!DOCTYPE html>" in html
        assert "Test Title" in html
        assert "Test Summary" in html
        assert "#tag1" in html

    def test_get_fallback_html_truncates_long_title(self):
        long_title = "A" * 100
        html = get_fallback_html(long_title, "Summary", [])
        # Title should be capped at 50 chars
        assert "A" * 50 in html
        assert "A" * 51 not in html

    def test_get_fallback_html_limits_tags(self):
        tags = [f"tag{i}" for i in range(10)]
        html = get_fallback_html("Title", "Summary", tags)
        # Only first 5 tags should appear
        assert "#tag4" in html
        assert "#tag5" not in html

    def test_all_card_styles_exist(self):
        for style in ["quote", "title", "list", "minimal"]:
            assert style in CARD_STYLES
            assert "name" in CARD_STYLES[style]
            assert "description" in CARD_STYLES[style]
