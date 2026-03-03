"""Shared constants for the GUI."""

from content_pilot.constants import PLATFORMS, STYLES

__all__ = ["PLATFORMS", "STYLES", "STATUS_COLORS", "PLATFORM_ICONS", "PLATFORM_COLORS"]

STATUS_COLORS: dict[str, str] = {
    "draft": "grey",
    "approved": "blue",
    "scheduled": "orange",
    "publishing": "amber",
    "published": "green",
    "failed": "red",
}

PLATFORM_ICONS: dict[str, str] = {
    "xiaohongshu": "auto_stories",
    "douyin": "music_video",
    "bilibili": "smart_display",
    "weibo": "public",
}

PLATFORM_COLORS: dict[str, str] = {
    "xiaohongshu": "#FF2442",
    "douyin": "#010101",
    "bilibili": "#00A1D6",
    "weibo": "#E6162D",
}
