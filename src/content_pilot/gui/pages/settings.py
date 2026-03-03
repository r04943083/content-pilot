"""Settings page: AI provider, API keys, safety settings, appearance."""

from __future__ import annotations

import logging
from pathlib import Path

from nicegui import ui

from content_pilot.config import get_settings
from content_pilot.gui.components.nav import page_layout, set_active_nav
from content_pilot.gui.constants import COLORS
from content_pilot.gui.i18n import t, set_language, get_language, LANGUAGE_NAMES

logger = logging.getLogger(__name__)

PROVIDERS = ["claude", "openai", "qwen", "glm"]


def register() -> None:
    @ui.page("/settings")
    async def settings_page():
        set_active_nav("/settings")

        settings = get_settings()

        with ui.column().classes(
            "full-width q-pa-md"
        ).style("max-width: 1200px; margin: auto;"):
            ui.label(t("settings.title")).classes(
                "text-h5 q-mb-md"
            ).style(f"color: {COLORS['text_primary']};")

            # Tabbed interface
            with ui.tabs().classes("full-width").props("dark") as tabs:
                ai_tab = ui.tab(t("settings.ai_provider"), icon="smart_toy")
                models_tab = ui.tab(t("settings.model_settings"), icon="tune")
                safety_tab = ui.tab(t("settings.safety"), icon="security")
                appearance_tab = ui.tab(t("settings.appearance"), icon="palette")
                about_tab = ui.tab(t("settings.about"), icon="info")

            with ui.tab_panels(tabs, value=ai_tab).classes("full-width q-mt-md").props("dark"):
                # --- AI Provider tab ---
                with ui.tab_panel(ai_tab):
                    with ui.card().classes("q-pa-md full-width").style(
                        f"background: {COLORS['surface']}; border-radius: 12px;"
                    ):
                        provider_select = ui.select(
                            PROVIDERS,
                            value=settings.ai.provider,
                            label=t("settings.provider"),
                        ).classes("full-width").props("outlined dark")

                        ui.label(t("settings.api_keys")).classes(
                            "text-subtitle1 q-mt-md q-mb-sm"
                        ).style(f"color: {COLORS['text_primary']};")

                        anthropic_key = ui.input(
                            "Anthropic API Key",
                            value=settings.ai.anthropic_api_key,
                            password=True,
                            password_toggle_button=True,
                        ).classes("full-width").props("outlined dark")

                        openai_key = ui.input(
                            "OpenAI API Key",
                            value=settings.ai.openai_api_key,
                            password=True,
                            password_toggle_button=True,
                        ).classes("full-width").props("outlined dark")

                        qwen_key = ui.input(
                            "Qwen API Key",
                            value=settings.ai.qwen_api_key,
                            password=True,
                            password_toggle_button=True,
                        ).classes("full-width").props("outlined dark")

                        glm_key = ui.input(
                            "GLM API Key",
                            value=settings.ai.glm_api_key,
                            password=True,
                            password_toggle_button=True,
                        ).classes("full-width").props("outlined dark")

                        # Test connection button
                        async def test_connection():
                            test_btn.props("loading")
                            try:
                                # Simple test - just check if key is set
                                provider = provider_select.value
                                key_map = {
                                    "claude": anthropic_key.value,
                                    "openai": openai_key.value,
                                    "qwen": qwen_key.value,
                                    "glm": glm_key.value,
                                }
                                if key_map.get(provider):
                                    ui.notify(
                                        f"API key configured for {provider}",
                                        type="positive"
                                    )
                                else:
                                    ui.notify(
                                        f"No API key set for {provider}",
                                        type="warning"
                                    )
                            finally:
                                test_btn.props(remove="loading")

                        test_btn = ui.button(
                            t("settings.test_connection"),
                            icon="wifi_find",
                            on_click=test_connection
                        ).props(f"color={COLORS['primary']} outline").classes("q-mt-md")

                # --- Models tab ---
                with ui.tab_panel(models_tab):
                    with ui.card().classes("q-pa-md full-width").style(
                        f"background: {COLORS['surface']}; border-radius: 12px;"
                    ):
                        claude_model = ui.input(
                            "Claude Model",
                            value=settings.ai.claude_model
                        ).classes("full-width").props("outlined dark")

                        openai_model = ui.input(
                            "OpenAI Model",
                            value=settings.ai.openai_model
                        ).classes("full-width").props("outlined dark")

                        qwen_model = ui.input(
                            "Qwen Model",
                            value=settings.ai.qwen_model
                        ).classes("full-width").props("outlined dark")

                        glm_model = ui.input(
                            "GLM Model",
                            value=settings.ai.glm_model
                        ).classes("full-width").props("outlined dark")

                        temperature = ui.slider(
                            min=0, max=2, step=0.1, value=settings.ai.temperature
                        ).classes("full-width")
                        ui.label().bind_text_from(
                            temperature,
                            "value",
                            backward=lambda v: f"{t('settings.temperature')}: {v}",
                        ).style(f"color: {COLORS['text_secondary']};")

                        max_tokens = ui.number(
                            t("settings.max_tokens"),
                            value=settings.ai.max_tokens,
                            min=100,
                            max=8000,
                            step=100,
                        ).classes("full-width").props("outlined dark")

                # --- Safety tab ---
                with ui.tab_panel(safety_tab):
                    with ui.card().classes("q-pa-md full-width").style(
                        f"background: {COLORS['surface']}; border-radius: 12px;"
                    ):
                        require_review = ui.switch(
                            t("settings.require_review"),
                            value=settings.safety.require_review,
                        ).props("dark")

                        max_posts = ui.number(
                            t("settings.max_posts_per_day"),
                            value=settings.safety.max_posts_per_day,
                            min=1,
                            max=50,
                            step=1,
                        ).classes("full-width").props("outlined dark")

                        min_interval = ui.number(
                            t("settings.min_interval"),
                            value=settings.safety.min_interval_minutes,
                            min=1,
                            max=1440,
                            step=1,
                        ).classes("full-width").props("outlined dark")

                # --- Appearance tab ---
                with ui.tab_panel(appearance_tab):
                    with ui.card().classes("q-pa-md full-width").style(
                        f"background: {COLORS['surface']}; border-radius: 12px;"
                    ):
                        ui.label(t("settings.language")).classes(
                            "text-subtitle1 q-mb-sm"
                        ).style(f"color: {COLORS['text_primary']};")

                        # Get current language
                        current_lang = get_language()
                        current_display = LANGUAGE_NAMES.get(current_lang, "中文")

                        language_select = ui.select(
                            ["中文", "English"],
                            value=current_display,
                            label=t("settings.language"),
                        ).classes("full-width").props("outlined dark")

                        def on_lang_change(e):
                            lang_map = {
                                "中文": "zh_CN",
                                "English": "en_US",
                            }
                            set_language(lang_map.get(e.value, "zh_CN"))
                            ui.notify(
                                t("settings.saved") + ". " + "Refresh to apply.",
                                type="positive"
                            )

                        language_select.on_value_change(on_lang_change)

                # --- About tab ---
                with ui.tab_panel(about_tab):
                    with ui.card().classes("q-pa-md full-width").style(
                        f"background: {COLORS['surface']}; border-radius: 12px;"
                    ):
                        ui.label("Content Pilot").classes(
                            "text-h4"
                        ).style(f"color: {COLORS['text_primary']};")
                        ui.label("AI-powered content creation and publishing platform").classes(
                            "text-body1 q-mt-sm"
                        ).style(f"color: {COLORS['text_secondary']};")

                        ui.separator().classes("q-my-md")

                        ui.label("Version: 1.0.0").classes("text-caption")
                        ui.link("GitHub", "https://github.com/content-pilot", new_tab=True).classes("text-caption")

                        ui.separator().classes("q-my-md")

                        ui.label("Built with ❤️ using NiceGUI").classes(
                            "text-caption"
                        ).style(f"color: {COLORS['text_secondary']};")

            # --- Save button (for all tabs) ---
            async def do_save():
                save_btn.props("loading")
                try:
                    _save_env(
                        provider=provider_select.value,
                        anthropic_key=anthropic_key.value,
                        openai_key=openai_key.value,
                        qwen_key=qwen_key.value,
                        glm_key=glm_key.value,
                    )
                    _save_config(
                        provider=provider_select.value,
                        claude_model=claude_model.value,
                        openai_model=openai_model.value,
                        qwen_model=qwen_model.value,
                        glm_model=glm_model.value,
                        temperature=temperature.value,
                        max_tokens=int(max_tokens.value),
                        require_review=require_review.value,
                        max_posts_per_day=int(max_posts.value),
                        min_interval_minutes=int(min_interval.value),
                    )
                    get_settings.cache_clear()
                    ui.notify(
                        t("settings.saved") + " " + t("common.success").lower() + "!",
                        type="positive",
                    )
                except Exception as e:
                    ui.notify(
                        f"{t('common.error')}: {e}",
                        type="negative"
                    )
                    logger.error("Settings save error: %s", e)
                finally:
                    save_btn.props(remove="loading")

            save_btn = ui.button(
                t("settings.save"),
                icon="save",
                on_click=do_save
            ).props(f"color={COLORS['primary']}").classes("q-mt-lg")


