"""File utility functions shared across the application."""

from pathlib import Path

from content_pilot.config import get_settings


def get_images_dir() -> Path:
    """Get the images directory path, creating it if it doesn't exist."""
    data_dir = Path(get_settings().general.data_dir).resolve()
    images_dir = data_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    return images_dir
