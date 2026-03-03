"""Click-to-enlarge image lightbox component."""

from __future__ import annotations

from nicegui import ui

from content_pilot.gui.constants import COLORS
from content_pilot.gui.i18n import t


def clickable_image(src: str, classes: str = "", style: str = "") -> ui.image:
    """Create an image that opens a full-size lightbox dialog on click.

    Args:
        src: Image source URL or path
        classes: CSS classes for the thumbnail image
        style: Inline CSS style for the thumbnail image

    Returns:
        The thumbnail ui.image element
    """
    base_style = "cursor: pointer;"
    if style:
        base_style += f" {style}"

    img = ui.image(src).classes(classes).style(base_style)
    img.tooltip(t("common.click_to_enlarge"))

    def open_lightbox():
        with ui.dialog() as dialog, ui.card().classes("q-pa-md").style(
            f"background: {COLORS['surface']}; max-width: 90vw; max-height: 90vh;"
        ):
            ui.image(src).style(
                "max-width: 80vw; max-height: 75vh; object-fit: contain;"
            )
            ui.button(
                t("common.close"),
                icon="close",
                on_click=dialog.close,
            ).props("flat dense").classes("q-mt-sm self-end")
        dialog.open()

    img.on("click", lambda: open_lightbox())
    return img
