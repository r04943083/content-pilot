"""Tests for browser manager."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content_pilot.browser.manager import BrowserManager, _STEALTH_JS


@pytest.fixture
def mock_settings(tmp_path):
    from content_pilot.config.settings import Settings

    s = Settings()
    s.browser.user_data_dir = str(tmp_path / "browser_contexts")
    s.browser.headless = True
    s.browser.stealth = True
    s.general.timezone = "Asia/Shanghai"
    return s


@pytest.fixture
def manager(mock_settings, monkeypatch):
    monkeypatch.setattr("content_pilot.browser.manager.get_settings", lambda: mock_settings)
    return BrowserManager()


class TestStatePath:
    def test_state_path_creates_dir(self, manager, tmp_path):
        path = manager._state_path("xiaohongshu")
        assert path.name == "xiaohongshu_state.json"
        assert path.parent.exists()

    def test_state_path_per_platform(self, manager):
        p1 = manager._state_path("xiaohongshu")
        p2 = manager._state_path("douyin")
        assert p1 != p2
        assert "xiaohongshu" in p1.name
        assert "douyin" in p2.name


class TestBrowserLifecycle:
    @pytest.mark.asyncio
    async def test_start_initializes_playwright(self, manager):
        with patch("content_pilot.browser.manager.async_playwright") as mock_pw:
            mock_instance = AsyncMock()
            mock_pw.return_value.start = AsyncMock(return_value=mock_instance)
            await manager.start()
            assert manager._playwright is not None

    @pytest.mark.asyncio
    async def test_stop_cleans_up(self, manager):
        mock_browser = AsyncMock()
        mock_pw = AsyncMock()
        manager._browser = mock_browser
        manager._playwright = mock_pw

        await manager.stop()

        mock_browser.close.assert_awaited_once()
        mock_pw.stop.assert_awaited_once()
        assert manager._browser is None
        assert manager._playwright is None

    @pytest.mark.asyncio
    async def test_stop_when_not_started(self, manager):
        """Stop should not error when nothing was started."""
        await manager.stop()
        assert manager._browser is None
        assert manager._playwright is None


class TestGetContext:
    @pytest.mark.asyncio
    async def test_get_context_auto_starts(self, manager):
        """get_context starts playwright if not already started."""
        mock_pw = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.is_connected.return_value = False
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_context = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        with patch("content_pilot.browser.manager.async_playwright") as mock_apw:
            mock_apw.return_value.start = AsyncMock(return_value=mock_pw)
            ctx = await manager.get_context("xiaohongshu")

        assert ctx is not None

    @pytest.mark.asyncio
    async def test_get_context_headless_override(self, manager, mock_settings):
        """Explicit headless=False overrides settings."""
        mock_pw = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.is_connected.return_value = False
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_context = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        manager._playwright = mock_pw

        await manager.get_context("xiaohongshu", headless=False)
        call_kwargs = mock_pw.chromium.launch.call_args
        assert call_kwargs.kwargs.get("headless") is False or call_kwargs[1].get("headless") is False

    @pytest.mark.asyncio
    async def test_stealth_injection(self, manager, mock_settings):
        """Stealth JS should be injected when stealth=True."""
        mock_settings.browser.stealth = True
        mock_pw = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.is_connected.return_value = False
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_context = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        manager._playwright = mock_pw

        await manager.get_context("xiaohongshu")
        mock_context.add_init_script.assert_awaited_once_with(_STEALTH_JS)

    @pytest.mark.asyncio
    async def test_no_stealth_when_disabled(self, manager, mock_settings):
        """Stealth JS should NOT be injected when stealth=False."""
        mock_settings.browser.stealth = False
        mock_pw = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.is_connected.return_value = False
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_context = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        manager._playwright = mock_pw

        await manager.get_context("xiaohongshu")
        mock_context.add_init_script.assert_not_awaited()


class TestSessionPersistence:
    @pytest.mark.asyncio
    async def test_save_session(self, manager, tmp_path):
        """save_session writes storage state to disk."""
        mock_context = AsyncMock()
        state_data = {"cookies": [{"name": "test"}], "origins": []}
        mock_context.storage_state = AsyncMock(return_value=state_data)

        await manager.save_session(mock_context, "xiaohongshu")

        state_path = manager._state_path("xiaohongshu")
        assert state_path.exists()
        loaded = json.loads(state_path.read_text())
        assert loaded["cookies"][0]["name"] == "test"

    @pytest.mark.asyncio
    async def test_clear_session(self, manager):
        """clear_session removes the state file."""
        state_path = manager._state_path("xiaohongshu")
        state_path.write_text("{}")
        assert state_path.exists()

        await manager.clear_session("xiaohongshu")
        assert not state_path.exists()

    @pytest.mark.asyncio
    async def test_clear_session_no_file(self, manager):
        """clear_session should not error when no file exists."""
        await manager.clear_session("xiaohongshu")  # Should not raise

    @pytest.mark.asyncio
    async def test_session_restore_on_get_context(self, manager, mock_settings):
        """get_context passes storage_state when session file exists."""
        state_path = manager._state_path("xiaohongshu")
        state_path.write_text(json.dumps({"cookies": [], "origins": []}))

        mock_pw = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.is_connected.return_value = False
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_context = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        manager._playwright = mock_pw

        await manager.get_context("xiaohongshu")
        call_kwargs = mock_browser.new_context.call_args
        assert call_kwargs.kwargs.get("storage_state") == str(state_path)


class TestBrowserReuse:
    @pytest.mark.asyncio
    async def test_reuses_browser_same_headless_mode(self, manager):
        """Browser is reused when headless mode matches."""
        old_browser = MagicMock()
        old_browser.is_connected.return_value = True
        old_browser.new_context = AsyncMock(return_value=AsyncMock())
        manager._browser = old_browser
        manager._browser_headless = True  # matches default

        mock_pw = AsyncMock()
        manager._playwright = mock_pw

        await manager.get_context("xiaohongshu")
        # Should NOT have launched a new browser
        mock_pw.chromium.launch.assert_not_awaited()
        # Should NOT have closed the old browser
        old_browser.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_closes_browser_when_headless_mode_changes(self, manager):
        """Browser is closed and relaunched when headless mode changes."""
        old_browser = MagicMock()
        old_browser.is_connected.return_value = True
        old_browser.close = AsyncMock()
        manager._browser = old_browser
        manager._browser_headless = True  # currently headless

        mock_pw = AsyncMock()
        new_browser = MagicMock()
        new_browser.is_connected.return_value = True
        new_browser.new_context = AsyncMock(return_value=AsyncMock())
        mock_pw.chromium.launch = AsyncMock(return_value=new_browser)
        manager._playwright = mock_pw

        # Request non-headless → mode change → should relaunch
        await manager.get_context("xiaohongshu", headless=False)
        old_browser.close.assert_awaited_once()
        mock_pw.chromium.launch.assert_awaited_once()
