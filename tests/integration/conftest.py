"""Shared fixtures for integration tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from content_pilot.config.settings import Settings
from content_pilot.database import Database


@pytest.fixture
def mock_settings(tmp_path):
    """Settings with temp DB and data dirs."""
    s = Settings()
    s.database.path = str(tmp_path / "test.db")
    s.browser.user_data_dir = str(tmp_path / "browser_contexts")
    s.general.data_dir = str(tmp_path / "data")
    s.ai.provider = "claude"
    s.ai.anthropic_api_key = "sk-test-integration-key"
    return s


@pytest.fixture
async def db(tmp_path):
    """Temp database for integration tests."""
    database = Database(tmp_path / "test.db")
    await database.connect()
    yield database
    await database.close()


@pytest.fixture
def mock_browser():
    """Mocked browser manager."""
    browser = AsyncMock()
    mock_context = AsyncMock()
    browser.get_context = AsyncMock(return_value=mock_context)
    browser.save_session = AsyncMock()
    browser.start = AsyncMock()
    browser.stop = AsyncMock()
    browser._state_path = lambda p: MagicMock(__str__=lambda s: f"/tmp/state_{p}.json")
    return browser


@pytest.fixture
def mock_ai_provider():
    """Mocked AI provider that returns realistic responses."""
    async def generate_response(*args, **kwargs):
        return "标题: 测试标题\n\n这是测试内容正文。\n\n标签: #测试 #AI"
    return generate_response
