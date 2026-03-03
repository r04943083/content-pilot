"""Accounts page: platform login cards with login/check session buttons."""

from __future__ import annotations

import logging

from nicegui import ui

from content_pilot.gui.components.nav import page_layout, set_active_nav
from content_pilot.gui.constants import (
    COLORS,
    PLATFORM_COLORS,
    PLATFORM_ICONS,
    PLATFORMS,
)
from content_pilot.gui.i18n import t
from content_pilot.gui.main import get_pilot

logger = logging.getLogger(__name__)


def register() -> None:
    @ui.page("/accounts")
    async def accounts_page():
        set_active_nav("/accounts")
        page_layout(t("accounts.title"))

        pilot = get_pilot()
        accounts = await pilot.db.get_all_accounts()
        account_map = {a["platform"]: a for a in accounts}

        log_area = None

        def append_log(msg: str):
            if log_area:
                log_area.push(msg)

        with ui.column().classes(
            "full-width q-pa-md"
        ).style("max-width: 1400px; margin: auto;"):
            ui.label(t("accounts.platform_accounts")).classes(
                "text-h5 q-mb-md"
            ).style(f"color: {COLORS['text_primary']};")

            with ui.row().classes("q-gutter-lg flex-wrap"):
                for platform in ["xiaohongshu", "douyin", "bilibili", "weibo"]:
                    acc = account_map.get(platform)
                    icon = PLATFORM_ICONS.get(platform, "person")
                    p_color = PLATFORM_COLORS.get(platform, "#666")
                    _render_platform_card(platform, acc, icon, p_color, append_log)

            ui.label(t("accounts.operation_log")).classes(
                "text-h5 q-mt-lg q-mb-md"
            ).style(f"color: {COLORS['text_primary']};")

            log_area = ui.log(max_lines=50).classes("full-width").style(
                f"background: {COLORS['surface']}; "
                "border-radius: 12px; height: 200px;"
            )


