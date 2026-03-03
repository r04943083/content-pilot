"""Image picker component: AI generation, web search, and local upload."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

import httpx
from nicegui import events, ui

from content_pilot.gui.main import get_pilot

logger = logging.getLogger(__name__)

IMAGES_DIR = Path("data/images")


def _ensure_images_dir() -> Path:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    return IMAGES_DIR


def image_picker(selected_images: list[str]) -> None:
    """Render image picker with three tabs: AI Generate, Web Search, Upload.

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
                        with ui.card().classes("q-pa-xs"):
                            ui.image(img_path).classes("w-24 h-24 object-cover")
                            p = img_path  # capture for closure

                            def make_remove(path=p):
                                return lambda: _remove_image(path)

                            ui.button(
                                icon="close", on_click=make_remove()
                            ).props("flat dense round size=xs color=red")

    with ui.tabs().classes("full-width") as tabs:
        ai_tab = ui.tab("AI Generate", icon="auto_awesome")
        search_tab = ui.tab("Web Search", icon="image_search")
        upload_tab = ui.tab("Upload", icon="upload_file")

    with ui.tab_panels(tabs, value=ai_tab).classes("full-width"):
        # --- AI Generate tab ---
        with ui.tab_panel(ai_tab):
            ai_prompt = ui.input("Image prompt", placeholder="Describe the image...").classes(
                "full-width"
            )
            ai_status = ui.label("").classes("text-caption")

            async def gen_ai_image():
                prompt = ai_prompt.value.strip()
                if not prompt:
                    ui.notify("Please enter a prompt", type="warning")
                    return
                ai_status.text = "Generating image with DALL-E..."
                try:
                    pilot = get_pilot()
                    img_bytes = await pilot.generator.generate_image(prompt)
                    if img_bytes:
                        _ensure_images_dir()
                        fname = f"ai_{uuid.uuid4().hex[:8]}.png"
                        fpath = IMAGES_DIR / fname
                        fpath.write_bytes(img_bytes)
                        _add_image(str(fpath))
                        ai_status.text = "Image generated!"
                        ui.notify("Image generated", type="positive")
                    else:
                        ai_status.text = "Generation failed (check OpenAI API key)"
                        ui.notify("Image generation failed", type="negative")
                except Exception as e:
                    ai_status.text = f"Error: {e}"
                    logger.error("AI image generation error: %s", e)

            ui.button("Generate", icon="auto_awesome", on_click=gen_ai_image).props(
                "color=primary"
            )

        # --- Web Search tab ---
        with ui.tab_panel(search_tab):
            search_query = ui.input(
                "Search query", placeholder="e.g. sunset beach"
            ).classes("full-width")
            search_results_container = ui.row().classes("q-gutter-sm flex-wrap")

            async def do_search():
                query = search_query.value.strip()
                if not query:
                    ui.notify("Please enter a search query", type="warning")
                    return
                search_results_container.clear()
                with search_results_container:
                    ui.label("Searching...").classes("text-caption")
                try:
                    urls = await search_unsplash(query, count=6)
                    search_results_container.clear()
                    with search_results_container:
                        if not urls:
                            ui.label("No results found").classes("text-grey")
                        for url in urls:
                            u = url  # capture

                            async def download_and_add(img_url=u):
                                path = await download_image(img_url)
                                if path:
                                    _add_image(path)
                                    ui.notify("Image added", type="positive")

                            with ui.card().classes("q-pa-xs cursor-pointer"):
                                ui.image(url).classes("w-24 h-24 object-cover")
                                ui.button(
                                    "Add", icon="add", on_click=download_and_add
                                ).props("flat dense color=primary")
                except Exception as e:
                    search_results_container.clear()
                    with search_results_container:
                        ui.label(f"Search error: {e}").classes("text-red")

            ui.button("Search", icon="search", on_click=do_search).props("color=primary")

        # --- Upload tab ---
        with ui.tab_panel(upload_tab):

            async def handle_upload(e: events.UploadEventArguments):
                _ensure_images_dir()
                fname = f"upload_{uuid.uuid4().hex[:8]}_{e.name}"
                fpath = IMAGES_DIR / fname
                fpath.write_bytes(e.content.read())
                _add_image(str(fpath))
                ui.notify(f"Uploaded: {e.name}", type="positive")

            ui.upload(
                label="Drop images here or click to upload",
                on_upload=handle_upload,
                auto_upload=True,
                multiple=True,
            ).classes("full-width").props('accept="image/*"')

    # --- Selected images preview ---
    ui.label("Selected Images").classes("text-subtitle1 q-mt-md")
    preview_container = ui.row().classes("q-gutter-sm flex-wrap q-mb-md")
    _refresh_preview()


async def search_unsplash(query: str, count: int = 6) -> list[str]:
    """Search Unsplash Source for images. Returns list of image URLs."""
    urls = []
    for i in range(count):
        # Unsplash Source URL — no API key needed
        url = f"https://source.unsplash.com/400x400/?{query}&sig={uuid.uuid4().hex[:6]}"
        urls.append(url)
    return urls


async def download_image(url: str) -> str | None:
    """Download an image URL to data/images/, return local path."""
    try:
        _ensure_images_dir()
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            ext = "jpg"
            ct = resp.headers.get("content-type", "")
            if "png" in ct:
                ext = "png"
            elif "webp" in ct:
                ext = "webp"
            fname = f"web_{uuid.uuid4().hex[:8]}.{ext}"
            fpath = IMAGES_DIR / fname
            fpath.write_bytes(resp.content)
            return str(fpath)
    except Exception as e:
        logger.error("Failed to download image %s: %s", url, e)
        return None
