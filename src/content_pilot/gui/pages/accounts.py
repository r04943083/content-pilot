"""Accounts page: platform login cards with login/check session buttons."""

from __future__ import annotations

import logging

from nicegui import ui

from content_pilot.gui.components.nav import page_layout
from content_pilot.gui.main import get_pilot

logger = logging.getLogger(__name__)

PLATFORMS = ["xiaohongshu", "douyin", "bilibili", "weibo"]


def register() -> None:
    @ui.page("/accounts")
    async def accounts_page():
        page_layout("Accounts")

        pilot = get_pilot()
        accounts = await pilot.db.get_all_accounts()
        account_map = {a["platform"]: a for a in accounts}

        log_area = None

        def append_log(msg: str):
            if log_area:
                log_area.push(msg)

        ui.label("Platform Accounts").classes("text-h6 q-mt-md q-mb-sm")

        with ui.row().classes("q-gutter-md flex-wrap"):
            for platform in PLATFORMS:
                acc = account_map.get(platform)
                with ui.card().classes("q-pa-md").style("min-width: 280px;"):
                    ui.label(platform.capitalize()).classes("text-h6 text-capitalize")
                    if acc:
                        color = "green" if acc["login_state"] == "active" else "red"
                        ui.badge(acc["login_state"], color=color)
                        ui.label(f"User: {acc['nickname'] or acc['username']}")
                        ui.label(f"Followers: {acc['follower_count']}")
                        ui.label(f"Updated: {acc['updated_at'] or 'N/A'}").classes(
                            "text-caption text-grey"
                        )
                    else:
                        ui.label("Not logged in").classes("text-grey")

                    with ui.row().classes("q-mt-sm q-gutter-sm"):
                        _make_login_btn(platform, append_log)
                        _make_check_btn(platform, append_log)

        ui.label("Operation Log").classes("text-h6 q-mt-lg q-mb-sm")
        log_area = ui.log(max_lines=50).classes("full-width").style("height: 200px;")


def _make_login_btn(platform: str, append_log):
    async def do_login():
        append_log(f"Logging in to {platform}... (check for browser popup)")
        try:
            pilot = get_pilot()
            ok = await pilot.login(platform)
            if ok:
                append_log(f"Login to {platform} succeeded!")
            else:
                append_log(f"Login to {platform} failed.")
        except Exception as e:
            append_log(f"Login error: {e}")
        ui.navigate.to("/accounts")

    ui.button("Login", icon="login", on_click=do_login).props("color=primary")


def _make_check_btn(platform: str, append_log):
    async def do_check():
        append_log(f"Checking session for {platform}...")
        try:
            pilot = get_pilot()
            context = await pilot.browser.get_context(platform)
            try:
                from content_pilot.platforms import PlatformRegistry

                connector = PlatformRegistry.create(platform, context)
                valid = await connector.check_session()
                if valid:
                    append_log(f"{platform}: session is valid")
                else:
                    append_log(f"{platform}: session expired, please login again")
            finally:
                await context.close()
        except Exception as e:
            append_log(f"Check error: {e}")

    ui.button("Check Session", icon="verified_user", on_click=do_check).props(
        "color=secondary outline"
    )
