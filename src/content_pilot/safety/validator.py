"""Content validation before publishing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from content_pilot.config import get_settings


@dataclass
class ValidationResult:
    valid: bool = True
    errors: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []


class ContentValidator:
    """Validates content against platform rules and safety checks."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._banned_words: list[str] = []
        self._load_banned_words()

    def _load_banned_words(self) -> None:
        path = self._settings.safety.banned_words_file
        if path:
            p = Path(path)
            if p.exists():
                self._banned_words = [
                    line.strip()
                    for line in p.read_text().splitlines()
                    if line.strip() and not line.startswith("#")
                ]

    def validate(
        self,
        platform: str,
        title: str = "",
        content: str = "",
        tags: list[str] | None = None,
        images: list[str] | None = None,
    ) -> ValidationResult:
        """Validate content against platform constraints and safety rules."""
        result = ValidationResult()
        tags = tags or []
        images = images or []

        platform_cfg = getattr(self._settings.platforms, platform, None)
        if platform_cfg is None:
            result.valid = False
            result.errors.append(f"Unknown platform: {platform}")
            return result

        # Title length
        if title and hasattr(platform_cfg, "max_title_length"):
            if len(title) > platform_cfg.max_title_length:
                result.errors.append(
                    f"Title too long: {len(title)}/{platform_cfg.max_title_length}"
                )

        # Content length
        max_len = platform_cfg.max_content_length
        if content and len(content) > max_len:
            result.errors.append(
                f"Content too long: {len(content)}/{max_len}"
            )

        # Tag count
        if len(tags) > platform_cfg.max_tags:
            result.errors.append(
                f"Too many tags: {len(tags)}/{platform_cfg.max_tags}"
            )

        # Image count
        if len(images) > platform_cfg.max_images:
            result.errors.append(
                f"Too many images: {len(images)}/{platform_cfg.max_images}"
            )

        # Banned words
        text = f"{title} {content}"
        for word in self._banned_words:
            if word in text:
                result.errors.append(f"Banned word detected: '{word}'")

        # Empty content check
        if not content and not images:
            result.errors.append("Content cannot be empty (no text or images)")

        if result.errors:
            result.valid = False

        return result
