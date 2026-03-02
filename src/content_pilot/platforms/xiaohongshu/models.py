"""Data models for Xiaohongshu."""

from dataclasses import dataclass


@dataclass
class XHSNote:
    """Represents a Xiaohongshu note."""
    title: str = ""
    content: str = ""
    tags: list[str] | None = None
    images: list[str] | None = None
    note_type: str = "normal"  # normal / video
