"""Playwright browser lifecycle management with stealth injection."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from playwright.async_api import BrowserContext, Playwright, async_playwright

from content_pilot.config import get_settings

logger = logging.getLogger(__name__)

# Minimal stealth script to mask automation signals
_STEALTH_JS = """
// Remove webdriver flag
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
// Mock plugins
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5],
});
// Mock languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['zh-CN', 'zh', 'en-US', 'en'],
});
// Chrome runtime
window.chrome = { runtime: {} };
// Permissions
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
    Promise.resolve({ state: Notification.permission }) :
    originalQuery(parameters)
);
"""


class BrowserManager:
    """Manages Playwright browser instances with stealth and session persistence."""

    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser = None
        self._settings = get_settings()

    async def start(self) -> None:
        self._playwright = await async_playwright().start()

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    def _state_path(self, platform: str) -> Path:
        base = Path(self._settings.browser.user_data_dir)
        base.mkdir(parents=True, exist_ok=True)
        return base / f"{platform}_state.json"

    async def get_context(
        self, platform: str, headless: bool | None = None
    ) -> BrowserContext:
        """Get a browser context for the given platform, with session restore."""
        if self._playwright is None:
            await self.start()
        assert self._playwright is not None

        if headless is None:
            headless = self._settings.browser.headless

        if self._browser and self._browser.is_connected():
            await self._browser.close()

        self._browser = await self._playwright.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )

        state_path = self._state_path(platform)
        storage_state = str(state_path) if state_path.exists() else None
        logger.info(
            "Browser: headless=%s, session=%s",
            headless,
            state_path if storage_state else "none",
        )

        context = await self._browser.new_context(
            storage_state=storage_state,
            viewport={"width": 1280, "height": 800},
            locale="zh-CN",
            timezone_id=self._settings.general.timezone,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
        )

        if self._settings.browser.stealth:
            await context.add_init_script(_STEALTH_JS)

        return context

    async def save_session(self, context: BrowserContext, platform: str) -> None:
        """Persist browser session for future use."""
        state_path = self._state_path(platform)
        state = await context.storage_state()
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2))

    async def clear_session(self, platform: str) -> None:
        """Remove stored session."""
        state_path = self._state_path(platform)
        if state_path.exists():
            state_path.unlink()

    async def connect_cdp(self, endpoint: str) -> BrowserContext:
        """Connect to an existing Chrome DevTools Protocol endpoint."""
        if self._playwright is None:
            await self.start()
        assert self._playwright is not None
        browser = await self._playwright.chromium.connect_over_cdp(endpoint)
        contexts = browser.contexts
        if contexts:
            return contexts[0]
        return await browser.new_context()
