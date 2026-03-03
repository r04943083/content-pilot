"""Dashboard page: statistics cards, account overview, activity chart, and recent posts table."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from nicegui import ui

from content_pilot.gui.components.account_card import account_card
from content_pilot.gui.components.nav import page_layout, set_active_nav
from content_pilot.gui.components.stat_card import stat_card
from content_pilot.gui.constants import COLORS, PLATFORM_COLORS, STATUS_COLORS
from content_pilot.gui.i18n import t
from content_pilot.gui.main import get_pilot

logger = logging.getLogger(__name__)


def register() -> None:
    @ui.page("/")
    async def dashboard_page():
        set_active_nav("/")
        page_layout(t("dashboard.title"))

        with ui.column().classes(
            "full-width q-pa-md"
        ).style("max-width: 1200px; margin: auto;"):

            async def load_dashboard():
                pilot = get_pilot()
                accounts = await pilot.db.get_all_accounts()
                posts = await pilot.db.get_posts(limit=20)
                schedules = await pilot.db.fetch_all("SELECT * FROM schedules")

                # Calculate statistics
                total_accounts = len(accounts)
                today = datetime.now().date()

                def _safe_parse_dt(value) -> datetime | None:
                    """Safely parse a datetime string, returning None on failure."""
                    if not value or str(value) == "CURRENT_TIMESTAMP":
                        return None
                    try:
                        return datetime.fromisoformat(str(value))
                    except (ValueError, TypeError):
                        return None

                def is_posted_today(p: dict) -> bool:
                    """Check if post was published today."""
                    dt = _safe_parse_dt(p.get("published_at"))
                    return dt.date() == today if dt else False

                posts_today = sum(1 for p in posts if is_posted_today(p))
                pending_review = sum(1 for p in posts if p.get("status") == "approved")
                scheduled_tasks = sum(1 for s in schedules if s.get("enabled", 0))

                # --- Statistics Summary Row ---
                with ui.row().classes("full-width q-gutter-md").style(
                    "display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));"
                ):
                    stat_card(
                        t("dashboard.total_accounts"),
                        total_accounts,
                        "people",
                        COLORS["primary"],
                    )
                    stat_card(
                        t("dashboard.posts_today"),
                        posts_today,
                        "publish",
                        COLORS["accent"],
                    )
                    stat_card(
                        t("dashboard.pending_review"),
                        pending_review,
                        "pending_actions",
                        COLORS["primary_light"],
                    )
                    stat_card(
                        t("dashboard.scheduled_tasks"),
                        scheduled_tasks,
                        "schedule",
                        COLORS["warning"],
                    )

                # --- Account Overview + Quick Actions Row ---
                with ui.row().classes("full-width q-gutter-lg q-mt-lg").style(
                    "display: grid; grid-template-columns: 2fr 1fr; align-items: start;"
                ):
                    # Account Overview
                    with ui.card().classes("q-pa-md full-width").style(
                        f"background: {COLORS['surface']}; border-radius: 12px; min-height: 180px;"
                    ):
                        ui.label(t("dashboard.account_overview")).classes(
                            "text-h6 q-mb-md"
                        ).style(f"color: {COLORS['text_primary']};")
                        if not accounts:
                            ui.label(
                                t("dashboard.no_accounts")
                            ).classes("text-grey")
                        else:
                            with ui.row().classes("q-gutter-md flex-wrap"):
                                for acc in accounts:
                                    account_card(acc)

                    # Quick Actions Panel
                    with ui.card().classes("q-pa-md full-width").style(
                        f"background: {COLORS['surface']}; border-radius: 12px; min-height: 180px;"
                    ):
                        ui.label(t("dashboard.quick_actions")).classes(
                            "text-h6 q-mb-md"
                        ).style(f"color: {COLORS['text_primary']};")
                        with ui.column().classes("q-gutter-sm full-width"):
                            ui.button(
                                t("dashboard.generate_content"),
                                icon="edit_note",
                                on_click=lambda: ui.navigate.to("/content"),
                            ).props(
                                "unelevated no-caps"
                            ).classes("full-width").style(
                                f"background: {COLORS['primary']}; "
                                f"color: {COLORS['text_primary']};"
                            )
                            ui.button(
                                t("dashboard.view_all_posts"),
                                icon="list",
                                on_click=lambda: ui.navigate.to("/publish"),
                            ).props(
                                "outline no-caps"
                            ).classes("full-width").style(
                                f"color: {COLORS['primary']}; "
                                f"border-color: {COLORS['primary']};"
                            )

                # --- Activity Chart (Last 7 Days) ---
                with ui.card().classes("q-pa-md q-mt-lg full-width").style(
                    f"background: {COLORS['surface']}; "
                    "border-radius: 12px;"
                ):
                    ui.label(t("dashboard.activity_chart")).classes("text-h6 q-mb-md").style(
                        f"color: {COLORS['text_primary']};"
                    )

                    # Calculate activity for last 7 days
                    dates = []
                    counts = []

                    def is_created_on_date(p: dict, target_date) -> bool:
                        dt = _safe_parse_dt(p.get("created_at"))
                        return dt.date() == target_date if dt else False

                    for i in range(6, -1, -1):
                        date = today - timedelta(days=i)
                        dates.append(date.strftime("%m/%d"))
                        count = sum(1 for p in posts if is_created_on_date(p, date))
                        counts.append(count)

                    max_count = max(counts) if counts else 1

                    with ui.row().classes("full-width q-gutter-md items-end justify-center").style(
                        "padding: 0 16px;"
                    ):
                        for date, count in zip(dates, counts):
                            height_percent = (count / max_count) * 100 if max_count > 0 else 0
                            with ui.column().classes("items-center").style("flex: 1;"):
                                ui.label(str(count)).classes("text-caption q-mb-xs").style(
                                    f"color: {COLORS['text_secondary']};"
                                )
                                with ui.card().classes("q-pa-none").style(
                                    f"background: {COLORS['primary']}; "
                                    f"width: 100%; max-width: 40px; "
                                    f"height: {max(height_percent, 8)}px; "
                                    "border-radius: 4px 4px 0 0; "
                                    "transition: height 0.3s;"
                                ):
                                    pass
                                ui.label(date).classes("text-caption q-mt-xs").style(
                                    f"color: {COLORS['text_secondary']};"
                                )

                # --- Recent Posts Table ---
                ui.label(t("dashboard.recent_posts")).classes(
                    "text-h6 q-mt-lg q-mb-md"
                ).style(f"color: {COLORS['text_primary']};")
                if not posts:
                    ui.label(
                        t("dashboard.no_posts")
                    ).classes("text-grey")
                else:
                    columns = [
                        {
                            "name": "thumbnail",
                            "label": "",
                            "field": "thumbnail",
                            "sortable": False,
                            "align": "left",
                            "style": "width: 50px; padding: 8px;",
                        },
                        {
                            "name": "title",
                            "label": t("content.title_label"),
                            "field": "title",
                            "sortable": True,
                        },
                        {
                            "name": "platform",
                            "label": t("content.platform"),
                            "field": "platform",
                            "sortable": True,
                        },
                        {
                            "name": "status",
                            "label": t("common.filter"),
                            "field": "status",
                            "sortable": True,
                        },
                        {
                            "name": "created_at",
                            "label": t("accounts.last_updated"),
                            "field": "created_at",
                            "sortable": True,
                        },
                    ]
                    rows = []
                    for p in posts:
                        s_color = STATUS_COLORS.get(p["status"], "grey")
                        # Get first image if available
                        images = p.get("images", "")
                        thumbnail = ""
                        if images:
                            try:
                                import json

                                img_list = json.loads(images)
                                if img_list:
                                    thumbnail = img_list[0]
                            except (json.JSONDecodeError, TypeError):
                                pass

                        # Format created_at
                        created_at = p.get("created_at", "")
                        dt = _safe_parse_dt(created_at)
                        if dt:
                            created_at = dt.strftime("%Y-%m-%d %H:%M")

                        rows.append(
                            {
                                "id": p["id"],
                                "thumbnail": thumbnail,
                                "title": (p.get("title") or "")[:60] or t("common.untitled"),
                                "platform": p["platform"],
                                "status": p["status"],
                                "status_color": s_color,
                                "created_at": created_at,
                            }
                        )

                    table = ui.table(columns=columns, rows=rows, row_key="id").classes(
                        "full-width"
                    ).props("dense flat")

                    # Custom slot for thumbnail column
                    table.add_slot(
                        "body-cell-thumbnail",
                        """
                        <q-td key="thumbnail" :props="props">
                            <template v-if="props.row.thumbnail">
                                <img :src="props.row.thumbnail"
                                     style="width: 40px; height: 40px; object-fit: cover; border-radius: 4px;" />
                            </template>
                            <template v-else>
                                <q-icon name="image" size="md" color="grey" />
                            </template>
                        </q-td>
                        """
                    )

                    # Custom slot for status badge
                    table.add_slot(
                        "body-cell-status",
                        f"""
                        <q-td key="status" :props="props">
                            <q-badge :color="props.row.status_color">{{{{props.row.status}}}}</q-badge>
                        </q-td>
                        """
                    )

            await load_dashboard()
