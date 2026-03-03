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
    "primary_hover": "#7577F5",
    "primary_active": "#5254D4",
    "accent": "#10B981",  # Emerald - success
    "accent_hover": "#34D399",
    "warning": "#F59E0B",  # Amber
    "error": "#EF4444",  # Red
    "info": "#3B82F6",  # Blue
    "background": "#111119",  # Warmer dark background
    "surface": "#1C1C2E",  # Lighter card surface
    "surface_elevated": "#252540",  # Elevated surface for dropdowns/modals
    "border": "rgba(255,255,255,0.08)",  # Subtle border
    "border_hover": "rgba(255,255,255,0.15)",  # Border on hover
    "text_primary": "#F1F1F6",  # Better text contrast
    "text_secondary": "rgba(241,241,246,0.6)",
    "card_radius": "12px",
}

# Spacing system
SPACING = {
    "xs": "4px",
    "sm": "8px",
    "md": "16px",
    "lg": "24px",
    "xl": "32px",
    "card_padding": "16px",
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
