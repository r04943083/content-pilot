"""Abstract base class for all platform connectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from playwright.async_api import BrowserContext


@dataclass
class AccountInfo:
    platform: str = ""
    username: str = ""
    nickname: str = ""
    avatar_url: str = ""
    follower_count: int = 0
    following_count: int = 0
    post_count: int = 0


@dataclass
class PublishResult:
    success: bool = False
    post_id: str = ""
    url: str = ""
    error: str = ""


@dataclass
class PostContent:
    title: str = ""
    content: str = ""
    tags: list[str] = field(default_factory=list)
    images: list[Path] = field(default_factory=list)
    video_path: Path | None = None


class AbstractPlatform(ABC):
    """Base class for platform connectors."""

    name: str = ""
    creator_url: str = ""

    def __init__(self, context: BrowserContext) -> None:
        self.context = context

    @abstractmethod
    async def login(self) -> bool:
        """Initiate login flow (usually QR code scan). Returns True on success."""

    @abstractmethod
    async def check_session(self) -> bool:
        """Check if current session is still valid."""

    @abstractmethod
    async def get_account_info(self) -> AccountInfo:
        """Fetch current account information."""

    @abstractmethod
    async def publish_text_image(self, post: PostContent) -> PublishResult:
        """Publish text+image content."""

    @abstractmethod
    async def publish_video(self, post: PostContent) -> PublishResult:
        """Publish video content."""

    @abstractmethod
    async def get_post_analytics(self, platform_post_id: str) -> dict:
        """Fetch analytics for a specific post."""

    async def close(self) -> None:
        """Cleanup resources."""
