"""Platform factory registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import BrowserContext

    from content_pilot.platforms.base import AbstractPlatform


class PlatformRegistry:
    """Registry for platform connector classes."""

    _platforms: dict[str, type[AbstractPlatform]] = {}

    @classmethod
    def register(cls, name: str):
        """Decorator to register a platform connector."""

        def decorator(platform_cls: type[AbstractPlatform]):
            cls._platforms[name] = platform_cls
            return platform_cls

        return decorator

    @classmethod
    def create(cls, name: str, context: BrowserContext) -> AbstractPlatform:
        """Create a platform connector instance by name."""
        if name not in cls._platforms:
            available = ", ".join(cls._platforms.keys())
            raise ValueError(
                f"Unknown platform '{name}'. Available: {available}"
            )
        return cls._platforms[name](context)

    @classmethod
    def available(cls) -> list[str]:
        return list(cls._platforms.keys())
