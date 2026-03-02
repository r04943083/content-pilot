"""Configuration loading: default.toml → user.toml → environment variables."""

from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_toml(path: Path) -> dict:
    if path.exists():
        with open(path, "rb") as f:
            return tomllib.load(f)
    return {}


def _find_project_root() -> Path:
    """Walk up from cwd to find pyproject.toml."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return current


# --- Nested config models ---


class GeneralConfig(BaseModel):
    timezone: str = "Asia/Shanghai"
    data_dir: str = "data"
    log_level: str = "INFO"


class AIConfig(BaseModel):
    provider: Literal["claude", "openai"] = "claude"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"
    openai_model: str = "gpt-4o"
    dalle_model: str = "dall-e-3"
    max_tokens: int = 2000
    temperature: float = 0.7


class DatabaseConfig(BaseModel):
    path: str = "data/content_pilot.db"


class BrowserConfig(BaseModel):
    headless: bool = False
    timeout: int = 60000
    stealth: bool = True
    user_data_dir: str = "data/browser_contexts"


class SafetyConfig(BaseModel):
    require_review: bool = True
    max_posts_per_day: int = 3
    min_interval_minutes: int = 60
    banned_words_file: str = ""


class PlatformConfig(BaseModel):
    creator_url: str = ""
    best_hours: list[int] = []
    max_title_length: int = 100
    max_content_length: int = 2000
    max_description_length: int = 2000
    max_tags: int = 10
    max_images: int = 9


class PlatformsConfig(BaseModel):
    enabled: list[str] = ["xiaohongshu", "douyin", "bilibili", "weibo"]
    xiaohongshu: PlatformConfig = PlatformConfig()
    douyin: PlatformConfig = PlatformConfig()
    bilibili: PlatformConfig = PlatformConfig()
    weibo: PlatformConfig = PlatformConfig()


class SchedulerConfig(BaseModel):
    job_store: str = "sqlite"
    coalesce: bool = True
    max_instances: int = 1
    misfire_grace_time: int = 3600


# --- Main settings ---


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CP_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    general: GeneralConfig = GeneralConfig()
    ai: AIConfig = AIConfig()
    database: DatabaseConfig = DatabaseConfig()
    browser: BrowserConfig = BrowserConfig()
    safety: SafetyConfig = SafetyConfig()
    platforms: PlatformsConfig = PlatformsConfig()
    scheduler: SchedulerConfig = SchedulerConfig()

    @classmethod
    def load(cls, user_config: Path | None = None) -> Settings:
        """Load settings: default.toml → user.toml → env vars."""
        project_root = _find_project_root()
        default_path = project_root / "config" / "default.toml"
        defaults = _load_toml(default_path)

        if user_config and user_config.exists():
            user = _load_toml(user_config)
            defaults = _deep_merge(defaults, user)

        # Also check ~/.content-pilot/config.toml
        home_config = Path.home() / ".content-pilot" / "config.toml"
        if home_config.exists():
            home = _load_toml(home_config)
            defaults = _deep_merge(defaults, home)

        # Pydantic Settings handles env var overlay
        return cls(**defaults)


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base."""
    merged = base.copy()
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


@lru_cache
def get_settings() -> Settings:
    """Cached singleton settings."""
    return Settings.load()
