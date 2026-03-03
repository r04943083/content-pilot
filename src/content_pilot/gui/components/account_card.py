"""Account overview card component."""

from __future__ import annotations

from nicegui import ui

from content_pilot.gui.constants import COLORS, PLATFORM_COLORS, PLATFORM_ICONS


def account_card(account: dict) -> ui.card:
    """Render an account overview card with avatar.

    Args:
        account: Account dictionary with keys:
            - platform: Platform name (e.g., "xiaohongshu")
            - nickname: Account nickname
            - username: Account username
            - avatar_url: URL to avatar image
            - follower_count: Number of followers
            - login_state: "active" or "inactive"

    Returns:
        The card element
    """
    platform = account["platform"]
    p_color = PLATFORM_COLORS.get(platform, "#666")
    icon = PLATFORM_ICONS.get(platform, "person")

    with ui.card().classes("q-pa-md").style(
        f"background: {COLORS['surface']}; "
        f"border-left: 4px solid {p_color}; "
        "flex: 1 1 200px; min-width: 200px; border-radius: 12px;"
    ) as card:
        with ui.row().classes("items-center q-gutter-sm"):
            # Avatar or icon
            if account.get("avatar_url"):
                ui.image(account["avatar_url"]).classes(
                    "q-pa-xs"
                ).style(
                    "width: 56px; height: 56px; "
                    "border-radius: 50%; object-fit: cover;"
                )
            else:
                ui.icon(icon).style(
                    f"color: {p_color}; font-size: 48px; "
                    "width: 48px; height: 48px;"
                )

            with ui.column().classes("q-gutter-xs"):
                name = account.get("nickname") or account.get("username", platform)
                ui.label(name).classes(
                    "text-subtitle1 text-weight-bold"
                ).style(f"color: {COLORS['text_primary']};")
                ui.label(
                    f"{account.get('follower_count', 0):,} {account.get('follower_count', 0) == 1 and 'follower' or 'followers'}"
                ).classes("text-caption").style(f"color: {COLORS['text_secondary']};")

        # Status indicator
        is_active = account.get("login_state") == "active"
        with ui.row().classes("items-center q-gutter-xs q-mt-sm"):
            ui.icon(
                "circle", size="xs"
            ).style(f"color: {'#10B981' if is_active else '#EF4444'};")
            ui.label("Active" if is_active else "Inactive").classes(
                "text-caption"
            ).style(f"color: {COLORS['text_secondary']};")

    return card
