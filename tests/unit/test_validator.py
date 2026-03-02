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
        title="A" * 100,
        content="Content here",
    )
    assert not result.valid
    assert any("title" in e.lower() for e in result.errors)
