"""AI content generation engine supporting Claude and OpenAI."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from content_pilot.config import get_settings
from content_pilot.content.templates import get_prompt

logger = logging.getLogger(__name__)


@dataclass
class GeneratedContent:
    title: str = ""
    content: str = ""
    tags: list[str] = field(default_factory=list)
    style: str = ""
    platform: str = ""


class ContentGenerator:
    """Generates platform-optimized content using Claude or OpenAI."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def generate(
        self,
        topic: str,
        platform: str,
        style: str = "tutorial",
    ) -> GeneratedContent:
        """Generate content for the given topic, platform, and style."""
        prompt = get_prompt(platform, style, topic)
        provider = self._settings.ai.provider

        if provider == "claude":
            raw = await self._generate_claude(prompt)
        elif provider == "openai":
            raw = await self._generate_openai(prompt)
        else:
            raise ValueError(f"Unknown AI provider: {provider}")

        return self._parse_response(raw, platform, style)

    async def _generate_claude(self, prompt: str) -> str:
        import anthropic

        client = anthropic.AsyncAnthropic(
            api_key=self._settings.ai.anthropic_api_key
        )
        message = await client.messages.create(
            model=self._settings.ai.claude_model,
            max_tokens=self._settings.ai.max_tokens,
            temperature=self._settings.ai.temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    async def _generate_openai(self, prompt: str) -> str:
        import openai

        client = openai.AsyncOpenAI(api_key=self._settings.ai.openai_api_key)
        response = await client.chat.completions.create(
            model=self._settings.ai.openai_model,
            max_tokens=self._settings.ai.max_tokens,
            temperature=self._settings.ai.temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""

    async def generate_image(self, prompt: str) -> bytes | None:
        """Generate an image using DALL-E. Returns PNG bytes or None."""
        try:
            import openai

            if not self._settings.ai.openai_api_key:
                logger.warning("OpenAI API key not set, skipping image generation")
                return None

            client = openai.AsyncOpenAI(api_key=self._settings.ai.openai_api_key)
            response = await client.images.generate(
                model=self._settings.ai.dalle_model,
                prompt=prompt,
                size="1024x1024",
                response_format="b64_json",
                n=1,
            )
            import base64
            return base64.b64decode(response.data[0].b64_json)
        except Exception as e:
            logger.error("Image generation failed: %s", e)
            return None

    def _parse_response(
        self, raw: str, platform: str, style: str
    ) -> GeneratedContent:
        """Parse AI response into structured content."""
        lines = raw.strip().split("\n")
        title = ""
        content_lines: list[str] = []
        tags: list[str] = []
        section = "content"

        for line in lines:
            stripped = line.strip()
            if stripped.lower().startswith("title:") or stripped.lower().startswith("标题:"):
                title = stripped.split(":", 1)[1].strip().strip("\"'《》")
                continue
            if stripped.lower().startswith("tags:") or stripped.lower().startswith("标签:"):
                tag_str = stripped.split(":", 1)[1].strip()
                tags = [
                    t.strip().strip("#")
                    for t in tag_str.replace("#", " #").split("#")
                    if t.strip()
                ]
                continue
            content_lines.append(line)

        content = "\n".join(content_lines).strip()

        # If no title was extracted, use first line
        if not title and content:
            first_line = content.split("\n")[0].strip()
            if len(first_line) <= 50:
                title = first_line
                content = "\n".join(content.split("\n")[1:]).strip()

        return GeneratedContent(
            title=title,
            content=content,
            tags=tags,
            style=style,
            platform=platform,
        )
