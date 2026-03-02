"""Human-like delays and input simulation."""

from __future__ import annotations

import asyncio
import random

from playwright.async_api import Page


async def random_delay(min_sec: float = 2.0, max_sec: float = 8.0) -> None:
    """Wait a random duration to mimic human behavior."""
    await asyncio.sleep(random.uniform(min_sec, max_sec))


async def short_delay() -> None:
    """Brief pause between actions."""
    await asyncio.sleep(random.uniform(0.5, 1.5))


async def human_type(page: Page, selector: str, text: str) -> None:
    """Type text with human-like speed variation."""
    await page.click(selector)
    await short_delay()
    for char in text:
        await page.keyboard.type(char, delay=random.randint(50, 150))
        if random.random() < 0.05:  # Occasional longer pause
            await asyncio.sleep(random.uniform(0.3, 0.8))


async def human_click(page: Page, selector: str) -> None:
    """Click with a small random offset."""
    element = await page.query_selector(selector)
    if element:
        box = await element.bounding_box()
        if box:
            x = box["x"] + box["width"] * random.uniform(0.3, 0.7)
            y = box["y"] + box["height"] * random.uniform(0.3, 0.7)
            await page.mouse.click(x, y)
            await short_delay()
            return
    await page.click(selector)
    await short_delay()
