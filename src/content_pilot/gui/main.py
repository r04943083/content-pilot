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


_GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

body, .nicegui-content {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

.q-card {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    border: 1px solid rgba(255,255,255,0.06);
}

.q-card:hover {
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}

/* Scrollbar styling */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.15);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(255,255,255,0.25);
}

/* Smooth transitions for interactive elements */
.q-btn, .q-input, .q-select, a {
    transition: all 0.2s ease;
}
</style>
"""


def launch_gui(host: str = "127.0.0.1", port: int = 8080) -> None:
    """Register pages and start NiceGUI."""
    from nicegui import app, ui

    from content_pilot.gui.pages import accounts, content, dashboard, publish, schedule, settings
    from content_pilot.utils.log import setup_logging

    setup_logging("INFO")

    app.on_startup(_startup)
    app.on_shutdown(_shutdown)

    # Add global CSS
    ui.add_head_html(_GLOBAL_CSS)

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
