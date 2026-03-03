"""Left-side navigation drawer component."""

from __future__ import annotations

import logging

from nicegui import app, ui

from content_pilot.gui.constants import COLORS

logger = logging.getLogger(__name__)

__all__ = ["nav_drawer", "page_layout", "set_active_nav", "get_current_path"]


def set_active_nav(path: str) -> None:
    """Store the current path for navigation highlighting.

    This should be called by each page to ensure the correct nav item
    is highlighted as active.

    Args:
        path: The current page path (e.g., "/", "/accounts")
    """
    try:
        app.storage.client["__nav_current_path__"] = path
    except (AttributeError, RuntimeError) as e:
        logger.debug(f"Could not set nav path: {e}")


def get_current_path() -> str:
    """Get the current page path.

    Returns the stored path or "/" as default.
    """
    try:
        return app.storage.client.get("__nav_current_path__", "/")
    except (AttributeError, RuntimeError):
        return "/"


def get_logo_svg() -> str:
    """Return the product logo SVG inline."""
    return '''<svg width="28" height="28" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="16" cy="16" r="14" fill="#6366F1" fill-opacity="0.2"/>
  <path d="M16 4C16 4 12 10 12 16C12 18.5 13.5 20.5 16 22C18.5 20.5 20 18.5 20 16C20 10 16 4 16 4Z" fill="#6366F1"/>
  <circle cx="16" cy="14" r="2.5" fill="#FFFFFF"/>
  <path d="M12 16L9 20L11 18L12 16Z" fill="#4F46E5"/>
  <path d="M20 16L23 20L21 18L20 16Z" fill="#4F46E5"/>
  <path d="M16 22C14.5 23.5 14 26 16 28C18 26 17.5 23.5 16 22Z" fill="#F59E0B"/>
  <rect x="18" y="18" width="8" height="10" rx="1" fill="#10B981" fill-opacity="0.8"/>
  <line x1="20" y1="21" x2="24" y2="21" stroke="white" stroke-width="1" stroke-linecap="round"/>
  <line x1="20" y1="23.5" x2="24" y2="23.5" stroke="white" stroke-width="1" stroke-linecap="round"/>
  <line x1="20" y1="26" x2="23" y2="26" stroke="white" stroke-width="1" stroke-linecap="round"/>
</svg>'''


def on_language_change(lang: str) -> None:
    """Handle language selection change.

    Args:
        lang: Selected language code ("zh" or "en")
    """
    try:
        from content_pilot.gui.i18n import set_language

        # Map display names to language codes
        lang_map = {
            "English": "en_US",
            "中文": "zh_CN",
        }
        code = lang_map.get(lang, "zh_CN")
        set_language(code)
        # Refresh the page to apply translations
        ui.navigate.to(ui.context.client.location.pathname)
        logger.info(f"Language changed to: {code}")
    except Exception as e:
        logger.warning(f"Could not change language: {e}")


def nav_drawer() -> ui.left_drawer:
    """Render the left navigation drawer shared across all pages."""
    current_path = get_current_path()

    with ui.left_drawer(value=True).classes(
        "bg-dark text-white q-pa-none"
    ).style(f"background: {COLORS['background']} !important;") as drawer:
        # Logo area with SVG
        with ui.row().classes(
            "items-center q-pa-md q-mb-sm no-wrap"
        ).style("border-bottom: 1px solid rgba(255,255,255,0.1);"):
            # Logo SVG
            ui.html(get_logo_svg()).classes("q-mr-sm")
            ui.label("Content Pilot").classes(
                "text-h6 text-weight-bold"
            ).style(f"color: {COLORS['primary']};")

        # Navigation items
        items = [
            ("Dashboard", "dashboard", "/"),
            ("Accounts", "manage_accounts", "/accounts"),
            ("Content", "edit_note", "/content"),
            ("Publish", "publish", "/publish"),
            ("Schedule", "schedule", "/schedule"),
            ("Settings", "settings", "/settings"),
        ]

        for label, icon, path in items:
            is_active = current_path == path
            active_bg = f"background: {COLORS['primary']};"
            active_text = f"color: {COLORS['text_primary']};"
            inactive_style = f"color: {COLORS['text_secondary']};"

            item_style = (
                active_bg + active_text
                if is_active
                else inactive_style
            )

            with ui.link(target=path).classes(
                "no-underline full-width q-pa-sm q-pl-md"
            ).style(
                "display: flex; align-items: center; gap: 12px;"
                "font-size: 1rem; border-radius: 4px; margin: 2px 8px;"
                "transition: background 0.2s;"
            ) as link:
                # Apply active/inactive styles
                link.style(item_style)

                # Icon color based on state
                icon_color = COLORS['text_primary'] if is_active else COLORS['text_secondary']
                ui.icon(icon, size="sm").style(f"color: {icon_color};")

                # Label style based on state
                label_color = COLORS['text_primary'] if is_active else COLORS['text_secondary']
                ui.label(label).style(
                    f"color: {label_color}; "
                    "font-weight: " + ("600" if is_active else "400") + ";"
                )

            # Hover effect via JavaScript
            link.on(
                "mouseover",
                js=f'this.style.background = "{COLORS["primary"]}" if !this.classList.contains("active") else null'
            )
            link.on(
                "mouseout",
                js=f'this.style.background = "{COLORS["background"]}" if !this.classList.contains("active") else null'
            )

        # Spacer to push language switcher to bottom
        ui.spacer()

        # Language switcher at bottom
        with ui.row().classes(
            "q-pa-md full-width items-center q-gutter-sm"
        ).style("border-top: 1px solid rgba(255,255,255,0.1);"):
            ui.icon("language").style(f"color: {COLORS['text_secondary']};")

            # Get current language
            try:
                from content_pilot.gui.i18n import get_language, LANGUAGE_NAMES
                current_lang = get_language()
                current_display = LANGUAGE_NAMES.get(current_lang, "中文")
            except Exception:
                current_display = "中文"

            ui.select(
                ["English", "中文"],
                value=current_display,
                on_change=lambda e: on_language_change(e.value)
            ).props("dark dense outlined").style(
                f"background: {COLORS['surface']}; "
                f"color: {COLORS['text_primary']}; "
                "border-color: rgba(255,255,255,0.2);"
            ).classes("text-sm")

    return drawer


def page_layout(title: str):
    """Common page layout with header and nav drawer.

    Args:
        title: Page title displayed in the header
    """
    # Set primary color for the app
    ui.colors(primary=COLORS["primary"])

    # Render navigation drawer
    drawer = nav_drawer()

    # Header with hamburger menu
    with ui.header().classes("items-center").style(
        f"background: {COLORS['primary']}; color: {COLORS['text_primary']};"
    ):
        ui.button(
            icon="menu",
            on_click=drawer.toggle
        ).props("flat color=white")
        ui.label(title).classes("text-h6")
