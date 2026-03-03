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


def test_all_platform_style_combinations():
    """All platform/style combinations produce valid prompts."""
    platforms = ["xiaohongshu", "douyin", "bilibili", "weibo"]
    styles = ["tutorial", "review", "lifestyle", "knowledge", "story"]
    for platform in platforms:
        for style in styles:
            prompt = get_prompt(platform, style, "测试主题")
            assert "测试主题" in prompt
            assert len(prompt) > 50  # Should have substantial content


def test_prompt_contains_output_format():
    """Every prompt should include the output format instructions."""
    prompt = get_prompt("xiaohongshu", "tutorial", "test")
    assert "标题" in prompt
    assert "标签" in prompt


def test_bilibili_prompts():
    prompt = get_prompt("bilibili", "tutorial", "编程教程")
    assert "编程教程" in prompt
    assert "B站" in prompt


def test_weibo_prompts():
    prompt = get_prompt("weibo", "lifestyle", "生活分享")
    assert "生活分享" in prompt
    assert "微博" in prompt


def test_unknown_style_falls_back():
    """Unknown style falls back to tutorial."""
    prompt = get_prompt("xiaohongshu", "nonexistent_style", "test")
    assert "test" in prompt
    # Should still produce a valid prompt


def test_topic_substitution():
    """Topic placeholder is properly substituted."""
    topic = "unique_topic_12345"
    prompt = get_prompt("xiaohongshu", "tutorial", topic)
    assert topic in prompt
    assert "{topic}" not in prompt  # Placeholder should be resolved
