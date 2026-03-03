"""Publish page: post list with publish/delete actions."""

from __future__ import annotations

import logging

from nicegui import ui

from content_pilot.gui.components.nav import page_layout
from content_pilot.gui.components.post_card import post_card
from content_pilot.gui.main import get_pilot

logger = logging.getLogger(__name__)

PLATFORMS = ["xiaohongshu", "douyin", "bilibili", "weibo"]
STATUSES = ["all", "draft", "approved", "published", "failed"]


def register() -> None:
    @ui.page("/publish")
    async def publish_page():
        page_layout("Publish")

        pilot = get_pilot()

        # Filter controls
        ui.label("Post Management").classes("text-h6 q-mt-md q-mb-sm")

        filter_platform = ui.select(
            ["all"] + PLATFORMS, value="all", label="Platform"
        ).classes("q-mr-md").style("min-width: 150px;")
        filter_status = ui.select(
            STATUSES, value="all", label="Status"
        ).style("min-width: 150px;")

        posts_container = ui.column().classes("full-width q-mt-md")

        async def refresh_posts():
            platform = filter_platform.value if filter_platform.value != "all" else None
            status = filter_status.value if filter_status.value != "all" else None
            posts = await pilot.db.get_posts(platform=platform, status=status, limit=50)
            posts_container.clear()
            with posts_container:
                if not posts:
                    ui.label("No posts found.").classes("text-grey")
                    return
                with ui.row().classes("q-gutter-md flex-wrap"):
                    for p in posts:
                        post_card(
                            p,
                            on_publish=do_publish,
                            on_delete=do_delete,
                        )

        async def do_publish(post_id: int):
            ui.notify(f"Publishing post {post_id}...", type="info")
            try:
                ok = await pilot.publish(post_id)
                if ok:
                    ui.notify(f"Post {post_id} published!", type="positive")
                else:
                    ui.notify(f"Publish failed for post {post_id}", type="negative")
            except Exception as e:
                ui.notify(f"Error: {e}", type="negative")
            await refresh_posts()

        async def do_delete(post_id: int):
            await pilot.db.delete_post(post_id)
            ui.notify(f"Post {post_id} deleted", type="info")
            await refresh_posts()

        filter_platform.on_value_change(lambda _: refresh_posts())
        filter_status.on_value_change(lambda _: refresh_posts())

        await refresh_posts()
