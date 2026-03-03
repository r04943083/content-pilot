"""Reusable post card component."""

from __future__ import annotations

import json
from typing import Callable

from nicegui import ui

from content_pilot.gui.components.image_lightbox import clickable_image
from content_pilot.gui.constants import PLATFORM_COLORS, PLATFORM_ICONS, STATUS_COLORS, COLORS
from content_pilot.gui.i18n import t


def post_card(
    post: dict,
    on_publish: Callable | None = None,
    on_delete: Callable | None = None,
) -> None:
    """Render a post card with title, content preview, status badge, and action buttons."""
    platform = post["platform"]
    p_color = PLATFORM_COLORS.get(platform, "#666")

    with ui.card().classes("q-pa-md").style(
        f"flex: 1 1 280px; min-width: 280px; max-width: 100%; background: {COLORS['surface']}; "
        f"border-left: 4px solid {p_color}; border-radius: 8px;"
    ):
        # Thumbnail area
        images = json.loads(post.get("images", "[]"))
        if images:
            clickable_image(images[0], classes="q-mb-sm", style="width: 100%; height: 180px; object-fit: cover; border-radius: 6px;")
        else:
            # Placeholder for posts without images
            with ui.row().classes(
                "q-mb-sm items-center justify-center"
            ).style(
                f"width: 100%; height: 120px; background: {COLORS['background']}; border-radius: 6px;"
            ):
                ui.icon("article", size="lg").style(f"color: {COLORS['text_secondary']}")

        # Header row with platform and status
        with ui.row().classes("items-center q-gutter-sm"):
            icon = PLATFORM_ICONS.get(platform, "article")
            ui.icon(icon, size="xs").style(f"color: {p_color};")
            ui.label(platform.capitalize()).classes(
                "text-weight-bold text-caption"
            ).style(f"color: {COLORS['text_primary']};")
            color = STATUS_COLORS.get(post["status"], "grey")
            ui.badge(t(f"status.{post['status']}"), color=color).props("outline")

        # Title
        if post.get("title"):
            title = post["title"]
            if len(title) > 60:
                title = title[:60] + "..."
            ui.label(title).classes("text-subtitle1 q-mt-xs").style(
                f"color: {COLORS['text_primary']};"
            )

        # Content preview
        content_preview = (post.get("content") or "")[:120]
        if content_preview:
            ui.label(
                content_preview
                + (
                    "..."
                    if len(post.get("content", "")) > 120
                    else ""
                )
            ).classes("text-body2 text-grey-7 q-mt-xs").style(
                f"color: {COLORS['text_secondary']};"
            )

        # Tags
        tags = []
        if post.get("tags"):
            try:
                tags = (
                    json.loads(post["tags"])
                    if isinstance(post["tags"], str)
                    else post["tags"]
                )
            except (json.JSONDecodeError, TypeError):
                pass
        if tags:
            with ui.row().classes("q-gutter-xs q-mt-sm"):
                for tag in tags[:3]:
                    ui.badge(f"#{tag}", color="blue-grey").props(
                        "outline"
                    )

        # Created at
        if post.get("created_at"):
            ui.label(f"Created: {post['created_at']}").classes(
                "text-caption text-grey q-mt-sm"
            ).style(f"color: {COLORS['text_secondary']};")

        # Action buttons
        with ui.row().classes("q-mt-sm q-gutter-sm"):
            if on_publish and post["status"] in ("approved", "draft"):
                ui.button(
                    t("publish.publish"),
                    icon="publish",
                    on_click=lambda _, pid=post["id"]: on_publish(pid),
                ).props(f"color={COLORS['primary']} dense")
            if on_delete and post["status"] in ("draft", "approved", "failed"):
                ui.button(
                    t("common.delete"),
                    icon="delete",
                    on_click=lambda _, pid=post["id"]: on_delete(pid),
                ).props(f"color={COLORS['warning']} dense outline")
