"""Content generation page: 3-column layout with integrated auto image generation."""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from nicegui import ui

from content_pilot.config import get_settings
from content_pilot.gui.components.nav import page_layout, set_active_nav
from content_pilot.gui.constants import COLORS, PLATFORMS, STYLES
from content_pilot.gui.i18n import t
from content_pilot.gui.main import get_pilot

if TYPE_CHECKING:
    from content_pilot.app import App

logger = logging.getLogger(__name__)


def _get_images_dir() -> Path:
    """Get the images directory path."""
    data_dir = Path(get_settings().general.data_dir).resolve()
    images_dir = data_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    return images_dir


def _create_draft_card(post: dict) -> None:
    """Create a draft card for display in the recent drafts section."""
    with ui.card().classes("q-pa-sm min-w-64 max-w-64").style(
        f"background-color: {COLORS['surface']};"
    ):
        # Platform icon and status
        with ui.row().classes("full-width items-center q-mb-sm"):
            ui.icon("auto_stories" if post["platform"] == "xiaohongshu" else "public").classes(
                "q-mr-xs"
            )
            ui.label(post["platform"]).classes("text-caption text-secondary")
            ui.label(post["status"]).classes(
                f"q-ml-auto text-caption text-{COLORS['accent']}"
            )

        # Title
        ui.label(post["title"] or t("content.title")).classes(
            "text-subtitle2 q-mb-xs"
        ).props("line-clamp=2")

        # Preview
        preview_text = post["content"] or ""
        ui.label(
            preview_text[:50] + "..." if len(preview_text) > 50 else preview_text
        ).classes("text-caption text-secondary q-mb-sm").props("line-clamp=2")

        # Date
        if post.get("created_at"):
            ui.label(post["created_at"]).classes("text-caption text-grey")


