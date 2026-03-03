"""Left-side navigation drawer component."""

from nicegui import app, ui


def nav_drawer() -> ui.left_drawer:
    """Render the left navigation drawer shared across all pages."""
    current_path = app.storage.tab.get("__nicegui_page_path__", "/")

    with ui.left_drawer(value=True).classes(
        "bg-dark text-white q-pa-none"
    ) as drawer:
        # Logo area
        with ui.row().classes(
            "items-center q-pa-md q-mb-sm no-wrap"
        ).style("border-bottom: 1px solid rgba(255,255,255,0.1);"):
            ui.icon("rocket_launch", size="sm").classes("text-primary")
            ui.label("Content Pilot").classes(
                "text-h6 text-weight-bold q-ml-sm"
            )

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
            bg = "bg-primary" if is_active else ""
            with ui.link(target=path).classes(
                f"no-underline full-width q-pa-sm q-pl-md {bg}"
            ).style(
                "display: flex; align-items: center; gap: 12px;"
                "font-size: 1rem; border-radius: 4px; margin: 2px 8px;"
                "transition: background 0.2s;"
                + ("" if is_active else "color: rgba(255,255,255,0.8);")
            ):
                ui.icon(icon, size="sm").classes(
                    "text-white" if is_active else "text-grey-5"
                )
                ui.label(label).classes(
                    "text-white text-weight-medium" if is_active else "text-grey-3"
                )

    return drawer


def page_layout(title: str):
    """Common page layout with header and nav drawer."""
    ui.colors(primary="#1976D2")
    drawer = nav_drawer()
    with ui.header().classes("bg-primary text-white items-center"):
        ui.button(icon="menu", on_click=drawer.toggle).props(
            "flat color=white"
        )
        ui.label(title).classes("text-h6")
