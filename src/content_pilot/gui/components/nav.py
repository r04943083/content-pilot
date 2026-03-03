"""Left-side navigation drawer component."""

from nicegui import ui


def nav_drawer() -> None:
    """Render the left navigation drawer shared across all pages."""
    with ui.left_drawer(value=True).classes("bg-dark text-white") as drawer:
        ui.label("Content Pilot").classes("text-h5 q-pa-md text-weight-bold")
        ui.separator()

        items = [
            ("Dashboard", "dashboard", "/"),
            ("Accounts", "manage_accounts", "/accounts"),
            ("Content", "edit_note", "/content"),
            ("Publish", "publish", "/publish"),
            ("Schedule", "schedule", "/schedule"),
            ("Settings", "settings", "/settings"),
        ]
        for label, icon, path in items:
            ui.link(label, path).classes(
                "text-white no-underline q-pa-sm q-pl-md flex items-center gap-sm"
            ).style("display: flex; align-items: center; gap: 8px; font-size: 1rem;")

    return drawer


def page_layout(title: str):
    """Common page layout with header and nav drawer."""
    ui.colors(primary="#1976D2")
    with ui.header().classes("bg-primary text-white items-center"):
        ui.button(icon="menu", on_click=lambda: drawer.toggle()).props("flat color=white")
        ui.label(title).classes("text-h6")
    drawer = nav_drawer()
