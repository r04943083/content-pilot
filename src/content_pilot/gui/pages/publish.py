"""Publish page: post list with publish/delete actions."""

from __future__ import annotations

import logging

from nicegui import ui

from content_pilot.gui.components.nav import page_layout
from content_pilot.gui.components.post_card import post_card
from content_pilot.gui.constants import PLATFORMS
from content_pilot.gui.main import get_pilot

logger = logging.getLogger(__name__)

STATUSES = ["all", "draft", "approved", "published", "failed"]


def register() -> None:
    @ui.page("/publish")
    async def publish_page():
        page_layout("Publish")

        pilot = get_pilot()

        with ui.column().classes(
            "full-width q-pa-md"
        ).style("max-width: 1200px; margin: auto;"):
            # Filter controls
            ui.label("Post Management").classes("text-h6 q-mb-sm")

            with ui.row().classes("q-gutter-md items-center"):
                filter_platform = ui.select(
                    ["all"] + PLATFORMS, value="all", label="Platform"
                ).style("min-width: 150px;").props("outlined dense")
                filter_status = ui.select(
                    STATUSES, value="all", label="Status"
                ).style("min-width: 150px;").props("outlined dense")

            posts_container = ui.column().classes("full-width q-mt-md")

            async def refresh_posts():
                platform = (
                    filter_platform.value
                    if filter_platform.value != "all"
                    else None
                )
                status = (
                    filter_status.value
                    if filter_status.value != "all"
                    else None
                )
                posts = await pilot.db.get_posts(
                    platform=platform, status=status, limit=50
                )
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
                ui.notify(
                    f"Publishing post {post_id}...", type="info"
                )
                try:
                    ok = await pilot.publish(post_id)
                    if ok:
                        ui.notify(
                            f"Post {post_id} published!",
                            type="positive",
                        )
                    else:
                        ui.notify(
                            f"Publish failed for post {post_id}",
                            type="negative",
                        )
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")
                await refresh_posts()

            async def do_delete(post_id: int):
                async def confirm_delete():
                    await pilot.db.delete_post(post_id)
                    ui.notify(f"Post {post_id} deleted", type="info")
                    dialog.close()
                    await refresh_posts()

                with ui.dialog() as dialog, ui.card():
                    ui.label(
                        f"Are you sure you want to delete post {post_id}?"
                    )
                    with ui.row().classes("q-gutter-sm q-mt-sm"):
                        ui.button(
                            "Yes, delete", on_click=confirm_delete
                        ).props("color=negative")
                        ui.button(
                            "Cancel", on_click=dialog.close
                        ).props("outline")
                dialog.open()

            filter_platform.on_value_change(
                lambda _: refresh_posts()  # noqa: ASYNC101 — NiceGUI handles the coroutine
            )
            filter_status.on_value_change(
                lambda _: refresh_posts()  # noqa: ASYNC101
            )

            await refresh_posts()
