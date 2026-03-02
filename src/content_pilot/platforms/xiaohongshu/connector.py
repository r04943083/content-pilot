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
            await page.goto(
                CREATOR_URL, wait_until="domcontentloaded", timeout=30000
            )
            # Wait for SPA redirect to settle (to /login or /new/home)
            try:
                await page.wait_for_url(
                    lambda url: "login" in url or "/new/" in url,
                    timeout=10000,
                )
            except Exception:
                pass  # URL might already be at the right place
            logger.info("Session check URL: %s", page.url)
            return "login" not in page.url.lower()
        except Exception as e:
            logger.error("Session check failed: %s", e)
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

    async def _create_placeholder_image(self) -> str:
        """Create a simple placeholder image when no images are provided."""
        from PIL import Image as PILImage

        path = "/tmp/content_pilot_placeholder.png"
        img = PILImage.new("RGB", (1080, 1080), color=(245, 245, 245))
        img.save(path)
        return path

    async def publish_text_image(self, post: PostContent) -> PublishResult:
        """Publish a text+image note on Xiaohongshu.

        XHS requires at least one image for a 图文笔记. The flow is:
        1. Navigate to publish page
        2. Click "上传图文" tab (default is video)
        3. Upload image(s) via file input
        4. Fill title, content, tags in the editor that appears
        5. Click "发布"
        """
        page = await self.context.new_page()
        try:
            await page.goto(
                PUBLISH_URL, wait_until="domcontentloaded", timeout=60000
            )
            await random_delay(3, 6)

            # Step 1: Click "上传图文" tab
            tabs = await page.query_selector_all(sel.PUBLISH_TAB_IMAGE)
            for tab in tabs:
                text = (await tab.text_content() or "").strip()
                if "图文" in text:
                    await tab.evaluate("e => e.click()")
                    break
            await random_delay(2, 4)

            # Step 2: Upload images (XHS requires at least one)
            image_paths: list[str] = []
            if post.images:
                image_paths = [str(p) for p in post.images]
            else:
                # Create a placeholder — XHS won't let you proceed without an image
                placeholder = await self._create_placeholder_image()
                image_paths = [placeholder]
                logger.info("No images provided, using placeholder image")

            file_input = await page.query_selector(sel.PUBLISH_IMAGE_UPLOAD)
            if file_input:
                await file_input.set_input_files(image_paths)
                await random_delay(4, 8)
            else:
                return PublishResult(
                    success=False, error="Image upload input not found"
                )

            # Step 3: Fill title (editor appears after image upload)
            if post.title:
                await page.wait_for_selector(
                    sel.PUBLISH_TITLE_INPUT, timeout=15000
                )
                await human_click(page, sel.PUBLISH_TITLE_INPUT)
                await short_delay()
                await page.fill(sel.PUBLISH_TITLE_INPUT, post.title[:20])  # XHS title max ~20 chars
                await short_delay()

            # Step 4: Fill content
            await page.wait_for_selector(
                sel.PUBLISH_CONTENT_INPUT, timeout=10000
            )
            await human_click(page, sel.PUBLISH_CONTENT_INPUT)
            await short_delay()
            await human_type(page, sel.PUBLISH_CONTENT_INPUT, post.content)
            await random_delay(1, 3)

            # Step 5: Add topic tags via # in content area
            for tag in post.tags[:5]:
                await page.keyboard.type(f" #{tag}", delay=50)
                await short_delay()

            # Step 6: Submit
            await random_delay(2, 4)
            await page.wait_for_selector(
                sel.PUBLISH_SUBMIT_BTN, timeout=10000
            )
            await human_click(page, sel.PUBLISH_SUBMIT_BTN)

            # Wait for navigation or success indicator
            try:
                await page.wait_for_url(
                    lambda url: "publish" not in url.lower(),
                    timeout=30000,
                )
                return PublishResult(success=True)
            except Exception:
                # May have succeeded without URL change
                return PublishResult(success=True)

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
