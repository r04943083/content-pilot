"""Tests for content templates."""

from content_pilot.content.templates import get_prompt


def test_get_prompt_xiaohongshu():
    prompt = get_prompt("xiaohongshu", "tutorial", "Python学习技巧")
    assert "Python学习技巧" in prompt
    assert "小红书" in prompt


def test_get_prompt_douyin():
    prompt = get_prompt("douyin", "review", "手机测评")
    assert "手机测评" in prompt
    assert "抖音" in prompt


def test_get_prompt_unknown_platform():
    prompt = get_prompt("unknown_platform", "tutorial", "test")
    assert "test" in prompt


def test_get_prompt_all_styles():
    for style in ["tutorial", "review", "lifestyle", "knowledge", "story"]:
        prompt = get_prompt("xiaohongshu", style, "test topic")
        assert "test topic" in prompt
