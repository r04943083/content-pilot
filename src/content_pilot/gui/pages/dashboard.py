"""Dashboard page: account status cards + recent posts table."""

from __future__ import annotations

import logging

from nicegui import ui

from content_pilot.gui.components.nav import page_layout
from content_pilot.gui.constants import PLATFORM_COLORS, PLATFORM_ICONS, STATUS_COLORS
from content_pilot.gui.main import get_pilot

logger = logging.getLogger(__name__)


def register() -> None:
    @ui.page("/")
    async def dashboard_page():
        page_layout("Dashboard")

        with ui.column().classes(
            "full-width q-pa-md"
        ).style("max-width: 1200px; margin: auto;"):

            @ui.refreshable
            async def data_section():
                pilot = get_pilot()
                accounts = await pilot.db.get_all_accounts()
                posts = await pilot.db.get_posts(limit=20)

                # --- Account status cards ---
                ui.label("Accounts").classes("text-h6 q-mb-sm")
                if not accounts:
                    ui.label(
                        "No accounts configured. Go to Accounts to login."
                    ).classes("text-grey")
                else:
                    with ui.row().classes("q-gutter-md flex-wrap"):
                        for acc in accounts:
                            platform = acc["platform"]
                            icon = PLATFORM_ICONS.get(platform, "person")
                            p_color = PLATFORM_COLORS.get(platform, "#666")
                            with ui.card().classes("q-pa-md").style(
                                f"min-width: 260px; border-top: 3px solid {p_color};"
                            ):
                                with ui.row().classes("items-center q-gutter-sm"):
                                    ui.icon(icon).style(f"color: {p_color};")
                                    ui.label(platform).classes(
                                        "text-weight-bold text-capitalize"
                                    )
                                    color = (
                                        "green"
                                        if acc["login_state"] == "active"
                                        else "red"
                                    )
                                    ui.badge(acc["login_state"], color=color)
                                ui.label(
                                    acc["nickname"] or acc["username"]
                                ).classes("text-subtitle2 q-mt-xs")
                                ui.label(f"Followers: {acc['follower_count']}")

                # --- Recent posts ---
                ui.label("Recent Posts").classes("text-h6 q-mt-lg q-mb-sm")
                if not posts:
                    ui.label(
                        "No posts yet. Go to Content to generate some."
                    ).classes("text-grey")
                else:
                    columns = [
                        {
                            "name": "id",
                            "label": "ID",
                            "field": "id",
                            "sortable": True,
                        },
                        {
                            "name": "platform",
                            "label": "Platform",
                            "field": "platform",
                            "sortable": True,
                        },
                        {
                            "name": "title",
                            "label": "Title",
                            "field": "title",
                        },
                        {
                            "name": "status",
                            "label": "Status",
                            "field": "status",
                            "sortable": True,
                        },
                        {
                            "name": "created_at",
                            "label": "Created",
                            "field": "created_at",
                            "sortable": True,
                        },
                    ]
                    rows = []
                    for p in posts:
                        s_color = STATUS_COLORS.get(p["status"], "grey")
                        rows.append(
                            {
                                "id": p["id"],
                                "platform": p["platform"],
                                "title": (p["title"] or "")[:60],
                                "status": p["status"],
                                "status_color": s_color,
                                "created_at": p["created_at"] or "",
                            }
                        )
                    ui.table(
                        columns=columns, rows=rows, row_key="id"
                    ).classes("full-width").props("dense flat")

            await data_section()

            # Auto-refresh data every 30 seconds (no full page reload)
            ui.timer(30.0, data_section.refresh)
