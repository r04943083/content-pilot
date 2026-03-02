"""Tests for configuration loading."""

from content_pilot.config.settings import Settings, _deep_merge


def test_default_settings():
    """Settings can be created with defaults."""
    settings = Settings()
    assert settings.general.timezone == "Asia/Shanghai"
    assert settings.ai.provider in ("claude", "openai")
    assert settings.safety.max_posts_per_day == 3
    assert settings.safety.require_review is True


def test_deep_merge():
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    override = {"b": {"c": 99}, "e": 5}
    result = _deep_merge(base, override)
    assert result == {"a": 1, "b": {"c": 99, "d": 3}, "e": 5}


def test_platform_config():
    settings = Settings()
    assert "xiaohongshu" in settings.platforms.enabled
    assert settings.platforms.xiaohongshu.max_tags == 10


def test_env_override():
    """Settings can be overridden via env vars with CP_ prefix."""
    import os
    os.environ["CP_AI__PROVIDER"] = "openai"
    try:
        settings = Settings()
        assert settings.ai.provider == "openai"
    finally:
        del os.environ["CP_AI__PROVIDER"]