def _save_env(
    provider: str,
    anthropic_key: str,
    openai_key: str,
    qwen_key: str,
    glm_key: str,
) -> None:
    """Write API keys to .env file."""
    env_path = Path(".env")
    existing: dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                existing[k.strip()] = v.strip()

    existing["CP_AI__PROVIDER"] = provider
    if anthropic_key:
        existing["CP_AI__ANTHROPIC_API_KEY"] = anthropic_key
    if openai_key:
        existing["CP_AI__OPENAI_API_KEY"] = openai_key
    if qwen_key:
        existing["CP_AI__QWEN_API_KEY"] = qwen_key
    if glm_key:
        existing["CP_AI__GLM_API_KEY"] = glm_key

    lines = [f"{k}={v}" for k, v in existing.items()]
    env_path.write_text("\n".join(lines) + "\n")


def _save_config(
    provider: str,
    claude_model: str,
    openai_model: str,
    qwen_model: str,
    glm_model: str,
    temperature: float,
    max_tokens: int,
    require_review: bool,
    max_posts_per_day: int,
    min_interval_minutes: int,
) -> None:
    """Write non-secret settings to ~/.content-pilot/config.toml."""
    config_dir = Path.home() / ".content-pilot"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.toml"

    toml_content = f"""\
[ai]
provider = "{provider}"
claude_model = "{claude_model}"
openai_model = "{openai_model}"
qwen_model = "{qwen_model}"
glm_model = "{glm_model}"
temperature = {temperature}
max_tokens = {max_tokens}

[safety]
require_review = {'true' if require_review else 'false'}
max_posts_per_day = {max_posts_per_day}
min_interval_minutes = {min_interval_minutes}
"""
    config_path.write_text(toml_content)