def _render_platform_card(
    platform: str,
    acc: dict | None,
    icon: str,
    p_color: str,
    append_log,
) -> None:
    """Render a platform account card with the new design system."""
    with ui.card().classes("q-pa-lg").style(
        f"flex: 1 1 280px; min-width: 280px; "
        f"background: {COLORS['surface']}; "
        f"border-left: 4px solid {p_color}; "
        "border-radius: 12px;"
    ):
        with ui.column().classes("full-width q-gutter-sm"):
            # Header row: avatar/icon + platform name + status
            with ui.row().classes("items-center q-gutter-md no-wrap"):
                # Avatar or Icon with unified size
                if acc and acc.get("avatar_url"):
                    ui.image(acc["avatar_url"]).classes(
                        "q-mr-sm"
                    ).style(
                        f"width: 56px; height: 56px; "
                        "border-radius: 50%; object-fit: cover; "
                        f"border: 2px solid {p_color};"
                    )
                else:
                    with ui.column().classes(
                        "items-center justify-center"
                    ).style(
                        f"width: 56px; min-width: 56px; height: 56px; "
                        f"background: {p_color}20; border-radius: 50%; "
                        f"border: 2px solid {p_color};"
                    ):
                        ui.icon(icon, size="2rem").style(f"color: {p_color};")

                with ui.column().classes("q-gutter-xs"):
                    # Platform name
                    ui.label(platform.capitalize()).classes(
                        "text-h5 text-weight-bold"
                    ).style(f"color: {COLORS['text_primary']};")

                    # Session status indicator with larger dot
                    if acc:
                        is_active = acc.get("login_state") == "active"
                        status_color = COLORS["accent"] if is_active else "#EF4444"
                        status_text = t("accounts.session_valid") if is_active else t("accounts.session_expired")

                        with ui.row().classes("items-center q-gutter-xs"):
                            ui.icon(
                                "circle",
                                size="xs"
                            ).style(f"color: {status_color};")
                            ui.label(status_text).classes(
                                "text-body2 text-weight-medium"
                            ).style(f"color: {status_color};")

                    # Nickname/username
                    if acc:
                        username = acc.get("nickname") or acc.get("username", "")
                        if username:
                            ui.label(username).classes(
                                "text-body1"
                            ).style(f"color: {COLORS['text_secondary']};")
                    else:
                        ui.label(t("accounts.not_logged_in")).classes(
                            "text-body1"
                        ).style(f"color: {COLORS['text_secondary']};")

            # Stats row (larger and more prominent)
            if acc:
                with ui.row().classes("q-gutter-lg q-mt-sm items-center"):
                    # Follower count
                    with ui.column().classes("q-gutter-none items-center"):
                        ui.label(
                            str(acc.get("follower_count", 0))
                        ).classes("text-h6 text-weight-bold").style(
                            f"color: {COLORS['text_primary']};"
                        )
                        ui.label(t("accounts.followers")).classes("text-caption").style(
                            f"color: {COLORS['text_secondary']};"
                        )

                    # Post count (if available)
                    if acc.get("post_count") is not None:
                        with ui.column().classes("q-gutter-none items-center"):
                            ui.label(str(acc["post_count"])).classes(
                                "text-h6 text-weight-bold"
                            ).style(f"color: {COLORS['text_primary']};")
                            ui.label(t("accounts.posts")).classes("text-caption").style(
                                f"color: {COLORS['text_secondary']};"
                            )

                    # Following count (if available)
                    if acc.get("following_count"):
                        with ui.column().classes("q-gutter-none items-center"):
                            ui.label(str(acc["following_count"])).classes(
                                "text-h6 text-weight-bold"
                            ).style(f"color: {COLORS['text_primary']};")
                            ui.label(t("accounts.following")).classes("text-caption").style(
                                f"color: {COLORS['text_secondary']};"
                            )

            # Last login time row
            if acc and acc.get("updated_at"):
                with ui.row().classes("q-mt-sm items-center q-gutter-xs"):
                    ui.icon("schedule", size="sm").style(f"color: {COLORS['text_secondary']};")
                    ui.label(
                        f"{t('accounts.last_login')}: {acc['updated_at'][:10]}"
                    ).classes("text-caption").style(f"color: {COLORS['text_secondary']};")

            # Divider
            ui.separator().style(
                f"background: {COLORS['text_secondary']}; "
                "opacity: 0.2; margin: 12px 0;"
            )

            # Action buttons row
            with ui.row().classes("q-gutter-sm justify-center q-mt-sm"):
                _make_login_btn(platform, append_log)
                _make_check_btn(platform, append_log)


def _make_login_btn(platform: str, append_log):
    """Create a login button for the given platform."""

    async def do_login():
        btn.props("loading")
        append_log(
            f"{t('accounts.login')} {platform}... ({t('accounts.check_browser_popup')})"
        )
        try:
            pilot = get_pilot()
            ok = await pilot.login(platform)
            if ok:
                append_log(f"{t('common.success')}: {platform}")
            else:
                append_log(f"{t('common.error')}: {platform}")
        except Exception as e:
            append_log(f"{t('common.error')}: {e}")
        finally:
            btn.props(remove="loading")
        ui.navigate.to("/accounts")

    btn = ui.button(
        t("accounts.login"),
        icon="login",
        on_click=do_login
    ).props(
        f"color={COLORS['primary']} outline no-caps"
    ).style("border-radius: 8px;")


def _make_check_btn(platform: str, append_log):
    """Create a check session button for the given platform."""

    async def do_check():
        btn.props("loading")
        append_log(f"{t('accounts.check_session')} {platform}...")
        try:
            pilot = get_pilot()
            context = await pilot.browser.get_context(platform)
            try:
                from content_pilot.platforms import PlatformRegistry

                connector = PlatformRegistry.create(platform, context)
                valid = await connector.check_session()
                if valid:
                    append_log(f"{platform}: {t('accounts.session_valid')}")
                else:
                    append_log(f"{platform}: {t('accounts.session_expired')}")
            finally:
                await context.close()
        except Exception as e:
            append_log(f"{t('common.error')}: {e}")
        finally:
            btn.props(remove="loading")

    btn = ui.button(
        t("accounts.check_session"),
        icon="verified_user",
        on_click=do_check
    ).props(
        f"color={COLORS['accent']} outline no-caps"
    ).style("border-radius: 8px;")
