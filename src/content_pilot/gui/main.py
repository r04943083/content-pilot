"""NiceGUI application entry point and App lifecycle management."""

from __future__ import annotations

import logging

from content_pilot.app import App

logger = logging.getLogger(__name__)

_pilot: App | None = None


def get_pilot() -> App:
    """Return the shared App instance. Raises if not started."""
    if _pilot is None:
        raise RuntimeError("App not started. GUI must be launched first.")
    return _pilot


async def _startup() -> None:
    global _pilot
    _pilot = App()
    await _pilot.startup()
    logger.info("Content Pilot app started")


async def _shutdown() -> None:
    global _pilot
    if _pilot:
        await _pilot.shutdown()
        _pilot = None
    logger.info("Content Pilot app stopped")


def launch_gui(host: str = "127.0.0.1", port: int = 8080) -> None:
    """Register pages and start NiceGUI."""
    from nicegui import app, ui

    from content_pilot.gui.pages import accounts, content, dashboard, publish, schedule, settings
    from content_pilot.utils.log import setup_logging

    setup_logging("INFO")

    app.on_startup(_startup)
    app.on_shutdown(_shutdown)

    # Register page routes
    dashboard.register()
    accounts.register()
    content.register()
    publish.register()
    schedule.register()
    settings.register()

    ui.run(
        host=host,
        port=port,
        title="Content Pilot",
        favicon="🚀",
        dark=True,
        reload=False,
        show=True,
    )