def register() -> None:
    @ui.page("/content")
    async def content_page():
        set_active_nav("/content")
        page_layout(t("content.title"))

        # State management
        generated = {
            "post_id": None,
            "title": "",
            "content": "",
            "tags": [],
            "images": [],
        }
        selected_images: list[str] = []

        # Main container
        with ui.column().classes(
            "full-width q-pa-md"
        ).style("max-width: 1400px; margin: auto;"):

            # --- Responsive Column Layout ---
            with ui.row().classes("full-width q-gutter-md items-start flex-wrap"):

                # --- Left: Generation Form ---
                with ui.card().classes("q-pa-md").style(
                    f"background-color: {COLORS['surface']}; "
                    "flex: 1 1 280px; min-width: 280px; max-width: 360px;"
                ):
                    ui.label(t("content.generate")).classes(
                        "text-h6 q-mb-md"
                    )

                    # Topic input
                    topic_input = ui.input(
                        t("content.topic"),
                        placeholder=t("content.topic_placeholder"),
                    ).classes("full-width q-mb-sm").props("outlined")

                    # Platform select
                    platform_select = ui.select(
                        PLATFORMS,
                        value="xiaohongshu",
                        label=t("content.platform"),
                    ).classes("full-width q-mb-sm").props("outlined")

                    # Style select
                    style_select = ui.select(
                        STYLES,
                        value="tutorial",
                        label=t("content.style"),
                    ).classes("full-width q-mb-md").props("outlined")

                    # Auto-generate images section
                    ui.separator().classes("q-my-md")
                    ui.label(t("content.auto_generate_images")).classes(
                        "text-subtitle2 q-mb-sm"
                    )

                    auto_generate_checkbox = ui.checkbox(
                        t("content.auto_generate_images")
                    ).classes("q-mb-sm").props("color=primary")

                    image_count_select = ui.select(
                        [1, 2, 3, 4],
                        value=1,
                        label=t("content.image_count"),
                    ).classes("full-width q-mb-md").props("outlined")

                    # Status label
                    status_label = ui.label("").classes(
                        "text-caption text-secondary q-mb-sm"
                    )

                    # Generate button
                    gen_btn = ui.button(
                        t("content.generate"),
                        icon="auto_awesome",
                    ).props("color=primary full-width")

                    async def do_generate():
                        topic = topic_input.value.strip()
                        if not topic:
                            ui.notify(t("content.topic_placeholder"), type="warning")
                            return

                        platform = platform_select.value
                        style = style_select.value
                        auto_generate = auto_generate_checkbox.value
                        img_count = image_count_select.value

                        status_label.text = t("content.generating")
                        gen_btn.props("loading")

                        try:
                            pilot = get_pilot()
                            post_id, content, image_paths = await pilot.generate_content(
                                topic,
                                platform,
                                style,
                                auto_generate_images=auto_generate,
                                image_count=img_count,
                            )

                            generated["post_id"] = post_id
                            generated["title"] = content.title
                            generated["content"] = content.content
                            generated["tags"] = content.tags
                            generated["images"] = image_paths

                            # Update preview fields
                            title_edit.value = content.title
                            content_edit.value = content.content
                            tags_edit.value = " ".join(f"#{t}" for t in content.tags)

                            # Update selected images with auto-generated images
                            if image_paths:
                                selected_images.clear()
                                selected_images.extend(image_paths)
                                _refresh_image_preview()

                            status_label.text = (
                                f"{t('content.generated')} (Post ID: {post_id})"
                            )
                            ui.notify(t("content.generated"), type="positive")

                        except Exception as e:
                            status_label.text = f"{t('common.error')}: {e}"
                            ui.notify(f"{t('common.error')}: {e}", type="negative")
                            logger.error("Content generation error: %s", e)
                        finally:
                            gen_btn.props(remove="loading")

                    gen_btn.on_click(do_generate)

                # --- Center: Preview/Edit ---
                with ui.card().classes("q-pa-md").style(
                    f"background-color: {COLORS['surface']}; "
                    "flex: 2 1 320px; min-width: 320px;"
                ):
                    ui.label(t("content.preview_edit")).classes(
                        "text-h6 q-mb-md"
                    )

                    # Title input
                    title_edit = ui.input(t("content.title_label")).classes(
                        "full-width q-mb-sm"
                    ).props("outlined")

                    # Content textarea
                    content_edit = ui.textarea(t("content.content_label")).classes(
                        "full-width q-mb-sm"
                    ).props("rows=12 outlined")

                    # Tags input
                    tags_edit = ui.input(
                        t("content.tags"),
                        placeholder=t("content.tags_placeholder"),
                    ).classes("full-width q-mb-md").props("outlined")

                    # Platform preview (optional, shows platform-specific style hint)
                    with ui.card().classes("q-pa-sm q-mb-md").style(
                        f"background-color: {COLORS['background']}; border-left: 4px solid {COLORS['primary']};"
                    ):
                        ui.label("Platform Preview").classes("text-caption text-secondary")
                        platform_preview = ui.label("").classes("text-subtitle2")

                        def update_platform_preview():
                            platform = platform_select.value
                            platform_preview.text = f"Target: {platform} | Style: {style_select.value}"

                        platform_select.on_value_change(lambda e: update_platform_preview())
                        style_select.on_value_change(lambda e: update_platform_preview())
                        update_platform_preview()

                    # Action buttons
                    with ui.row().classes("full-width q-gutter-sm justify-end"):
                        approve_btn = ui.button(
                            t("content.approve"),
                            icon="check",
                            color="positive",
                        )
                        discard_btn = ui.button(
                            t("content.discard"),
                            icon="delete",
                            color="negative",
                        ).props("outline")

                        async def do_approve():
                            if not generated["post_id"]:
                                ui.notify("Generate content first", type="warning")
                                return

                            approve_btn.props("loading")
                            try:
                                pilot = get_pilot()
                                raw_tags = tags_edit.value.strip()
                                tag_list = (
                                    [
                                        t.strip().lstrip("#")
                                        for t in raw_tags.split("#")
                                        if t.strip()
                                    ]
                                    if raw_tags
                                    else []
                                )

                                update_kwargs = {
                                    "title": title_edit.value,
                                    "content": content_edit.value,
                                    "tags": json.dumps(tag_list, ensure_ascii=False),
                                    "status": "approved",
                                }

                                if selected_images:
                                    update_kwargs["images"] = json.dumps(
                                        selected_images, ensure_ascii=False
                                    )

                                await pilot.db.update_post(
                                    generated["post_id"], **update_kwargs
                                )

                                ui.notify(
                                    f"Post {generated['post_id']} {t('content.approve')}!",
                                    type="positive",
                                )

                                # Clear state
                                generated["post_id"] = None
                                generated["title"] = ""
                                generated["content"] = ""
                                generated["tags"] = []
                                generated["images"] = []
                                title_edit.value = ""
                                content_edit.value = ""
                                tags_edit.value = ""
                                selected_images.clear()
                                _refresh_image_preview()

                                # Refresh recent drafts
                                _refresh_recent_drafts()

                            finally:
                                approve_btn.props(remove="loading")

                        async def do_discard():
                            if not generated["post_id"]:
                                ui.notify("Nothing to discard", type="info")
                                return

                            async def confirm_discard():
                                pilot = get_pilot()
                                await pilot.db.delete_post(generated["post_id"])
                                ui.notify(t("content.discard"), type="info")
                                generated["post_id"] = None
                                title_edit.value = ""
                                content_edit.value = ""
                                tags_edit.value = ""
                                selected_images.clear()
                                _refresh_image_preview()
                                _refresh_recent_drafts()
                                dialog.close()

                            with ui.dialog() as dialog, ui.card():
                                ui.label("Are you sure you want to discard this post?")
                                with ui.row().classes("q-gutter-sm q-mt-sm"):
                                    ui.button(
                                        t("common.yes"),
                                        on_click=confirm_discard,
                                    ).props("color=negative")
                                    ui.button(
                                        t("common.cancel"),
                                        on_click=dialog.close,
                                    ).props("outline")
                            dialog.open()

                        approve_btn.on_click(do_approve)
                        discard_btn.on_click(do_discard)

                # --- Right: Image Area ---
                with ui.card().classes("q-pa-md").style(
                    f"background-color: {COLORS['surface']}; "
                    "flex: 1 1 280px; min-width: 280px; max-width: 360px;"
                ):
                    ui.label(t("content.images")).classes(
                        "text-h6 q-mb-md"
                    )

                    # Auto-generate indicator
                    auto_gen_indicator = ui.label("").classes(
                        "text-caption q-mb-sm"
                    )

                    def update_auto_gen_indicator():
                        if generated["images"]:
                            auto_gen_indicator.text = f"{len(generated['images'])} {t('content.generated')}"
                            auto_gen_indicator.classes("text-positive")
                        else:
                            auto_gen_indicator.text = ""

                    # Image tabs
                    with ui.tabs().classes("full-width q-mb-sm") as img_tabs:
                        upload_tab = ui.tab(t("content.upload_images"), icon="upload_file")

                    with ui.tab_panels(img_tabs, value=upload_tab).classes("full-width"):
                        with ui.tab_panel(upload_tab):
                            # Upload area
                            async def handle_upload(e):
                                images_dir = _get_images_dir()
                                fname = f"upload_{uuid.uuid4().hex[:8]}_{e.name}"
                                fpath = images_dir / fname
                                fpath.write_bytes(e.content.read())

                                if fpath not in selected_images:
                                    selected_images.append(str(fpath))
                                _refresh_image_preview()
                                ui.notify(f"Uploaded: {e.name}", type="positive")

                            ui.upload(
                                label=t("content.upload_images"),
                                on_upload=handle_upload,
                                auto_upload=True,
                                multiple=True,
                            ).classes("full-width").props('accept="image/*"')

                    # Selected images preview
                    ui.separator().classes("q-my-md")
                    ui.label(t("content.selected_images")).classes(
                        "text-subtitle2 q-mb-sm"
                    )

                    image_preview_container = ui.row().classes(
                        "q-gutter-sm flex-wrap"
                    )

                    def _refresh_image_preview():
                        image_preview_container.clear()
                        with image_preview_container:
                            if not selected_images:
                                ui.label(t("common.none")).classes("text-caption text-grey")
                            else:
                                for img_path in list(selected_images):
                                    with ui.card().classes("q-pa-xs").style(
                                        "border-radius: 8px;"
                                    ):
                                        ui.image(img_path).classes(
                                            "w-20 h-20 object-cover"
                                        ).style("border-radius: 6px;")

                                        def make_remove(path=img_path):
                                            return lambda: _remove_image(path)

                                        ui.button(
                                            icon="close",
                                            on_click=make_remove(),
                                        ).props("flat dense round size=xs color=negative")

                        update_auto_gen_indicator()

                    def _remove_image(path: str):
                        if path in selected_images:
                            selected_images.remove(path)
                            _refresh_image_preview()

                    _refresh_image_preview()

            # --- Recent Drafts Section (Bottom) ---
            ui.separator().classes("q-my-lg")
            with ui.column().classes("full-width"):
                ui.label(t("content.recent_drafts")).classes(
                    "text-h6 q-mb-md"
                )

                recent_drafts_container = ui.row().classes(
                    "full-width q-gutter-sm scroll-x"
                ).style("overflow-x: auto;")

                async def _refresh_recent_drafts():
                    recent_drafts_container.clear()
                    with recent_drafts_container:
                        try:
                            pilot = get_pilot()
                            posts = await pilot.db.get_posts(
                                platform=None,
                                status="draft",
                                limit=5,
                            )

                            if not posts:
                                ui.label("No recent drafts").classes(
                                    "text-caption text-grey q-px-md"
                                )
                            else:
                                for post in posts:
                                    _create_draft_card(post)

                        except Exception as e:
                            logger.error("Failed to load recent drafts: %s", e)
                            ui.label("Failed to load drafts").classes(
                                "text-caption text-red q-px-md"
                            )

                # Load recent drafts on page load
                await _refresh_recent_drafts()
