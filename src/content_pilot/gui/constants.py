"""Shared constants for the GUI."""

from content_pilot.constants import PLATFORMS, STYLES

__all__ = [
    "PLATFORMS",
    "STYLES",
    "STATUS_COLORS",
    "PLATFORM_ICONS",
    "PLATFORM_COLORS",
    "COLORS",
    "SPACING",
]

# Design System Colors
COLORS = {
    "primary": "#6366F1",  # Modern indigo
    "primary_light": "#818CF8",
    "primary_dark": "#4F46E5",
    "accent": "#10B981",  # Emerald - success
    "warning": "#F59E0B",  # Amber
    "background": "#0F0F17",  # Dark background
    "surface": "#1E1E2E",  # Card surface
    "text_primary": "#FFFFFF",
    "text_secondary": "rgba(255,255,255,0.7)",
}

# Spacing system
SPACING = {
    "xs": "4px",
    "sm": "8px",
    "md": "16px",
    "lg": "24px",
    "xl": "32px",
}

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
