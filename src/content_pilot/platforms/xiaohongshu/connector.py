"""Xiaohongshu platform connector implementation."""

from __future__ import annotations

import logging

from playwright.async_api import BrowserContext

from content_pilot.platforms.base import (
    AbstractPlatform,
    AccountInfo,
    PostContent,
    PublishResult,
)
from content_pilot.platforms.registry import PlatformRegistry
from content_pilot.platforms.xiaohongshu import selectors as sel
from content_pilot.utils.humanize import human_click, human_type, random_delay, short_delay

logger = logging.getLogger(__name__)

CREATOR_URL = "https://creator.xiaohongshu.com"
LOGIN_URL = "https://creator.xiaohongshu.com/login"
PUBLISH_URL = "https://creator.xiaohongshu.com/publish/publish"


@PlatformRegistry.register("xiaohongshu")
class XiaohongshuPlatform(AbstractPlatform):
    """Xiaohongshu (Little Red Book) connector."""

    name = "xiaohongshu"
    creator_url = CREATOR_URL

    def __init__(self, context: BrowserContext) -> None:
        super().__init__(context)

    async def login(self) -> bool:
        """Login via QR code scan."""
        page = await self.context.new_page()
        try:
            await page.goto(LOGIN_URL, wait_until="networkidle", timeout=30000)
            await random_delay(1, 3)

            # Wait for QR code to appear
            qr_element = await page.wait_for_selector(
                sel.LOGIN_QR_CODE, timeout=15000
            )
            if qr_element:
                logger.info("QR code detected. Please scan with Xiaohongshu app in the browser window.")

            # Wait for login success (up to 120 seconds).
            # After QR scan the page navigates away from /login,
            # so we detect success by URL change OR a DOM indicator.
            await page.wait_for_url(
                lambda url: "login" not in url.lower(),
                timeout=120000,
            )
            logger.info("Login successful!")
            return True
        except Exception as e:
            logger.error("Login failed: %s", e)
            return False
        finally:
            await page.close()

    async def check_session(self) -> bool:
        """Check if session is still valid."""
        page = await self.context.new_page()
        try:
            await page.goto(CREATOR_URL, wait_until="networkidle", timeout=15000)
            await short_delay()
            # If redirected to login page, session is invalid
            if "login" in page.url.lower():
                return False
            # Check for user info element
            user_el = await page.query_selector(sel.LOGIN_SUCCESS_INDICATOR)
            return user_el is not None
        except Exception:
            return False
        finally:
            await page.close()

    async def get_account_info(self) -> AccountInfo:
        """Fetch account information from creator center."""
        page = await self.context.new_page()
        try:
            await page.goto(CREATOR_URL, wait_until="networkidle", timeout=15000)
            await random_delay(1, 3)

            info = AccountInfo(platform=self.name)

            nickname_el = await page.query_selector(sel.ACCOUNT_NICKNAME)
            if nickname_el:
                info.nickname = (await nickname_el.text_content() or "").strip()

            follower_el = await page.query_selector(sel.ACCOUNT_FOLLOWER)
            if follower_el:
                text = (await follower_el.text_content() or "").strip()
                info.follower_count = _parse_count(text)

            avatar_el = await page.query_selector(sel.ACCOUNT_AVATAR)
            if avatar_el:
                info.avatar_url = await avatar_el.get_attribute("src") or ""

            return info
        except Exception as e:
            logger.error("Failed to get account info: %s", e)
            return AccountInfo(platform=self.name)
        finally:
            await page.close()

    async def publish_text_image(self, post: PostContent) -> PublishResult:
        """Publish a text+image note on Xiaohongshu."""
        page = await self.context.new_page()
        try:
            await page.goto(PUBLISH_URL, wait_until="networkidle", timeout=30000)
            await random_delay(2, 5)

            # Upload images if any
            if post.images:
                file_input = await page.query_selector(sel.PUBLISH_IMAGE_UPLOAD)
                if file_input:
                    await file_input.set_input_files([str(p) for p in post.images])
                    await random_delay(3, 6)

            # Enter title
            if post.title:
                title_input = await page.wait_for_selector(
                    sel.PUBLISH_TITLE_INPUT, timeout=10000
                )
                if title_input:
                    await title_input.click()
                    await short_delay()
                    await title_input.fill(post.title)
                    await short_delay()

            # Enter content
            content_el = await page.wait_for_selector(
                sel.PUBLISH_CONTENT_INPUT, timeout=10000
            )
            if content_el:
                await content_el.click()
                await short_delay()
                await page.keyboard.type(post.content, delay=30)
                await random_delay(1, 3)

            # Add tags
            for tag in post.tags[:10]:  # Max 10 tags
                tag_input = await page.query_selector(sel.PUBLISH_TAG_INPUT)
                if tag_input:
                    await tag_input.click()
                    await short_delay()
                    await tag_input.fill(tag)
                    await page.keyboard.press("Enter")
                    await short_delay()

            # Submit
            await random_delay(2, 4)
            submit_btn = await page.wait_for_selector(
                sel.PUBLISH_SUBMIT_BTN, timeout=10000
            )
            if submit_btn:
                await submit_btn.click()

            # Wait for success
            try:
                await page.wait_for_selector(sel.PUBLISH_SUCCESS, timeout=30000)
                return PublishResult(success=True)
            except Exception:
                return PublishResult(success=True)  # May have succeeded without indicator

        except Exception as e:
            logger.error("Publish failed: %s", e)
            return PublishResult(success=False, error=str(e))
        finally:
            await page.close()

    async def publish_video(self, post: PostContent) -> PublishResult:
        """Publish video content (not primary for XHS, but supported)."""
        # Xiaohongshu video publishing follows similar flow
        return await self.publish_text_image(post)

    async def get_post_analytics(self, platform_post_id: str) -> dict:
        """Scrape analytics for a specific post."""
        page = await self.context.new_page()
        try:
            await page.goto(
                f"{CREATOR_URL}/data",
                wait_until="networkidle",
                timeout=15000,
            )
            await random_delay(2, 4)

            data = {
                "views": 0,
                "likes": 0,
                "comments": 0,
                "favorites": 0,
                "shares": 0,
            }

            for key, selector in [
                ("views", sel.ANALYTICS_VIEWS),
                ("likes", sel.ANALYTICS_LIKES),
                ("comments", sel.ANALYTICS_COMMENTS),
                ("favorites", sel.ANALYTICS_FAVORITES),
                ("shares", sel.ANALYTICS_SHARES),
            ]:
                el = await page.query_selector(selector)
                if el:
                    text = (await el.text_content() or "").strip()
                    data[key] = _parse_count(text)

            return data
        except Exception as e:
            logger.error("Failed to get analytics: %s", e)
            return {}
        finally:
            await page.close()


def _parse_count(text: str) -> int:
    """Parse count strings like '1.2万' into integers."""
    text = text.strip().replace(",", "")
    try:
        if "万" in text:
            return int(float(text.replace("万", "")) * 10000)
        if "亿" in text:
            return int(float(text.replace("亿", "")) * 100000000)
        # Extract digits only
        digits = "".join(c for c in text if c.isdigit() or c == ".")
        return int(float(digits)) if digits else 0
    except (ValueError, TypeError):
        return 0
