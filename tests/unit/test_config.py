"""Tests for configuration loading."""

import os

import pytest

from content_pilot.config.settings import AIConfig, Settings, _deep_merge


def test_default_settings():
    """Settings can be created with defaults."""
    settings = Settings()
    assert settings.general.timezone == "Asia/Shanghai"
    assert settings.ai.provider in ("claude", "openai", "qwen", "glm")
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
    os.environ["CP_AI__PROVIDER"] = "openai"
    try:
        settings = Settings()
        assert settings.ai.provider == "openai"
    finally:
        del os.environ["CP_AI__PROVIDER"]


def test_qwen_provider_config():
    """Qwen provider can be configured via env vars."""
    os.environ["CP_AI__PROVIDER"] = "qwen"
    os.environ["CP_AI__QWEN_API_KEY"] = "sk-test-qwen"
    try:
        settings = Settings()
        assert settings.ai.provider == "qwen"
        assert settings.ai.qwen_api_key == "sk-test-qwen"
        assert settings.ai.qwen_model == "qwen3-max-2026-01-23"
        assert "dashscope.aliyuncs.com" in settings.ai.qwen_base_url
    finally:
        del os.environ["CP_AI__PROVIDER"]
        del os.environ["CP_AI__QWEN_API_KEY"]


def test_glm_provider_config():
    """GLM provider can be configured via env vars."""
    os.environ["CP_AI__PROVIDER"] = "glm"
    os.environ["CP_AI__GLM_API_KEY"] = "test-glm-key"
    try:
        settings = Settings()
        assert settings.ai.provider == "glm"
        assert settings.ai.glm_api_key == "test-glm-key"
        assert settings.ai.glm_model == "glm-4-flash"
        assert "bigmodel.cn" in settings.ai.glm_base_url
    finally:
        del os.environ["CP_AI__PROVIDER"]
        del os.environ["CP_AI__GLM_API_KEY"]


def test_default_provider_is_qwen():
    """Default provider should be qwen."""
    ai = AIConfig()
    assert ai.provider == "qwen"


def test_config_load_with_missing_toml(tmp_path):
    """Settings.load() works when config files don't exist."""
    settings = Settings.load(user_config=tmp_path / "nonexistent.toml")
    assert settings.general.timezone == "Asia/Shanghai"


def test_deep_merge_empty_base():
    result = _deep_merge({}, {"a": 1})
    assert result == {"a": 1}


def test_deep_merge_empty_override():
    result = _deep_merge({"a": 1}, {})
    assert result == {"a": 1}


def test_deep_merge_nested_override():
    base = {"a": {"b": {"c": 1, "d": 2}}}
    override = {"a": {"b": {"c": 99}}}
    result = _deep_merge(base, override)
    assert result["a"]["b"]["c"] == 99
    assert result["a"]["b"]["d"] == 2


def test_default_values():
    """All default values are sensible."""
    s = Settings()
    assert s.database.path == "data/content_pilot.db"
    assert s.browser.headless is False
    assert s.browser.timeout == 60000
    assert s.browser.stealth is True
    assert s.safety.min_interval_minutes == 60
    assert s.scheduler.coalesce is True
    assert s.scheduler.max_instances == 1
    assert s.ai.max_tokens == 2000
    assert s.ai.temperature == 0.7


def test_env_var_override_nested():
    """Nested env var override with CP_ prefix."""
    os.environ["CP_SAFETY__MAX_POSTS_PER_DAY"] = "10"
    try:
        settings = Settings()
        assert settings.safety.max_posts_per_day == 10
    finally:
        del os.environ["CP_SAFETY__MAX_POSTS_PER_DAY"]


def test_invalid_provider_rejected():
    """Invalid provider value raises validation error."""
    import pydantic
    with pytest.raises(pydantic.ValidationError):
        AIConfig(provider="invalid_provider")
