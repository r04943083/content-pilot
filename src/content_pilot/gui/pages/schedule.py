"""Schedule page: list, create, pause, resume, delete schedules."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from calendar import monthcalendar, month_name
from typing import TYPE_CHECKING

from apscheduler.triggers.cron import CronTrigger
from nicegui import ui

from content_pilot.gui.components.nav import set_active_nav
from content_pilot.gui.constants import COLORS, PLATFORMS, STYLES
from content_pilot.gui.i18n import t
from content_pilot.gui.main import get_pilot

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


def _format_next_run(cron_expression: str) -> str:
    """Calculate human-readable time until next scheduled run.

    Args:
        cron_expression: Cron expression (e.g., "0 20 * * *")

    Returns:
        Human-readable time string or "Unknown"
    """
    try:
        trigger = CronTrigger.from_crontab(cron_expression)
        next_run = trigger.get_next_fire_time(None, datetime.now())
        if next_run:
            delta = next_run - datetime.now()
            if delta.days > 0:
                return f"{t('schedule.next_run')}: {delta.days}d {(delta.seconds // 3600) % 24}h"
            elif delta.seconds >= 3600:
                hours = delta.seconds // 3600
                minutes = (delta.seconds // 60) % 60
                return f"{t('schedule.next_run')}: {hours}h {minutes}m"
            elif delta.seconds >= 60:
                return f"{t('schedule.next_run')}: {delta.seconds // 60}m"
            else:
                return f"{t('schedule.next_run')}: {delta.seconds}s"
    except Exception:
        pass
    return f"{t('schedule.next_run')}: Unknown"


def _get_schedules_for_day(schedules: list[dict], year: int, month: int, day: int) -> list[dict]:
    """Get all schedules that run on a specific day.

    Args:
        schedules: List of schedule dicts
        year: Year
        month: Month (1-12)
        day: Day of month

    Returns:
        List of schedules that run on this day
    """
    try:
        date_to_check = datetime(year, month, day)
        matching = []
        for s in schedules:
            if not s.get("enabled"):
                continue
            try:
                trigger = CronTrigger.from_crontab(s["cron_expression"])
                next_runs = []
                # Check for next 30 days for this trigger
                check_date = date_to_check
                for _ in range(30):
                    next_fire = trigger.get_next_fire_time(None, check_date)
                    if next_fire is None:
                        break
                    next_runs.append(next_fire)
                    check_date = next_fire

                # Check if date_to_check matches any run
                if any(
                    nr.year == year and nr.month == month and nr.day == day
                    for nr in next_runs
                ):
                    matching.append(s)
            except Exception:
                continue
        return matching
    except Exception:
        return []


def register() -> None:
    @ui.page("/schedule")
    async def schedule_page():
        set_active_nav("/schedule")
        pilot = get_pilot()

        # State variables
        view_state = {"current": "list"}  # "list" or "calendar"
        calendar_state = {"year": datetime.now().year, "month": datetime.now().month}

        with ui.column().classes(
            "full-width q-pa-md"
        ).style("max-width: 1400px; margin: auto;"):
            # Header with view toggle
            with ui.row().classes("full-width items-center justify-between q-mb-md"):
                ui.label(t("schedule.schedules")).classes(
                    "text-h6"
                ).style(f"color: {COLORS['text_primary']};")

                view_toggle = ui.toggle(
                    {"list": t("schedule.list_view"), "calendar": t("schedule.calendar_view")},
                    value="list",
                ).props("dark dense")

                def on_view_change(e):
                    view_state["current"] = e.value
                    if e.value == "calendar":
                        calendar_container.classes("visible")
                        list_container.classes("hidden")
                    else:
                        calendar_container.classes("hidden")
                        list_container.classes("visible")

                view_toggle.on_value_change(on_view_change)

            # Calendar view (hidden by default)
            with ui.card().classes("full-width q-pa-lg hidden").style(
                f"background: {COLORS['surface']}; border-radius: 12px;"
            ) as calendar_container:
                ui.label(t("schedule.calendar_view")).classes(
                    "text-subtitle1 q-mb-md"
                ).style(f"color: {COLORS['text_primary']};")

                # Month navigation
                with ui.row().classes("full-width items-center justify-between q-mb-md"):
                    ui.button(icon="chevron_left", on_click=lambda: _change_month(-1)).props(
                        "dense flat"
                    ).style(f"color: {COLORS['primary']};")
                    month_label = ui.label("").classes("text-h6 text-weight-bold").style(
                        f"color: {COLORS['text_primary']};"
                    )
                    ui.button(icon="chevron_right", on_click=lambda: _change_month(1)).props(
                        "dense flat"
                    ).style(f"color: {COLORS['primary']};")

                # Day headers
                with ui.row().classes("full-width q-gutter-xs q-mb-sm"):
                    day_names = [t("schedule.mon"), t("schedule.tue"), t("schedule.wed"),
                                t("schedule.thu"), t("schedule.fri"), t("schedule.sat"),
                                t("schedule.sun")]
                    for day in day_names:
                        ui.label(day).classes(
                            "flex-1 text-center text-caption text-weight-bold"
                        ).style(f"color: {COLORS['text_secondary']};")

                # Calendar grid container
                calendar_grid = ui.column().classes("full-width")

            # List view
            with ui.column().classes("full-width") as list_container:
                # Schedule cards container
                schedules_container = ui.row().classes("q-gutter-md flex-wrap")

                # Add new schedule form
                ui.separator().classes("q-my-lg")

                ui.label(t("schedule.add_new")).classes(
                    "text-h6 q-mt-md q-mb-md"
                ).style(f"color: {COLORS['text_primary']};")

                with ui.card().classes("q-pa-md full-width").style(
                    f"background: {COLORS['surface']}; border-radius: 12px;"
                ):
                    with ui.row().classes("q-gutter-md items-start"):
                        with ui.column().classes("flex-1"):
                            name_input = ui.input(
                                t("schedule.name"),
                                placeholder="Daily Tech Post"
                            ).classes("full-width").props("outlined dark")

                            platform_input = ui.select(
                                PLATFORMS,
                                value="xiaohongshu",
                                label=t("content.platform"),
                            ).classes("full-width").props("outlined dark")

                        with ui.column().classes("flex-1"):
                            topic_input = ui.input(
                                t("content.topic"),
                                placeholder="AI news"
                            ).classes("full-width").props("outlined dark")

                            style_input = ui.select(
                                STYLES, value="tutorial", label=t("content.style")
                            ).classes("full-width").props("outlined dark")

                        with ui.column().classes("flex-1"):
                            ui.label(t("schedule.schedule")).classes("text-caption q-mb-sm").style(
                                f"color: {COLORS['text_secondary']};"
                            )

                            cron_preset = ui.select(
                                {
                                    "0 9 * * *": f"{t('schedule.daily')} 9:00",
                                    "0 20 * * *": f"{t('schedule.daily')} 20:00",
                                    "0 9 * * 1": f"{t('schedule.weekly')} ({t('schedule.mon')})",
                                    "0 20 * * 5": f"{t('schedule.weekly')} ({t('schedule.fri')})",
                                    "0 */4 * * *": f"{t('schedule.every')} 4h",
                                    "custom": t("schedule.custom"),
                                },
                                value="0 20 * * *",
                                label=t("schedule.preset"),
                            ).classes("full-width").props("outlined dark")

                            cron_input = ui.input(
                                t("schedule.cron_expression"),
                                value="0 20 * * *",
                            ).classes("full-width").props("outlined dark")

                            cron_input.bind_value_from(cron_preset, "value")

                            def _update_cron(e):
                                if e.value != "custom":
                                    cron_input.value = e.value

                            cron_preset.on_value_change(_update_cron)

                            # Cron description helper
                            cron_description = ui.label("").classes("text-caption q-mt-xs").style(
                                f"color: {COLORS['text_secondary']};"
                            )

                            def _update_description():
                                desc = _describe_cron(cron_input.value)
                                cron_description.text = desc

                            cron_input.on_value_change(_update_description)
                            _update_description()

                async def do_add():
                    name = name_input.value.strip()
                    if not name:
                        ui.notify(
                            f"{t('common.error')}: {t('schedule.name_required')}",
                            type="warning"
                        )
                        return
                    cron = cron_input.value.strip()
                    if not cron:
                        ui.notify(
                            f"{t('common.error')}: {t('schedule.cron_required')}",
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
                            f"{t('common.success')}: {t('schedule.created')} (ID: {sid})",
                            type="positive",
                        )
                        name_input.value = ""
                        topic_input.value = ""
                        await refresh_schedules()
                    except Exception as e:
                        ui.notify(f"{t('common.error')}: {e}", type="negative")
                    finally:
                        add_btn.props(remove="loading")

                add_btn = ui.button(
                    t("schedule.add_new"),
                    icon="add",
                    on_click=do_add
                ).props(f"color={COLORS['primary']}").classes("q-mt-md")

            async def refresh_schedules():
                """Refresh the schedules list and calendar."""
                schedules = await pilot.db.get_schedules()

                # Update list view
                schedules_container.clear()
                with schedules_container:
                    if not schedules:
                        ui.label(t("schedule.no_schedules")).classes(
                            "text-grey q-pa-md"
                        )
                    else:
                        for s in schedules:
                            with ui.card().classes("q-pa-md").style(
                                f"background: {COLORS['surface']}; "
                                f"border-left: 4px solid {COLORS['accent'] if s.get('enabled') else COLORS['warning']}; "
                                "min-width: 300px; border-radius: 12px;"
                            ):
                                with ui.row().classes("items-center justify-between"):
                                    ui.label(s["name"]).classes(
                                        "text-subtitle1 text-weight-bold"
                                    ).style(f"color: {COLORS['text_primary']};")

                                    status_color = COLORS["accent"] if s.get("enabled") else COLORS["warning"]
                                    status_text = t("schedule.enabled") if s.get("enabled") else t("schedule.disabled")
                                    ui.badge(status_text, color=status_color).props("transparent")

                                ui.label(s["platform"]).classes("text-caption").style(
                                    f"color: {COLORS['text_secondary']};"
                                )

                                ui.label(f"{t('schedule.cron')}: {s['cron_expression']}").classes(
                                    "text-caption q-mt-xs"
                                ).style(f"color: {COLORS['text_secondary']};")

                                # Topic
                                if s.get("topic"):
                                    ui.label(f"{t('schedule.topic')}: {s['topic']}").classes(
                                        "text-caption"
                                    ).style(f"color: {COLORS['text_secondary']};")

                                # Next run countdown
                                if s.get("enabled"):
                                    ui.label(_format_next_run(s["cron_expression"])).classes(
                                        "text-caption q-mt-xs"
                                    ).style(
                                        f"color: {COLORS['primary']};"
                                    )

                                with ui.row().classes("q-gutter-sm q-mt-sm"):
                                    if s["enabled"]:
                                        _pause_btn(s["id"], refresh_schedules)
                                    else:
                                        _resume_btn(s["id"], refresh_schedules)
                                    _delete_btn(s["id"], refresh_schedules)

                # Update calendar view
                _update_calendar(schedules)

            def _update_calendar(schedules: list[dict]):
                """Update the calendar grid with schedules."""
                calendar_grid.clear()
                with calendar_grid:
                    cal = monthcalendar(calendar_state["year"], calendar_state["month"])
                    month_name_str = month_name[calendar_state["month"]]
                    month_label.text = f"{month_name_str} {calendar_state['year']}"

                    today = datetime.now()
                    is_current_month = (
                        calendar_state["year"] == today.year
                        and calendar_state["month"] == today.month
                    )

                    for week_idx, week in enumerate(cal):
                        with ui.row().classes("full-width q-gutter-xs q-mt-xs"):
                            for day in week:
                                with ui.card().classes(
                                    "flex-1 q-pa-xs cursor-pointer"
                                ).style(
                                    f"background: {COLORS['background'] if day != 0 else 'transparent'}; "
                                    f"border: 1px solid {COLORS['primary'] if is_current_month and day == today.day else 'rgba(255,255,255,0.1)'}; "
                                    "min-height: 70px; border-radius: 8px; transition: all 0.2s;"
                                ):
                                    if day != 0:
                                        # Day number
                                        is_today = is_current_month and day == today.day
                                        ui.label(str(day)).classes(
                                            f"text-caption text-weight-bold"
                                        ).style(
                                            f"color: {COLORS['primary']} if is_today else {COLORS['text_primary']};"
                                        )

                                        # Get schedules for this day
                                        day_schedules = _get_schedules_for_day(
                                            schedules,
                                            calendar_state["year"],
                                            calendar_state["month"],
                                            day
                                        )

                                        # Show schedule indicators
                                        if day_schedules:
                                            with ui.column().classes("q-mt-xs"):
                                                for sched in day_schedules[:3]:  # Max 3 shown
                                                    # Platform icon
                                                    platform = sched.get("platform", "unknown")
                                                    icon_name = PLATFORMS.get(platform, "schedule")
                                                    ui.icon(icon_name, size="xs").classes(
                                                        "text-primary"
                                                    ).style(f"color: {COLORS['primary_light']};")

                                                if len(day_schedules) > 3:
                                                    ui.label(f"+{len(day_schedules) - 3}").classes(
                                                        "text-caption text-center"
                                                    ).style(f"color: {COLORS['text_secondary']};")

                                        # Click to show details
                                        if day_schedules:
                                            ui.card().classes("hidden").props("flat")
                                            async def show_details(d=day, ds=day_schedules):
                                                with ui.dialog() as dialog, ui.card():
                                                    ui.label(f"{t('schedule.schedules')} - {month_name_str} {d}").classes(
                                                        "text-h6 q-mb-md"
                                                    )
                                                    with ui.column().classes("q-gutter-sm"):
                                                        for sched in ds:
                                                            with ui.card().classes("q-pa-sm"):
                                                                with ui.row().classes("items-center q-gutter-sm"):
                                                                    ui.icon(
                                                                        PLATFORMS.get(sched.get("platform"), "schedule")
                                                                    ).classes("text-primary")
                                                                    ui.label(sched["name"]).classes("text-subtitle2")
                                                                ui.label(f"{t('schedule.cron')}: {sched['cron_expression']}").classes(
                                                                    "text-caption"
                                                                )
                                                                if sched.get("topic"):
                                                                    ui.label(f"{t('schedule.topic')}: {sched['topic']}").classes(
                                                                        "text-caption"
                                                                    )
                                                    with ui.row().classes("q-gutter-sm q-mt-md"):
                                                        ui.button(
                                                            t("common.close"),
                                                            on_click=dialog.close
                                                        ).props("outline")
                                                dialog.open()

                                            # Make the card clickable
                                            current_card = ui.parent_card
                                            current_card.on("click", show_details)
                                            current_card.classes(
                                                "hover:opacity-80"
                                            ).style("cursor: pointer;")

            def _change_month(delta: int):
                """Navigate between months.

                Args:
                    delta: Number of months to move (-1 or 1)
                """
                new_month = calendar_state["month"] + delta
                if new_month > 12:
                    calendar_state["month"] = 1
                    calendar_state["year"] += 1
                elif new_month < 1:
                    calendar_state["month"] = 12
                    calendar_state["year"] -= 1
                else:
                    calendar_state["month"] = new_month
                # Refresh calendar (schedules are fetched separately)
                ui.run_javascript("window.location.reload()")

            def _describe_cron(cron_expr: str) -> str:
                """Provide a human-readable description of the cron expression.

                Args:
                    cron_expr: Cron expression

                Returns:
                    Human-readable description
                """
                parts = cron_expr.strip().split()
                if len(parts) != 5:
                    return t("schedule.invalid_cron")

                minute, hour, day, month, weekday = parts

                # Common patterns
                if cron_expr == "0 9 * * *":
                    return f"{t('schedule.runs_daily')} 09:00"
                elif cron_expr == "0 20 * * *":
                    return f"{t('schedule.runs_daily')} 20:00"
                elif cron_expr == "0 * * * *":
                    return t("schedule.runs_hourly")
                elif cron_expr == "0 */4 * * *":
                    return f"{t('schedule.runs_every')} 4h"
                elif cron_expr == "0 9 * * 1":
                    return f"{t('schedule.runs_weekly')} ({t('schedule.mon')}) 09:00"
                elif cron_expr == "0 9 * * 5":
                    return f"{t('schedule.runs_weekly')} ({t('schedule.fri')}) 09:00"

                # Generic description
                return f"{t('schedule.cron_format')}: {cron_expr}"

            # Initial load
            await refresh_schedules()


def _pause_btn(schedule_id: int, refresh: Callable[[], None]) -> None:
    """Create a pause button for a schedule.

    Args:
        schedule_id: ID of the schedule to pause
        refresh: Callback to refresh the UI
    """
    async def do_pause():
        pilot = get_pilot()
        await pilot.scheduler.pause_schedule(schedule_id)
        ui.notify(t("schedule.paused"), type="info")
        await refresh()

    ui.button(
        t("schedule.pause"),
        icon="pause",
        on_click=do_pause
    ).props("dense outline").style(f"color: {COLORS['warning']};")


def _resume_btn(schedule_id: int, refresh: Callable[[], None]) -> None:
    """Create a resume button for a schedule.

    Args:
        schedule_id: ID of the schedule to resume
        refresh: Callback to refresh the UI
    """
    async def do_resume():
        pilot = get_pilot()
        await pilot.scheduler.resume_schedule(schedule_id)
        ui.notify(t("schedule.resumed"), type="positive")
        await refresh()

    ui.button(
        t("schedule.resume"),
        icon="play_arrow",
        on_click=do_resume
    ).props("dense outline").style(f"color: {COLORS['accent']};")


def _delete_btn(schedule_id: int, refresh: Callable[[], None]) -> None:
    """Create a delete button for a schedule.

    Args:
        schedule_id: ID of the schedule to delete
        refresh: Callback to refresh the UI
    """
    async def do_delete():
        async def confirm_delete():
            pilot = get_pilot()
            await pilot.scheduler.remove_schedule(schedule_id)
            ui.notify(t("schedule.deleted"), type="info")
            dialog.close()
            await refresh()

        with ui.dialog() as dialog, ui.card():
            ui.label(t("common.confirm_delete"))
            with ui.row().classes("q-gutter-sm q-mt-sm"):
                ui.button(
                    f"{t('common.yes')}, {t('common.delete').lower()}",
                    on_click=confirm_delete
                ).props(f"color={COLORS['warning']}")
                ui.button(
                    t("common.cancel"),
                    on_click=dialog.close
                ).props("outline")
        dialog.open()

    ui.button(
        t("common.delete"),
        icon="delete",
        on_click=do_delete
    ).props("dense outline").style("color: #EF4444;")
