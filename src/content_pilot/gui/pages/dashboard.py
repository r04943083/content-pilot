"""Dashboard page: account status cards + recent posts table."""

from __future__ import annotations

import json
import logging

from nicegui import ui

from content_pilot.gui.components.nav import page_layout
from content_pilot.gui.main import get_pilot

logger = logging.getLogger(__name__)


def register() -> None:
    @ui.page("/")
    async def dashboard_page():
        page_layout("Dashboard")

        pilot = get_pilot()
        accounts = await pilot.db.get_all_accounts()
        posts = await pilot.db.get_posts(limit=20)

        # --- Account status cards ---
        ui.label("Accounts").classes("text-h6 q-mt-md q-mb-sm")
        if not accounts:
            ui.label("No accounts configured. Go to Accounts to login.").classes(
                "text-grey"
            )
        else:
            with ui.row().classes("q-gutter-md"):
                for acc in accounts:
                    with ui.card().classes("q-pa-md"):
                        with ui.row().classes("items-center gap-sm"):
                            color = "green" if acc["login_state"] == "active" else "red"
                            ui.badge(acc["login_state"], color=color)
                            ui.label(acc["platform"]).classes("text-weight-bold text-capitalize")
                        ui.label(acc["nickname"] or acc["username"]).classes("text-subtitle2")
                        ui.label(f"Followers: {acc['follower_count']}")

        # --- Recent posts ---
        ui.label("Recent Posts").classes("text-h6 q-mt-lg q-mb-sm")
        if not posts:
            ui.label("No posts yet. Go to Content to generate some.").classes(
                "text-grey"
            )
        else:
            columns = [
                {"name": "id", "label": "ID", "field": "id", "sortable": True},
                {"name": "platform", "label": "Platform", "field": "platform", "sortable": True},
                {"name": "title", "label": "Title", "field": "title"},
                {"name": "status", "label": "Status", "field": "status", "sortable": True},
                {"name": "created_at", "label": "Created", "field": "created_at", "sortable": True},
            ]
            rows = [
                {
                    "id": p["id"],
                    "platform": p["platform"],
                    "title": (p["title"] or "")[:60],
                    "status": p["status"],
                    "created_at": p["created_at"] or "",
                }
                for p in posts
            ]
            ui.table(columns=columns, rows=rows, row_key="id").classes("full-width")

        # Auto-refresh every 30 seconds
        ui.timer(30.0, lambda: ui.navigate.to("/"))
