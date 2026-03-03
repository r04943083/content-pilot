"""Statistics summary card component."""

from __future__ import annotations

from nicegui import ui

from content_pilot.gui.constants import COLORS


def stat_card(
    title: str,
    value: int | str,
    icon: str,
    color: str | None = None,
    trend: str | None = None,
) -> ui.card:
    """Render a statistics summary card.

    Args:
        title: Card title (e.g., "Total Accounts")
        value: Numeric or string value to display
        icon: Material Design icon name
        color: Icon color (defaults to primary)
        trend: Optional trend indicator (e.g., "+5" or "-2")

    Returns:
        The card element
    """
    with ui.card().classes("q-pa-md").style(
        f"background: {COLORS['surface']}; "
        "flex: 1 1 140px; min-width: 140px; border-radius: 12px;"
    ) as card:
        with ui.row().classes("items-center q-gutter-sm"):
            ui.icon(icon, size="md").style(
                f"color: {color or COLORS['primary']};"
            )
            with ui.column().classes("q-gutter-xs"):
                ui.label(str(value)).classes("text-h4 text-weight-bold").style(
                    f"color: {COLORS['text_primary']};"
                )
                ui.label(title).classes("text-caption").style(
                    f"color: {COLORS['text_secondary']};"
                )
                if trend:
                    trend_color = "#10B981" if trend.startswith("+") else "#EF4444"
                    with ui.row().classes("items-center q-gutter-xs"):
                        ui.icon(
                            "trending_up" if trend.startswith("+") else "trending_down",
                            size="xs",
                        ).style(f"color: {trend_color};")
                        ui.label(trend).classes("text-caption").style(
                            f"color: {trend_color};"
                        )
    return card
