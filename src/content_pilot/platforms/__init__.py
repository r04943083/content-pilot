"""Platform connectors for social media automation."""

from content_pilot.platforms.base import AbstractPlatform, AccountInfo, PublishResult
from content_pilot.platforms.registry import PlatformRegistry

__all__ = ["AbstractPlatform", "AccountInfo", "PublishResult", "PlatformRegistry"]
