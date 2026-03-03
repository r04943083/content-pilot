"""Image picker component: AI code-generated cards, web search, and local upload."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

import httpx
from nicegui import events, ui

from content_pilot.config import get_settings
from content_pilot.content.card_templates import CARD_STYLES, DEFAULT_STYLE_MAP
from content_pilot.gui.main import get_pilot

logger = logging.getLogger(__name__)


def _get_images_dir() -> Path:
    data_dir = Path(get_settings().general.data_dir).resolve()
    images_dir = data_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    return images_dir


def image_picker(selected_images: list[str]) -> None:
    """Render image picker with three tabs: Code-Generated Cards, Web Search, Upload.

    selected_images is a mutable list that will be filled with chosen image paths.
    """

    def _add_image(path: str):
        if path not in selected_images:
            selected_images.append(path)
            _refresh_preview()

    def _remove_image(path: str):
        if path in selected_images:
            selected_images.remove(path)
            _refresh_preview()

    preview_container = None

    def _refresh_preview():
        if preview_container is None:
            return
        preview_container.clear()
        with preview_container:
            if not selected_images:
                ui.label("No images selected").classes("text-grey")
            else:
                with ui.row().classes("q-gutter-sm flex-wrap"):
                    for img_path in list(selected_images):
                        with ui.card().classes("q-pa-xs").style(
                            "border-radius: 8px;"
                        ):
                            ui.image(img_path).classes(
                                "w-24 h-24 object-cover"
                            ).style("border-radius: 6px;")

                            def make_remove(path=img_path):
                                return lambda: _remove_image(path)

                            ui.button(
                                icon="close", on_click=make_remove()
                            ).props(
                                "flat dense round size=xs color=red"
                            )

    with ui.tabs().classes("full-width") as tabs:
        ai_tab = ui.tab("代码生成图卡", icon="auto_awesome")
        search_tab = ui.tab("Web Search", icon="image_search")
        upload_tab = ui.tab("Upload", icon="upload_file")

    with ui.tab_panels(tabs, value=ai_tab).classes("full-width"):
        # --- Code-Generated Card tab ---
        with ui.tab_panel(ai_tab):
            ui.label("卡片风格").classes("text-caption q-mb-xs")
            card_style = ui.radio(
                options={k: v["name"] for k, v in CARD_STYLES.items()},
                value="quote",
            ).classes("q-mb-md")

            ui.label("标题").classes("text-caption q-mb-xs")
            card_title = ui.input(
                placeholder="输入标题...",
            ).classes("full-width").props("outlined dense")

            ui.label("摘要").classes("text-caption q-mb-xs q-mt-sm")
            card_summary = ui.textarea(
                placeholder="输入内容摘要...",
            ).classes("full-width").props("outlined dense autogrow")

            ui.label("标签（逗号分隔）").classes("text-caption q-mb-xs q-mt-sm")
            card_tags = ui.input(
                placeholder="标签1, 标签2, ...",
            ).classes("full-width").props("outlined dense")

            card_status = ui.label("").classes("text-caption q-mt-sm")

            async def gen_card_image():
                title = card_title.value.strip()
                summary = card_summary.value.strip()
                if not title:
                    ui.notify("请输入标题", type="warning")
                    return
                if not summary:
                    ui.notify("请输入摘要", type="warning")
                    return

                tags = [
                    t.strip()
                    for t in card_tags.value.split(",")
                    if t.strip()
                ]

                card_status.text = "正在生成图卡..."
                card_gen_btn.props("loading")
                try:
                    pilot = get_pilot()
                    img_bytes = await pilot.generator.generate_image_from_code(
                        title=title,
                        summary=summary,
                        tags=tags,
                        style=card_style.value,
                    )
                    if img_bytes:
                        images_dir = _get_images_dir()
                        fname = f"card_{uuid.uuid4().hex[:8]}.png"
                        fpath = images_dir / fname
                        fpath.write_bytes(img_bytes)
                        _add_image(str(fpath))
                        card_status.text = "图卡生成成功！"
                        ui.notify("图卡已生成", type="positive")
                    else:
                        card_status.text = "生成失败（检查 AI 配置或 Playwright 安装）"
                        ui.notify("图卡生成失败", type="negative")
                except Exception as e:
                    card_status.text = f"错误: {e}"
                    logger.error("Card generation error: %s", e)
                finally:
                    card_gen_btn.props(remove="loading")

            card_gen_btn = ui.button(
                "生成图卡",
                icon="auto_awesome",
                on_click=gen_card_image,
            ).props("color=primary").classes("q-mt-md")

        # --- Web Search tab ---
        with ui.tab_panel(search_tab):
            search_query = ui.input(
                "Search query",
                placeholder="e.g. sunset beach",
            ).classes("full-width").props("outlined")
            search_results_container = ui.row().classes(
                "q-gutter-sm flex-wrap"
            )

            async def do_search():
                query = search_query.value.strip()
                if not query:
                    ui.notify(
                        "Please enter a search query",
                        type="warning",
                    )
                    return
                search_results_container.clear()
                with search_results_container:
                    ui.label("Searching...").classes("text-caption")
                try:
                    urls = await search_unsplash(query, count=6)
                    search_results_container.clear()
                    with search_results_container:
                        if not urls:
                            ui.label("No results found").classes(
                                "text-grey"
                            )
                        for url in urls:

                            async def download_and_add(
                                img_url=url,
                            ):
                                path = await download_image(
                                    img_url
                                )
                                if path:
                                    _add_image(path)
                                    ui.notify(
                                        "Image added",
                                        type="positive",
                                    )

                            with ui.card().classes(
                                "q-pa-xs cursor-pointer"
                            ).style("border-radius: 8px;"):
                                ui.image(url).classes(
                                    "w-24 h-24 object-cover"
                                ).style("border-radius: 6px;")
                                ui.button(
                                    "Add",
                                    icon="add",
                                    on_click=download_and_add,
                                ).props(
                                    "flat dense color=primary"
                                )
                except Exception as e:
                    search_results_container.clear()
                    with search_results_container:
                        ui.label(f"Search error: {e}").classes(
                            "text-red"
                        )

            ui.button(
                "Search", icon="search", on_click=do_search
            ).props("color=primary")

        # --- Upload tab ---
        with ui.tab_panel(upload_tab):

            async def handle_upload(
                e: events.UploadEventArguments,
            ):
                images_dir = _get_images_dir()
                fname = (
                    f"upload_{uuid.uuid4().hex[:8]}_{e.name}"
                )
                fpath = images_dir / fname
                fpath.write_bytes(e.content.read())
                _add_image(str(fpath))
                ui.notify(
                    f"Uploaded: {e.name}", type="positive"
                )

            ui.upload(
                label="Drop images here or click to upload",
                on_upload=handle_upload,
                auto_upload=True,
                multiple=True,
            ).classes("full-width").props('accept="image/*"')

    # --- Selected images preview ---
    ui.label("Selected Images").classes(
        "text-subtitle1 q-mt-md"
    )
    preview_container = ui.row().classes(
        "q-gutter-sm flex-wrap q-mb-md"
    )
    _refresh_preview()


async def search_unsplash(
    query: str, count: int = 6
) -> list[str]:
    """Search Unsplash Source for images. Returns list of image URLs."""
    urls = []
    for i in range(count):
        url = f"https://source.unsplash.com/400x400/?{query}&sig={uuid.uuid4().hex[:6]}"
        urls.append(url)
    return urls


async def download_image(url: str) -> str | None:
    """Download an image URL to data/images/, return local path."""
    try:
        images_dir = _get_images_dir()
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=30
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            ext = "jpg"
            ct = resp.headers.get("content-type", "")
            if "png" in ct:
                ext = "png"
            elif "webp" in ct:
                ext = "webp"
            fname = f"web_{uuid.uuid4().hex[:8]}.{ext}"
            fpath = images_dir / fname
            fpath.write_bytes(resp.content)
            return str(fpath)
    except Exception as e:
        logger.error(
            "Failed to download image %s: %s", url, e
        )
        return None
