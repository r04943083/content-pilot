"""Tests for GUI app lifecycle (get_pilot) and image helpers."""

from __future__ import annotations

import pytest

from content_pilot.gui.main import get_pilot, _startup, _shutdown
import content_pilot.gui.main as gui_main


class TestGetPilot:
    def test_get_pilot_before_startup_raises(self):
        """get_pilot() should raise if app hasn't been started."""
        gui_main._pilot = None
        with pytest.raises(RuntimeError, match="App not started"):
            get_pilot()

    @pytest.mark.asyncio
    async def test_startup_creates_pilot(self, tmp_path, monkeypatch):
        """After _startup(), get_pilot() returns an App instance."""
        # Patch settings to use a temp database
        from content_pilot.config.settings import Settings

        def mock_settings():
            s = Settings()
            s.database.path = str(tmp_path / "test.db")
            return s

        monkeypatch.setattr("content_pilot.config.get_settings", mock_settings)
        monkeypatch.setattr("content_pilot.app.get_settings", mock_settings)

        gui_main._pilot = None
        await _startup()
        try:
            pilot = get_pilot()
            assert pilot is not None
            assert pilot.db is not None
        finally:
            await _shutdown()

    @pytest.mark.asyncio
    async def test_shutdown_clears_pilot(self, tmp_path, monkeypatch):
        """After _shutdown(), get_pilot() raises again."""
        from content_pilot.config.settings import Settings

        def mock_settings():
            s = Settings()
            s.database.path = str(tmp_path / "test.db")
            return s

        monkeypatch.setattr("content_pilot.config.get_settings", mock_settings)
        monkeypatch.setattr("content_pilot.app.get_settings", mock_settings)

        gui_main._pilot = None
        await _startup()
        await _shutdown()
        with pytest.raises(RuntimeError, match="App not started"):
            get_pilot()


class TestImageHelpers:
    @pytest.mark.asyncio
    async def test_search_unsplash_returns_urls(self):
        from content_pilot.gui.components.image_picker import search_unsplash

        urls = await search_unsplash("nature", count=3)
        assert len(urls) == 3
        for url in urls:
            assert "unsplash" in url
            assert "nature" in url

    def test_get_images_dir(self, tmp_path, monkeypatch):
        from content_pilot.utils import files as files_mod
        from content_pilot.utils.files import get_images_dir

        test_dir = tmp_path / "data"
        from unittest.mock import MagicMock

        mock_settings = MagicMock()
        mock_settings.general.data_dir = str(test_dir)
        monkeypatch.setattr(files_mod, "get_settings", lambda: mock_settings)
        result = get_images_dir()
        assert result == (test_dir / "images").resolve()
        assert result.exists()

    @pytest.mark.asyncio
    async def test_download_image_bad_url(self, tmp_path, monkeypatch):
        from content_pilot.gui.components.image_picker import download_image
        from content_pilot.utils import files as files_mod
        from unittest.mock import MagicMock

        mock_settings = MagicMock()
        mock_settings.general.data_dir = str(tmp_path / "data")
        monkeypatch.setattr(files_mod, "get_settings", lambda: mock_settings)
        result = await download_image("http://invalid.test/no-image.jpg")
        assert result is None
