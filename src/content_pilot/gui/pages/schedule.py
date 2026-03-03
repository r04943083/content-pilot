"""Schedule page: list, create, pause, resume, delete schedules."""

from __future__ import annotations

import logging

from nicegui import ui

from content_pilot.gui.components.nav import page_layout
from content_pilot.gui.constants import PLATFORMS, STYLES
from content_pilot.gui.main import get_pilot

logger = logging.getLogger(__name__)


def register() -> None:
    @ui.page("/schedule")
    async def schedule_page():
        page_layout("Schedules")

        pilot = get_pilot()

        with ui.column().classes(
            "full-width q-pa-md"
        ).style("max-width: 1200px; margin: auto;"):
            # --- Schedule list ---
            ui.label("Schedules").classes("text-h6 q-mb-sm")
            schedule_container = ui.column().classes("full-width")

            async def refresh_schedules():
                schedules = await pilot.db.get_schedules()
                schedule_container.clear()
                with schedule_container:
                    if not schedules:
                        ui.label("No schedules configured.").classes(
                            "text-grey"
                        )
                        return
                    columns = [
                        {"name": "id", "label": "ID", "field": "id"},
                        {
                            "name": "name",
                            "label": "Name",
                            "field": "name",
                        },
                        {
                            "name": "platform",
                            "label": "Platform",
                            "field": "platform",
                        },
                        {
                            "name": "cron",
                            "label": "Cron",
                            "field": "cron_expression",
                        },
                        {
                            "name": "topic",
                            "label": "Topic",
                            "field": "topic",
                        },
                        {
                            "name": "enabled",
                            "label": "Enabled",
                            "field": "enabled",
                        },
                        {
                            "name": "last_run",
                            "label": "Last Run",
                            "field": "last_run_at",
                        },
                    ]
                    rows = []
                    for s in schedules:
                        rows.append(
                            {
                                "id": s["id"],
                                "name": s["name"],
                                "platform": s["platform"],
                                "cron_expression": s["cron_expression"],
                                "topic": (s["topic"] or "")[:40],
                                "enabled": "Yes"
                                if s["enabled"]
                                else "No",
                                "last_run_at": s["last_run_at"] or "Never",
                            }
                        )
                    ui.table(
                        columns=columns, rows=rows, row_key="id"
                    ).classes("full-width").props("dense flat")

                    # Action buttons per schedule
                    with ui.row().classes(
                        "q-gutter-sm q-mt-sm flex-wrap"
                    ):
                        for s in schedules:
                            with ui.card().classes("q-pa-sm"):
                                ui.label(
                                    f"{s['name']} (ID: {s['id']})"
                                ).classes("text-caption")
                                with ui.row().classes("q-gutter-xs"):
                                    if s["enabled"]:
                                        _pause_btn(
                                            s["id"], refresh_schedules
                                        )
                                    else:
                                        _resume_btn(
                                            s["id"], refresh_schedules
                                        )
                                    _delete_btn(
                                        s["id"], refresh_schedules
                                    )

            await refresh_schedules()

            # --- Add new schedule form ---
            ui.separator().classes("q-mt-lg")
            ui.label("Add New Schedule").classes(
                "text-h6 q-mt-md q-mb-sm"
            )
            with ui.card().classes("q-pa-md full-width"):
                name_input = ui.input(
                    "Name", placeholder="Daily Tech Post"
                ).classes("full-width").props("outlined")
                platform_input = ui.select(
                    PLATFORMS,
                    value="xiaohongshu",
                    label="Platform",
                ).classes("full-width").props("outlined")
                topic_input = ui.input(
                    "Topic", placeholder="AI news"
                ).classes("full-width").props("outlined")
                style_input = ui.select(
                    STYLES, value="tutorial", label="Style"
                ).classes("full-width").props("outlined")
                cron_input = ui.input(
                    "Cron Expression",
                    placeholder="0 20 * * *",
                    value="0 20 * * *",
                ).classes("full-width").props("outlined")

                async def do_add():
                    name = name_input.value.strip()
                    if not name:
                        ui.notify(
                            "Name is required", type="warning"
                        )
                        return
                    cron = cron_input.value.strip()
                    if not cron:
                        ui.notify(
                            "Cron expression is required",
                            type="warning",
                        )
                        return
                    add_btn.props("loading")
                    try:
                        sid = await pilot.scheduler.add_schedule(
                            name=name,
                            platform=platform_input.value,
                            topic=topic_input.value.strip(),
                            style=style_input.value,
                            cron_expression=cron,
                        )
                        ui.notify(
                            f"Schedule '{name}' created (ID: {sid})",
                            type="positive",
                        )
                        name_input.value = ""
                        topic_input.value = ""
                        await refresh_schedules()
                    except Exception as e:
                        ui.notify(f"Error: {e}", type="negative")
                    finally:
                        add_btn.props(remove="loading")

                add_btn = ui.button(
                    "Add Schedule", icon="add", on_click=do_add
                ).props("color=primary").classes("q-mt-sm")


def _pause_btn(schedule_id: int, refresh):
    async def do_pause():
        pilot = get_pilot()
        await pilot.scheduler.pause_schedule(schedule_id)
        ui.notify(f"Schedule {schedule_id} paused", type="info")
        await refresh()

    ui.button("Pause", icon="pause", on_click=do_pause).props(
        "dense outline color=orange"
    )


def _resume_btn(schedule_id: int, refresh):
    async def do_resume():
        pilot = get_pilot()
        await pilot.scheduler.resume_schedule(schedule_id)
        ui.notify(f"Schedule {schedule_id} resumed", type="positive")
        await refresh()

    ui.button("Resume", icon="play_arrow", on_click=do_resume).props(
        "dense outline color=green"
    )


def _delete_btn(schedule_id: int, refresh):
    async def do_delete():
        async def confirm_delete():
            pilot = get_pilot()
            await pilot.scheduler.remove_schedule(schedule_id)
            ui.notify(
                f"Schedule {schedule_id} deleted", type="info"
            )
            dialog.close()
            await refresh()

        with ui.dialog() as dialog, ui.card():
            ui.label(
                f"Are you sure you want to delete schedule {schedule_id}?"
            )
            with ui.row().classes("q-gutter-sm q-mt-sm"):
                ui.button(
                    "Yes, delete", on_click=confirm_delete
                ).props("color=negative")
                ui.button(
                    "Cancel", on_click=dialog.close
                ).props("outline")
        dialog.open()

    ui.button("Delete", icon="delete", on_click=do_delete).props(
        "dense outline color=red"
    )
