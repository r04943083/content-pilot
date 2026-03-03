"""Publish page: post list with publish/delete actions."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from nicegui import ui

from content_pilot.gui.components.nav import page_layout, set_active_nav
from content_pilot.gui.constants import PLATFORMS, COLORS, STATUS_COLORS, PLATFORM_ICONS, PLATFORM_COLORS
from content_pilot.gui.i18n import t
from content_pilot.gui.main import get_pilot

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def register() -> None:
    @ui.page("/publish")
    async def publish_page():
        set_active_nav("/publish")
        page_layout(t("publish.title"))

        pilot = get_pilot()

        # State variables
        view_state = {"view": "list"}
        selected_posts = set()

        # Create containers first (will be populated later)
        list_container = ui.column().classes("full-width")
        kanban_container = ui.row().classes("full-width q-gutter-md")
        batch_toolbar = ui.row().classes(
            "full-width items-center q-gutter-sm q-mb-md q-pa-sm"
        ).style(
            f"background: {COLORS['surface']}; border-radius: 8px; display: none;"
        )

        # Define all callback functions FIRST (before UI elements that reference them)

        def _update_batch_toolbar():
            if selected_posts:
                batch_toolbar.style(f"background: {COLORS['surface']}; border-radius: 8px; display: flex;")
            else:
                batch_toolbar.style(f"background: {COLORS['surface']}; border-radius: 8px; display: none;")

        def _clear_selection():
            selected_posts.clear()
            current_posts = list_container.default_slot.children
            for card in current_posts:
                if hasattr(card, 'checkbox'):
                    card.checkbox.value = False
            _update_batch_toolbar()

        def _toggle_post_selection(post_id: int, is_selected: bool):
            if is_selected:
                selected_posts.add(post_id)
            else:
                selected_posts.discard(post_id)
            _update_batch_toolbar()

        def _toggle_all_select(select_all: bool):
            current_posts = list_container.default_slot.children
            for card in current_posts:
                if hasattr(card, 'post_id'):
                    checkbox = getattr(card, 'checkbox', None)
                    if checkbox:
                        checkbox.value = select_all
                        _toggle_post_selection(card.post_id, select_all)

        def _set_view(view: str):
            view_state["view"] = view
            if view == "list":
                list_container.set_visibility(True)
                kanban_container.set_visibility(False)
                batch_toolbar.set_visibility(True)
            else:
                list_container.set_visibility(False)
                kanban_container.set_visibility(True)
                batch_toolbar.set_visibility(False)
                _clear_selection()

        async def do_publish(post_id: int):
            ui.notify(t("publish.publish") + "...", type="info")
            try:
                ok = await pilot.publish(post_id)
                if ok:
                    ui.notify(t("common.success"), type="positive")
                else:
                    ui.notify(t("common.error"), type="negative")
            except Exception as e:
                ui.notify(f"Error: {e}", type="negative")
            await refresh_posts()

        async def do_delete(post_id: int):
            async def confirm_delete():
                await pilot.db.delete_post(post_id)
                ui.notify(t("publish.no_posts"), type="info")
                dialog.close()
                await refresh_posts()

            with ui.dialog() as dialog, ui.card().classes("q-pa-md").style(
                f"background: {COLORS['surface']};"
            ):
                ui.label(t("common.confirm_delete")).style(f"color: {COLORS['text_primary']};")
                with ui.row().classes("q-gutter-sm q-mt-sm"):
                    ui.button(
                        t("common.yes") + ", " + t("common.delete").lower(),
                        on_click=confirm_delete
                    ).props("color=negative")
                    ui.button(
                        t("common.cancel"),
                        on_click=dialog.close
                    ).props("outline")

            dialog.open()

        async def _publish_and_close(post_id: int, dialog):
            dialog.close()
            await do_publish(post_id)

        def _show_post_detail(post: dict):
            with ui.dialog() as dialog, ui.card().classes("q-pa-lg").style(
                f"background: {COLORS['surface']}; min-width: 400px; max-width: 600px;"
            ):
                ui.label(post.get("title") or "Untitled").classes("text-h6").style(
                    f"color: {COLORS['text_primary']};"
                )
                ui.label(post["platform"].capitalize()).classes("text-caption").style(
                    f"color: {COLORS['text_secondary']};"
                )

                images = json.loads(post.get("images", "[]"))
                if images:
                    ui.image(images[0]).classes("q-my-md").style(
                        "width: 100%; border-radius: 8px;"
                    )

                ui.separator().props("dark")

                content = post.get("content", "")
                if content:
                    ui.label(content[:500] + ("..." if len(content) > 500 else "")).classes("q-mt-sm text-body2").style(
                        f"color: {COLORS['text_primary']};"
                    )

                tags = []
                if post.get("tags"):
                    try:
                        tags = (
                            json.loads(post["tags"])
                            if isinstance(post["tags"], str)
                            else post["tags"]
                        )
                    except (json.JSONDecodeError, TypeError):
                        pass
                if tags:
                    with ui.row().classes("q-gutter-xs q-mt-sm"):
                        for tag in tags[:5]:
                            ui.badge(f"#{tag}", color="blue-grey").props("outline")

                if post.get("created_at"):
                    ui.label(f"Created: {post['created_at']}").classes(
                        "text-caption text-grey q-mt-md"
                    )

                with ui.row().classes("q-gutter-sm q-mt-md"):
                    if post.get("status") in ("approved", "draft"):
                        ui.button(
                            t("publish.publish"),
                            icon="publish",
                            on_click=lambda: _publish_and_close(post["id"], dialog)
                        ).props(f"color={COLORS['primary']}")
                    ui.button(
                        t("common.close"),
                        on_click=dialog.close
                    ).props("outline")

            dialog.open()

        async def batch_publish():
            if not selected_posts:
                return

            async def confirm_batch_publish():
                dialog.close()
                success_count = 0
                for post_id in list(selected_posts):
                    try:
                        ok = await pilot.publish(post_id)
                        if ok:
                            success_count += 1
                    except Exception:
                        pass
                ui.notify(
                    f"{t('common.success')}: {success_count}/{len(selected_posts)} posts published",
                    type="positive"
                )
                _clear_selection()
                await refresh_posts()

            with ui.dialog() as dialog, ui.card().classes("q-pa-md").style(
                f"background: {COLORS['surface']};"
            ):
                ui.label(
                    f"{t('publish.batch_operations')}: {len(selected_posts)} posts"
                ).style(f"color: {COLORS['text_primary']};")
                with ui.row().classes("q-gutter-sm q-mt-sm"):
                    ui.button(
                        t("common.confirm"),
                        on_click=confirm_batch_publish
                    ).props(f"color={COLORS['primary']}")
                    ui.button(
                        t("common.cancel"),
                        on_click=dialog.close
                    ).props("outline")

            dialog.open()

        async def batch_delete():
            if not selected_posts:
                return

            async def confirm_batch_delete():
                dialog.close()
                for post_id in list(selected_posts):
                    try:
                        await pilot.db.delete_post(post_id)
                    except Exception:
                        pass
                ui.notify(f"{len(selected_posts)} posts deleted", type="info")
                _clear_selection()
                await refresh_posts()

            with ui.dialog() as dialog, ui.card().classes("q-pa-md").style(
                f"background: {COLORS['surface']};"
            ):
                ui.label(
                    f"{t('common.confirm_delete')} {len(selected_posts)} posts?"
                ).style(f"color: {COLORS['text_primary']};")
                with ui.row().classes("q-gutter-sm q-mt-sm"):
                    ui.button(
                        t("common.yes") + ", " + t("common.delete").lower(),
                        on_click=confirm_batch_delete
                    ).props(f"color={COLORS['warning']}")
                    ui.button(
                        t("common.cancel"),
                        on_click=dialog.close
                    ).props("outline")

            dialog.open()

        async def refresh_posts():
            platform = filter_platform.value if filter_platform.value != "all" else None
            status = filter_status.value if filter_status.value != "all" else None
            posts = await pilot.db.get_posts(platform=platform, status=status, limit=50)

            # Update list view
            list_container.clear()
            with list_container:
                if not posts:
                    with ui.card().classes("q-pa-lg").style(
                        f"background: {COLORS['surface']}; text-align: center;"
                    ):
                        ui.label(t("publish.no_posts")).classes("text-grey")
                    return

                with ui.row().classes("q-gutter-md flex-wrap"):
                    for p in posts:
                        selectable_post_card(
                            p,
                            on_publish=do_publish,
                            on_delete=do_delete,
                            on_select=_toggle_post_selection,
                        )

            # Update kanban view
            kanban_container.clear()
            with kanban_container:
                status_groups = {
                    "draft": [], "approved": [], "scheduled": [], "published": [], "failed": [],
                }
                for p in posts:
                    s = p.get("status", "draft")
                    if s in status_groups:
                        status_groups[s].append(p)

                for status, status_posts in status_groups.items():
                    with ui.column().classes("flex-1 q-gutter-sm").style(
                        f"min-width: 250px; background: {COLORS['surface']}; border-radius: 8px; padding: 12px;"
                    ):
                        with ui.row().classes("items-center q-gutter-sm q-mb-sm"):
                            ui.icon("circle", size="xs").style(
                                f"color: {STATUS_COLORS.get(status, 'grey')};"
                            )
                            ui.label(t(f"status.{status}")).classes(
                                "text-body1 text-weight-bold"
                            ).style(f"color: {COLORS['text_primary']};")
                            ui.badge(len(status_posts), color="primary").props("transparent")

                        if not status_posts:
                            ui.label("—").classes("text-grey text-caption")
                        else:
                            for post in status_posts:
                                with ui.card().classes("q-pa-sm").style(
                                    f"background: {COLORS['background']}; border-radius: 6px; cursor: pointer;"
                                ).on("click", lambda p=post: _show_post_detail(p)):
                                    with ui.row().classes("items-center q-gutter-sm"):
                                        images = json.loads(post.get("images", "[]"))
                                        if images:
                                            ui.image(images[0]).classes("q-ml-sm").style(
                                                "width: 48px; height: 48px; border-radius: 6px; object-fit: cover;"
                                            )
                                        else:
                                            ui.icon("article", size="sm").classes("text-grey q-ml-sm")

                                        with ui.column().classes("flex-1 q-ml-sm"):
                                            title = (post.get("title") or "Untitled")[:35]
                                            ui.label(
                                                title + ("..." if len(post.get("title") or "") > 35 else "")
                                            ).classes("text-caption text-weight-medium").style(
                                                f"color: {COLORS['text_primary']};"
                                            )
                                            ui.label(post["platform"].capitalize()).classes(
                                                "text-caption text-grey"
                                            )

        # NOW build the UI (all callbacks are defined above)

        with ui.column().classes("full-width q-pa-md").style("max-width: 1400px; margin: auto;"):
            # Header with view toggle
            with ui.row().classes("full-width items-center justify-between q-mb-md"):
                ui.label(t("publish.post_management")).classes("text-h6").style(
                    f"color: {COLORS['text_primary']};"
                )

                with ui.row().classes("q-gutter-sm"):
                    ui.button(
                        icon="view_list",
                        on_click=lambda: _set_view("list")
                    ).props("flat round").style(
                        f"color: {COLORS['primary'] if view_state['view'] == 'list' else COLORS['text_secondary']};"
                    )
                    ui.button(
                        icon="view_kanban",
                        on_click=lambda: _set_view("kanban")
                    ).props("flat round").style(
                        f"color: {COLORS['primary'] if view_state['view'] == 'kanban' else COLORS['text_secondary']};"
                    )

            # Filter controls
            with ui.row().classes("q-gutter-md items-center q-mb-md"):
                platform_options = {"all": t("publish.all")}
                platform_options.update({p: p.capitalize() for p in PLATFORMS})
                filter_platform = ui.select(
                    platform_options,
                    value="all", label=t("publish.filter_platform")
                ).style("min-width: 150px;").props("outlined dark")

                status_options = {"all": t("publish.all")}
                status_options.update({s: t(f"status.{s}") for s in ["draft", "approved", "scheduled", "published", "failed"]})
                filter_status = ui.select(
                    status_options,
                    value="all",
                    label=t("publish.filter_status")
                ).style("min-width: 150px;").props("outlined dark")

            # Batch operations toolbar
            with batch_toolbar:
                ui.label(t("publish.batch_operations")).classes("text-subtitle2").style(
                    f"color: {COLORS['text_primary']};"
                )
                ui.checkbox("select_all_checkbox").on_value_change(
                    lambda e: _toggle_all_select(e.value)
                ).props("dense")

                ui.element("div").classes("flex-grow")

                ui.button(
                    t("publish.publish"),
                    icon="publish",
                    on_click=batch_publish
                ).props(f"color={COLORS['primary']} dense")

                ui.button(
                    t("common.delete"),
                    icon="delete",
                    on_click=batch_delete
                ).props(f"color={COLORS['warning']} dense")

                ui.button(
                    t("common.cancel"),
                    icon="close",
                    on_click=_clear_selection
                ).props("flat dense")

        # Set up filter change handlers
        filter_platform.on_value_change(lambda _: refresh_posts())
        filter_status.on_value_change(lambda _: refresh_posts())

        # Initial load
        await refresh_posts()
        _set_view("list")


def selectable_post_card(
    post: dict,
    on_publish,
    on_delete,
    on_select,
) -> None:
    """Render a selectable post card for batch operations."""
    platform = post["platform"]
    p_color = PLATFORM_COLORS.get(platform, "#666")

    with ui.card().classes("q-pa-md").style(
        f"flex: 1 1 280px; min-width: 280px; max-width: 100%; background: {COLORS['surface']}; "
        f"border-left: 4px solid {p_color}; border-radius: 8px;"
    ) as card:
        card.post_id = post["id"]

        with ui.row().classes("items-center q-gutter-sm q-mb-sm"):
            card.checkbox = ui.checkbox().props("dense").on_value_change(
                lambda e, pid=post["id"]: on_select(pid, e.value)
            )

            images = json.loads(post.get("images", "[]"))
            if images:
                ui.image(images[0]).classes("q-mb-sm").style(
                    "width: 100%; height: 180px; object-fit: cover; border-radius: 6px;"
                )
            else:
                with ui.row().classes("q-mb-sm items-center justify-center").style(
                    f"width: 100%; height: 120px; background: {COLORS['background']}; border-radius: 6px;"
                ):
                    ui.icon("article", size="lg").style(f"color: {COLORS['text_secondary']}")

            with ui.row().classes("items-center q-gutter-sm"):
                icon = PLATFORM_ICONS.get(platform, "article")
                ui.icon(icon, size="xs").style(f"color: {p_color};")
                ui.label(platform.capitalize()).classes("text-weight-bold text-caption").style(
                    f"color: {COLORS['text_primary']};"
                )
                color = STATUS_COLORS.get(post["status"], "grey")
                ui.badge(t(f"status.{post['status']}"), color=color).props("outline")

            if post.get("title"):
                title = post["title"]
                if len(title) > 60:
                    title = title[:60] + "..."
                ui.label(title).classes("text-subtitle1 q-mt-xs").style(
                    f"color: {COLORS['text_primary']};"
                )

            content_preview = (post.get("content") or "")[:120]
            if content_preview:
                ui.label(
                    content_preview + ("..." if len(post.get("content", "")) > 120 else "")
                ).classes("text-body2 text-grey-7 q-mt-xs").style(
                    f"color: {COLORS['text_secondary']};"
                )

            tags = []
            if post.get("tags"):
                try:
                    tags = json.loads(post["tags"]) if isinstance(post["tags"], str) else post["tags"]
                except (json.JSONDecodeError, TypeError):
                    pass
            if tags:
                with ui.row().classes("q-gutter-xs q-mt-sm"):
                    for tag in tags[:3]:
                        ui.badge(f"#{tag}", color="blue-grey").props("outline")

            if post.get("created_at"):
                ui.label(f"Created: {post['created_at']}").classes(
                    "text-caption text-grey q-mt-sm"
                ).style(f"color: {COLORS['text_secondary']};")

            with ui.row().classes("q-mt-sm q-gutter-sm"):
                if on_publish and post["status"] in ("approved", "draft"):
                    ui.button(
                        t("publish.publish"),
                        icon="publish",
                        on_click=lambda _, pid=post["id"]: on_publish(pid),
                    ).props(f"color={COLORS['primary']} dense")
                if on_delete and post["status"] in ("draft", "failed"):
                    ui.button(
                        t("common.delete"),
                        icon="delete",
                        on_click=lambda _, pid=post["id"]: on_delete(pid),
                    ).props(f"color={COLORS['warning']} dense outline")
