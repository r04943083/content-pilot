"""Settings page: AI provider, API keys, safety settings."""

from __future__ import annotations

import logging
from pathlib import Path

from nicegui import ui

from content_pilot.config import get_settings
from content_pilot.gui.components.nav import page_layout

logger = logging.getLogger(__name__)

PROVIDERS = ["claude", "openai", "qwen", "glm"]


def register() -> None:
    @ui.page("/settings")
    async def settings_page():
        page_layout("Settings")

        settings = get_settings()

        # --- AI Provider settings ---
        ui.label("AI Provider").classes("text-h6 q-mt-md q-mb-sm")
        with ui.card().classes("q-pa-md full-width"):
            provider_select = ui.select(
                PROVIDERS, value=settings.ai.provider, label="Provider"
            ).classes("full-width")

            anthropic_key = ui.input(
                "Anthropic API Key",
                value=settings.ai.anthropic_api_key,
                password=True,
                password_toggle_button=True,
            ).classes("full-width")
            openai_key = ui.input(
                "OpenAI API Key",
                value=settings.ai.openai_api_key,
                password=True,
                password_toggle_button=True,
            ).classes("full-width")
            qwen_key = ui.input(
                "Qwen API Key",
                value=settings.ai.qwen_api_key,
                password=True,
                password_toggle_button=True,
            ).classes("full-width")
            glm_key = ui.input(
                "GLM API Key",
                value=settings.ai.glm_api_key,
                password=True,
                password_toggle_button=True,
            ).classes("full-width")

        # --- Model settings ---
        ui.label("Model Settings").classes("text-h6 q-mt-lg q-mb-sm")
        with ui.card().classes("q-pa-md full-width"):
            claude_model = ui.input("Claude Model", value=settings.ai.claude_model).classes(
                "full-width"
            )
            openai_model = ui.input("OpenAI Model", value=settings.ai.openai_model).classes(
                "full-width"
            )
            qwen_model = ui.input("Qwen Model", value=settings.ai.qwen_model).classes(
                "full-width"
            )
            glm_model = ui.input("GLM Model", value=settings.ai.glm_model).classes("full-width")
            temperature = ui.slider(min=0, max=2, step=0.1, value=settings.ai.temperature).classes(
                "full-width"
            )
            ui.label().bind_text_from(temperature, "value", backward=lambda v: f"Temperature: {v}")
            max_tokens = ui.number(
                "Max Tokens", value=settings.ai.max_tokens, min=100, max=8000, step=100
            ).classes("full-width")

        # --- Safety settings ---
        ui.label("Safety").classes("text-h6 q-mt-lg q-mb-sm")
        with ui.card().classes("q-pa-md full-width"):
            require_review = ui.switch(
                "Require review before publishing", value=settings.safety.require_review
            )
            max_posts = ui.number(
                "Max posts per day",
                value=settings.safety.max_posts_per_day,
                min=1,
                max=50,
                step=1,
            ).classes("full-width")
            min_interval = ui.number(
                "Min interval (minutes)",
                value=settings.safety.min_interval_minutes,
                min=1,
                max=1440,
                step=1,
            ).classes("full-width")

        # --- Save ---
        async def do_save():
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
                # Clear settings cache so next access picks up new values
                get_settings.cache_clear()
                ui.notify("Settings saved! Restart may be needed for full effect.", type="positive")
            except Exception as e:
                ui.notify(f"Error saving: {e}", type="negative")
                logger.error("Settings save error: %s", e)

        ui.button("Save Settings", icon="save", on_click=do_save).props(
            "color=primary"
        ).classes("q-mt-lg")


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
