"""Tests for content validator."""

from content_pilot.safety.validator import ContentValidator


def test_valid_content():
    v = ContentValidator()
    result = v.validate(
        platform="xiaohongshu",
        title="Test",
        content="Hello world",
        tags=["tag1", "tag2"],
    )
    assert result.valid
    assert not result.errors


def test_empty_content():
    v = ContentValidator()
    result = v.validate(
        platform="xiaohongshu",
        title="Test",
        content="",
        tags=[],
        images=[],
    )
    assert not result.valid
    assert any("empty" in e.lower() for e in result.errors)


def test_too_many_tags():
    v = ContentValidator()
    result = v.validate(
        platform="xiaohongshu",
        title="Test",
        content="Content here",
        tags=[f"tag{i}" for i in range(20)],
    )
    assert not result.valid
    assert any("tags" in e.lower() for e in result.errors)


def test_title_too_long():
    v = ContentValidator()
    result = v.validate(
        platform="xiaohongshu",
        title="A" * 200,
        content="Content here",
    )
    assert not result.valid
    assert any("title" in e.lower() for e in result.errors)


def test_title_at_max_length():
    """Title exactly at max_title_length should be valid."""
    v = ContentValidator()
    max_len = v._settings.platforms.xiaohongshu.max_title_length
    result = v.validate(
        platform="xiaohongshu",
        title="A" * max_len,
        content="Content here",
    )
    # Should have no title length error
    assert not any("title" in e.lower() for e in result.errors)


def test_content_too_long():
    v = ContentValidator()
    max_len = v._settings.platforms.xiaohongshu.max_content_length
    result = v.validate(
        platform="xiaohongshu",
        title="Test",
        content="A" * (max_len + 1),
    )
    assert not result.valid
    assert any("content" in e.lower() for e in result.errors)


def test_content_at_max_length():
    """Content at exact max length should not trigger error."""
    v = ContentValidator()
    max_len = v._settings.platforms.xiaohongshu.max_content_length
    result = v.validate(
        platform="xiaohongshu",
        title="Test",
        content="A" * max_len,
    )
    assert not any("content too long" in e.lower() for e in result.errors)


def test_unknown_platform():
    v = ContentValidator()
    result = v.validate(
        platform="nonexistent_platform",
        title="Test",
        content="Content",
    )
    assert not result.valid
    assert any("unknown platform" in e.lower() for e in result.errors)


def test_too_many_images():
    v = ContentValidator()
    result = v.validate(
        platform="xiaohongshu",
        title="Test",
        content="Content",
        images=[f"img{i}.jpg" for i in range(20)],
    )
    assert not result.valid
    assert any("images" in e.lower() for e in result.errors)


def test_images_with_no_content():
    """Having images but no text should be valid."""
    v = ContentValidator()
    result = v.validate(
        platform="xiaohongshu",
        title="Test",
        content="",
        images=["img1.jpg"],
    )
    # Should be valid since images are provided
    assert result.valid


def test_multiple_errors():
    """Validator accumulates all errors."""
    v = ContentValidator()
    result = v.validate(
        platform="xiaohongshu",
        title="A" * 200,
        content="",
        tags=[f"tag{i}" for i in range(20)],
        images=[],
    )
    assert not result.valid
    assert len(result.errors) >= 2  # At least title + empty content errors


def test_all_platforms_valid():
    """All known platforms can be validated."""
    v = ContentValidator()
    for platform in ["xiaohongshu", "douyin", "bilibili", "weibo"]:
        result = v.validate(
            platform=platform,
            title="Test",
            content="Content here",
        )
        assert result.valid, f"Validation failed for {platform}: {result.errors}"
