"""Card generator: AI generates HTML/CSS, Playwright renders to image."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from content_pilot.content.card_templates import (
    CARD_STYLES,
    FALLBACK_TEMPLATE,
    get_card_prompt,
    get_fallback_html,
)

if TYPE_CHECKING:
    from content_pilot.config import Settings

logger = logging.getLogger(__name__)

# Card image dimensions
CARD_WIDTH = 1080
CARD_HEIGHT = 1350
DEVICE_SCALE_FACTOR = 2  # 2x for high resolution


class CardGenerator:
    """Generates social media cards using AI-written HTML/CSS rendered via Playwright."""

    def __init__(self, settings: "Settings") -> None:
        self._settings = settings

    async def generate_card(
        self,
        title: str,
        summary: str,
        tags: list[str],
        style: str = "quote",
    ) -> bytes | None:
        """
        Generate a card image.

        1. Call AI to generate HTML/CSS code
        2. Render with Playwright
        3. Return PNG bytes

        Args:
            title: Card title
            summary: Card summary/content
            tags: List of tags
            style: Card style (quote, title, list, minimal)

        Returns:
            PNG image bytes or None on failure
        """
        # Validate style
        if style not in CARD_STYLES:
            style = "quote"

        # Step 1: Generate HTML via AI
        html_content = await self._generate_html(title, summary, tags, style)

        if not html_content:
            logger.warning("AI HTML generation failed, using fallback template")
            html_content = get_fallback_html(title, summary, tags)

        # Step 2: Render to image
        return await self._render_to_image(html_content)

    async def _generate_html(
        self,
        title: str,
        summary: str,
        tags: list[str],
        style: str,
    ) -> str | None:
        """Call AI to generate HTML/CSS code."""
        try:
            prompt = get_card_prompt(title, summary, tags, style)
            raw = await self._call_ai(prompt)

            if not raw:
                return None

            # Extract HTML from response
            html = self._extract_html(raw)
            return html

        except Exception as e:
            logger.error("Failed to generate HTML: %s", e)
            return None

    async def _call_ai(self, prompt: str) -> str | None:
        """Call the configured AI provider."""
        ai = self._settings.ai
        provider = ai.provider

        try:
            if provider == "claude":
                return await self._call_anthropic(
                    prompt,
                    api_key=ai.anthropic_api_key,
                    base_url=None,
                    model=ai.claude_model,
                )
            elif provider == "openai":
                return await self._call_openai(
                    prompt,
                    api_key=ai.openai_api_key,
                    base_url=None,
                    model=ai.openai_model,
                )
            elif provider == "qwen":
                return await self._call_anthropic(
                    prompt,
                    api_key=ai.qwen_api_key,
                    base_url=ai.qwen_base_url,
                    model=ai.qwen_model,
                )
            elif provider == "glm":
                return await self._call_openai(
                    prompt,
                    api_key=ai.glm_api_key,
                    base_url=ai.glm_base_url,
                    model=ai.glm_model,
                )
            else:
                logger.error("Unknown AI provider: %s", provider)
                return None
        except Exception as e:
            logger.error("AI call failed: %s", e)
            return None

    async def _call_anthropic(
        self,
        prompt: str,
        *,
        api_key: str,
        base_url: str | None,
        model: str,
    ) -> str:
        """Call Anthropic-compatible API (Claude, Qwen)."""
        import anthropic

        kwargs: dict = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        client = anthropic.AsyncAnthropic(**kwargs)
        message = await client.messages.create(
            model=model,
            max_tokens=4000,  # More tokens for HTML generation
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    async def _call_openai(
        self,
        prompt: str,
        *,
        api_key: str,
        base_url: str | None,
        model: str,
    ) -> str:
        """Call OpenAI-compatible API (OpenAI, GLM)."""
        import openai

        kwargs: dict = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        client = openai.AsyncOpenAI(**kwargs)
        response = await client.chat.completions.create(
            model=model,
            max_tokens=4000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""

    def _extract_html(self, raw: str) -> str | None:
        """Extract HTML content from AI response."""
        # Try to find HTML between doctype and closing html tag
        # Pattern 1: Full HTML from <!DOCTYPE to </html>
        match = re.search(
            r"<!DOCTYPE\s+html>.*?</html>",
            raw,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            return match.group(0)

        # Pattern 2: From <html to </html>
        match = re.search(
            r"<html.*?</html>",
            raw,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            return "<!DOCTYPE html>\n" + match.group(0)

        # If the response looks like it starts with HTML
        stripped = raw.strip()
        if stripped.startswith("<!DOCTYPE") or stripped.startswith("<html"):
            return stripped

        logger.warning("Could not extract valid HTML from AI response")
        return None

    async def _render_to_image(self, html_content: str) -> bytes | None:
        """Render HTML to PNG using Playwright."""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page(
                    viewport={"width": CARD_WIDTH, "height": CARD_HEIGHT},
                    device_scale_factor=DEVICE_SCALE_FACTOR,
                )

                # Set the HTML content
                await page.set_content(html_content, wait_until="networkidle")

                # Take screenshot
                screenshot = await page.screenshot(type="png")

                await browser.close()
                return screenshot

        except ImportError:
            logger.error(
                "Playwright not installed. Run: pip install playwright && playwright install chromium"
            )
            return None
        except Exception as e:
            logger.error("Failed to render HTML to image: %s", e)
            return None

    async def render_html_to_image(self, html_content: str) -> bytes | None:
        """Public method to render arbitrary HTML to image."""
        return await self._render_to_image(html_content)
