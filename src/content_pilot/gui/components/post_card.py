"""Reusable post card component."""

from __future__ import annotations

import json
from typing import Callable

from nicegui import ui


STATUS_COLORS = {
    "draft": "grey",
    "approved": "blue",
    "scheduled": "orange",
    "publishing": "amber",
    "published": "green",
    "failed": "red",
}


def post_card(
    post: dict,
    on_publish: Callable | None = None,
    on_delete: Callable | None = None,
) -> None:
    """Render a post card with title, content preview, status badge, and action buttons."""
    with ui.card().classes("q-pa-md").style("min-width: 300px; max-width: 500px;"):
        with ui.row().classes("items-center q-gutter-sm"):
            ui.label(post["platform"]).classes("text-weight-bold text-capitalize")
            color = STATUS_COLORS.get(post["status"], "grey")
            ui.badge(post["status"], color=color)
            ui.label(f"ID: {post['id']}").classes("text-caption text-grey")

        if post.get("title"):
            ui.label(post["title"]).classes("text-subtitle1 q-mt-xs")

        content_preview = (post.get("content") or "")[:150]
        if content_preview:
            ui.label(content_preview + ("..." if len(post.get("content", "")) > 150 else "")).classes(
                "text-body2 text-grey-7"
            )

        tags = []
        if post.get("tags"):
            try:
                tags = json.loads(post["tags"]) if isinstance(post["tags"], str) else post["tags"]
            except (json.JSONDecodeError, TypeError):
                pass
        if tags:
            with ui.row().classes("q-gutter-xs"):
                for tag in tags[:5]:
                    ui.badge(f"#{tag}", color="blue-grey").props("outline")

        if post.get("created_at"):
            ui.label(f"Created: {post['created_at']}").classes("text-caption text-grey q-mt-xs")

        with ui.row().classes("q-mt-sm q-gutter-sm"):
            if on_publish and post["status"] in ("approved", "draft"):
                ui.button("Publish", icon="publish", on_click=lambda: on_publish(post["id"])).props(
                    "color=primary dense"
                )
            if on_delete and post["status"] in ("draft", "failed"):
                ui.button("Delete", icon="delete", on_click=lambda: on_delete(post["id"])).props(
                    "color=negative dense outline"
                )
