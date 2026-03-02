"""Douyin platform connector implementation."""

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
from content_pilot.platforms.douyin import selectors as sel
from content_pilot.utils.humanize import random_delay, short_delay

logger = logging.getLogger(__name__)

CREATOR_URL = "https://creator.douyin.com"
LOGIN_URL = "https://creator.douyin.com/login"
PUBLISH_URL = "https://creator.douyin.com/creator-micro/content/upload"


@PlatformRegistry.register("douyin")
class DouyinPlatform(AbstractPlatform):
    """Douyin creator center connector."""

    name = "douyin"
    creator_url = CREATOR_URL

    def __init__(self, context: BrowserContext) -> None:
        super().__init__(context)

    async def login(self) -> bool:
        page = await self.context.new_page()
        try:
            await page.goto(LOGIN_URL, wait_until="networkidle", timeout=30000)
            await random_delay(1, 3)

            qr_element = await page.wait_for_selector(sel.LOGIN_QR_CODE, timeout=15000)
            if qr_element:
                logger.info("QR code detected. Please scan with Douyin app.")
                qr_src = await qr_element.get_attribute("src")
                if qr_src:
                    from content_pilot.utils.qr import display_qr_in_terminal
                    try:
                        display_qr_in_terminal(qr_src)
                    except Exception:
                        pass

            await page.wait_for_selector(sel.LOGIN_SUCCESS_INDICATOR, timeout=120000)
            logger.info("Douyin login successful!")
            return True
        except Exception as e:
            logger.error("Douyin login failed: %s", e)
            return False
        finally:
            await page.close()

    async def check_session(self) -> bool:
        page = await self.context.new_page()
        try:
            await page.goto(CREATOR_URL, wait_until="networkidle", timeout=15000)
            if "login" in page.url.lower():
                return False
            user_el = await page.query_selector(sel.LOGIN_SUCCESS_INDICATOR)
            return user_el is not None
        except Exception:
            return False
        finally:
            await page.close()

    async def get_account_info(self) -> AccountInfo:
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

            return info
        except Exception as e:
            logger.error("Failed to get Douyin account info: %s", e)
            return AccountInfo(platform=self.name)
        finally:
            await page.close()

    async def publish_text_image(self, post: PostContent) -> PublishResult:
        """Douyin primarily supports video; image posts go through photo mode."""
        page = await self.context.new_page()
        try:
            await page.goto(PUBLISH_URL, wait_until="networkidle", timeout=30000)
            await random_delay(2, 5)

            # Upload images
            if post.images:
                file_input = await page.query_selector(sel.PUBLISH_IMAGE_UPLOAD)
                if file_input:
                    await file_input.set_input_files([str(p) for p in post.images])
                    await random_delay(3, 6)

            # Title
            if post.title:
                title_input = await page.wait_for_selector(
                    sel.PUBLISH_TITLE_INPUT, timeout=10000
                )
                if title_input:
                    await title_input.fill(post.title)
                    await short_delay()

            # Description
            desc_el = await page.wait_for_selector(sel.PUBLISH_DESC_INPUT, timeout=10000)
            if desc_el:
                await desc_el.click()
                await page.keyboard.type(post.content, delay=30)
                await random_delay(1, 3)

            # Tags
            for tag in post.tags[:5]:
                tag_input = await page.query_selector(sel.PUBLISH_TAG_INPUT)
                if tag_input:
                    await tag_input.fill(f"#{tag}")
                    await page.keyboard.press("Enter")
                    await short_delay()

            # Submit
            await random_delay(2, 4)
            submit_btn = await page.wait_for_selector(sel.PUBLISH_SUBMIT_BTN, timeout=10000)
            if submit_btn:
                await submit_btn.click()

            try:
                await page.wait_for_selector(sel.PUBLISH_SUCCESS, timeout=30000)
            except Exception:
                pass
            return PublishResult(success=True)

        except Exception as e:
            logger.error("Douyin publish failed: %s", e)
            return PublishResult(success=False, error=str(e))
        finally:
            await page.close()

    async def publish_video(self, post: PostContent) -> PublishResult:
        """Publish a video on Douyin."""
        page = await self.context.new_page()
        try:
            await page.goto(PUBLISH_URL, wait_until="networkidle", timeout=30000)
            await random_delay(2, 5)

            # Upload video
            if post.video_path:
                file_input = await page.query_selector(sel.PUBLISH_VIDEO_UPLOAD)
                if file_input:
                    await file_input.set_input_files(str(post.video_path))
                    await random_delay(5, 15)  # Video upload takes longer

            # Title
            if post.title:
                title_input = await page.wait_for_selector(
                    sel.PUBLISH_TITLE_INPUT, timeout=10000
                )
                if title_input:
                    await title_input.fill(post.title)
                    await short_delay()

            # Description
            desc_el = await page.wait_for_selector(sel.PUBLISH_DESC_INPUT, timeout=10000)
            if desc_el:
                await desc_el.click()
                await page.keyboard.type(post.content, delay=30)

            # Tags
            for tag in post.tags[:5]:
                tag_input = await page.query_selector(sel.PUBLISH_TAG_INPUT)
                if tag_input:
                    await tag_input.fill(f"#{tag}")
                    await page.keyboard.press("Enter")
                    await short_delay()

            # Submit
            await random_delay(2, 4)
            submit_btn = await page.wait_for_selector(sel.PUBLISH_SUBMIT_BTN, timeout=10000)
            if submit_btn:
                await submit_btn.click()

            try:
                await page.wait_for_selector(sel.PUBLISH_SUCCESS, timeout=60000)
            except Exception:
                pass
            return PublishResult(success=True)

        except Exception as e:
            logger.error("Douyin video publish failed: %s", e)
            return PublishResult(success=False, error=str(e))
        finally:
            await page.close()

    async def get_post_analytics(self, platform_post_id: str) -> dict:
        page = await self.context.new_page()
        try:
            await page.goto(
                f"{CREATOR_URL}/creator-micro/data/stats",
                wait_until="networkidle",
                timeout=15000,
            )
            await random_delay(2, 4)
            data = {"views": 0, "likes": 0, "comments": 0, "shares": 0}

            for key, selector in [
                ("views", sel.ANALYTICS_VIEWS),
                ("likes", sel.ANALYTICS_LIKES),
                ("comments", sel.ANALYTICS_COMMENTS),
                ("shares", sel.ANALYTICS_SHARES),
            ]:
                el = await page.query_selector(selector)
                if el:
                    text = (await el.text_content() or "").strip()
                    data[key] = _parse_count(text)
            return data
        except Exception as e:
            logger.error("Failed to get Douyin analytics: %s", e)
            return {}
        finally:
            await page.close()


def _parse_count(text: str) -> int:
    text = text.strip().replace(",", "")
    try:
        if "万" in text:
            return int(float(text.replace("万", "")) * 10000)
        if "亿" in text:
            return int(float(text.replace("亿", "")) * 100000000)
        digits = "".join(c for c in text if c.isdigit() or c == ".")
        return int(float(digits)) if digits else 0
    except (ValueError, TypeError):
        return 0
