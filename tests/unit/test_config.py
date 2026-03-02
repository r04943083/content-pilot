"""Tests for configuration loading."""

import os

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
        assert settings.ai.qwen_model == "qwen-plus"
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
