"""Content generation page: topic input, AI generation, preview/edit, image selection."""

from __future__ import annotations

import json
import logging

from nicegui import ui

from content_pilot.gui.components.image_picker import image_picker
from content_pilot.gui.components.nav import page_layout
from content_pilot.gui.constants import PLATFORMS, STYLES
from content_pilot.gui.main import get_pilot

logger = logging.getLogger(__name__)


def register() -> None:
    @ui.page("/content")
    async def content_page():
        page_layout("Content Generation")

        # State
        generated = {"post_id": None, "title": "", "content": "", "tags": []}
        selected_images: list[str] = []

        with ui.column().classes(
            "full-width q-pa-md"
        ).style("max-width: 1200px; margin: auto;"):
            # --- Left: Input form ---
            with ui.row().classes("full-width q-gutter-md items-start"):
                with ui.card().classes("q-pa-md").style(
                    "flex: 1; min-width: 350px;"
                ):
                    ui.label("Generate Content").classes(
                        "text-h6 q-mb-sm"
                    )
                    topic_input = ui.input(
                        "Topic",
                        placeholder="e.g. Python async programming tips",
                    ).classes("full-width").props("outlined")
                    platform_select = ui.select(
                        PLATFORMS, value="xiaohongshu", label="Platform"
                    ).classes("full-width").props("outlined")
                    style_select = ui.select(
                        STYLES, value="tutorial", label="Style"
                    ).classes("full-width").props("outlined")
                    status_label = ui.label("").classes("text-caption")

                    async def do_generate():
                        topic = topic_input.value.strip()
                        if not topic:
                            ui.notify(
                                "Please enter a topic", type="warning"
                            )
                            return
                        platform = platform_select.value
                        style = style_select.value
                        status_label.text = "Generating content..."
                        gen_btn.props("loading")
                        try:
                            pilot = get_pilot()
                            post_id, result = await pilot.generate_content(
                                topic, platform, style
                            )
                            generated["post_id"] = post_id
                            generated["title"] = result.title
                            generated["content"] = result.content
                            generated["tags"] = result.tags
                            # Update preview fields
                            title_edit.value = result.title
                            content_edit.value = result.content
                            tags_edit.value = " ".join(
                                f"#{t}" for t in result.tags
                            )
                            status_label.text = (
                                f"Generated! (Post ID: {post_id})"
                            )
                            ui.notify(
                                "Content generated", type="positive"
                            )
                        except Exception as e:
                            status_label.text = f"Error: {e}"
                            ui.notify(
                                f"Generation failed: {e}", type="negative"
                            )
                            logger.error(
                                "Content generation error: %s", e
                            )
                        finally:
                            gen_btn.props(remove="loading")

                    gen_btn = ui.button(
                        "Generate",
                        icon="auto_awesome",
                        on_click=do_generate,
                    ).props("color=primary").classes("q-mt-sm")

                # --- Right: Preview / Edit ---
                with ui.card().classes("q-pa-md").style(
                    "flex: 1; min-width: 350px;"
                ):
                    ui.label("Preview & Edit").classes(
                        "text-h6 q-mb-sm"
                    )
                    title_edit = ui.input("Title").classes(
                        "full-width"
                    ).props("outlined")
                    content_edit = ui.textarea("Content").classes(
                        "full-width"
                    ).props("rows=10 outlined")
                    tags_edit = ui.input(
                        "Tags", placeholder="#tag1 #tag2 #tag3"
                    ).classes("full-width").props("outlined")

                    with ui.row().classes("q-mt-sm q-gutter-sm"):

                        async def do_approve():
                            if not generated["post_id"]:
                                ui.notify(
                                    "Generate content first",
                                    type="warning",
                                )
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
                                    "tags": json.dumps(
                                        tag_list, ensure_ascii=False
                                    ),
                                    "status": "approved",
                                }
                                if selected_images:
                                    update_kwargs["images"] = json.dumps(
                                        selected_images,
                                        ensure_ascii=False,
                                    )
                                await pilot.db.update_post(
                                    generated["post_id"], **update_kwargs
                                )
                                ui.notify(
                                    f"Post {generated['post_id']} approved!",
                                    type="positive",
                                )
                                generated["post_id"] = None
                                title_edit.value = ""
                                content_edit.value = ""
                                tags_edit.value = ""
                                selected_images.clear()
                            finally:
                                approve_btn.props(remove="loading")

                        async def do_discard():
                            if not generated["post_id"]:
                                ui.notify(
                                    "Nothing to discard", type="info"
                                )
                                return

                            async def confirm_discard():
                                pilot = get_pilot()
                                await pilot.db.delete_post(
                                    generated["post_id"]
                                )
                                ui.notify("Discarded", type="info")
                                generated["post_id"] = None
                                title_edit.value = ""
                                content_edit.value = ""
                                tags_edit.value = ""
                                selected_images.clear()
                                dialog.close()

                            with ui.dialog() as dialog, ui.card():
                                ui.label(
                                    "Are you sure you want to discard this post?"
                                )
                                with ui.row().classes("q-gutter-sm q-mt-sm"):
                                    ui.button(
                                        "Yes, discard",
                                        on_click=confirm_discard,
                                    ).props("color=negative")
                                    ui.button(
                                        "Cancel",
                                        on_click=dialog.close,
                                    ).props("outline")
                            dialog.open()

                        approve_btn = ui.button(
                            "Approve",
                            icon="check",
                            on_click=do_approve,
                        ).props("color=positive")
                        ui.button(
                            "Discard",
                            icon="delete",
                            on_click=do_discard,
                        ).props("color=negative outline")

            # --- Image picker ---
            with ui.card().classes("q-pa-md q-mt-md full-width"):
                ui.label("Images").classes("text-h6 q-mb-sm")
                image_picker(selected_images)
