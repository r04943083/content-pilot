"""CLI entry point using Click with Rich output."""

from __future__ import annotations

import asyncio
import json
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from content_pilot.constants import PLATFORMS, STYLES
from content_pilot.utils.log import setup_logging

console = Console()


def run_async(coro):
    """Run async function from sync Click context."""
    return asyncio.get_event_loop().run_until_complete(coro)


def get_app():
    """Lazy import to avoid import-time side effects."""
    from content_pilot.app import App
    return App()


# --- Main CLI group ---


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool) -> None:
    """Content Pilot - AI-driven social media automation."""
    setup_logging("DEBUG" if verbose else "INFO")


# --- Login ---


@cli.command()
@click.option(
    "--platform", "-p",
    type=click.Choice(PLATFORMS + ["all"]),
    required=True,
    help="Platform to login to",
)
def login(platform: str) -> None:
    """Login to a platform via QR code scan."""
    app = get_app()

    async def _login():
        await app.startup()
        try:
            if platform == "all":
                results = await app.login_all()
                for p, ok in results.items():
                    status = "[green]Success[/green]" if ok else "[red]Failed[/red]"
                    console.print(f"  {p}: {status}")
            else:
                console.print(f"Logging in to [bold]{platform}[/bold]...")
                console.print("Please scan the QR code with your phone app.")
                ok = await app.login(platform)
                if ok:
                    console.print(f"[green]Login to {platform} successful![/green]")
                else:
                    console.print(f"[red]Login to {platform} failed.[/red]")
                    sys.exit(1)
        finally:
            await app.shutdown()

    run_async(_login())


# --- Status ---


@cli.command()
def status() -> None:
    """Show account status for all platforms."""
    app = get_app()

    async def _status():
        await app.startup()
        try:
            accounts = await app.db.get_all_accounts()
            if not accounts:
                console.print("[yellow]No accounts configured. Run 'content-pilot login' first.[/yellow]")
                return

            table = Table(title="Account Status")
            table.add_column("Platform", style="cyan")
            table.add_column("Nickname")
            table.add_column("Followers", justify="right")
            table.add_column("Login State")
            table.add_column("Updated")

            for acc in accounts:
                state_color = "green" if acc["login_state"] == "active" else "red"
                table.add_row(
                    acc["platform"],
                    acc["nickname"] or acc["username"],
                    str(acc["follower_count"]),
                    f"[{state_color}]{acc['login_state']}[/{state_color}]",
                    acc["updated_at"] or "",
                )

            console.print(table)
        finally:
            await app.shutdown()

    run_async(_status())


# --- Generate ---


@cli.command()
@click.option("--topic", "-t", required=True, help="Content topic")
@click.option(
    "--platform", "-p",
    type=click.Choice(PLATFORMS),
    required=True,
    help="Target platform",
)
@click.option(
    "--style", "-s",
    type=click.Choice(STYLES),
    default="tutorial",
    help="Content style",
)
def generate(topic: str, platform: str, style: str) -> None:
    """Generate AI content for a platform."""
    app = get_app()

    async def _generate():
        await app.startup()
        try:
            console.print(f"Generating [bold]{style}[/bold] content about [bold]{topic}[/bold] for [cyan]{platform}[/cyan]...")

            try:
                post_id, content = await app.generate_content(topic, platform, style)
            except RuntimeError as e:
                console.print(f"[red]{e}[/red]")
                sys.exit(1)
            except Exception as e:
                err_msg = str(e)
                if "401" in err_msg or "auth" in err_msg.lower() or "api_key" in err_msg.lower():
                    console.print(f"[red]API authentication failed. Please check your API key in .env[/red]")
                    console.print(f"[dim]{err_msg[:200]}[/dim]")
                else:
                    console.print(f"[red]Content generation failed: {err_msg[:200]}[/red]")
                sys.exit(1)

            console.print(Panel(
                f"[bold]{content.title}[/bold]\n\n{content.content}\n\n"
                f"Tags: {' '.join(f'#{t}' for t in content.tags)}",
                title=f"Generated Content (ID: {post_id})",
                border_style="green",
            ))

            # Review flow
            if app.settings.safety.require_review:
                action = click.prompt(
                    "Action",
                    type=click.Choice(["approve", "edit", "regenerate", "cancel"]),
                    default="approve",
                )
                if action == "approve":
                    await app.db.update_post(post_id, status="approved")
                    console.print(f"[green]Post {post_id} approved.[/green]")
                elif action == "edit":
                    new_content = click.edit(content.content)
                    if new_content:
                        await app.db.update_post(post_id, content=new_content, status="approved")
                        console.print(f"[green]Post {post_id} edited and approved.[/green]")
                elif action == "regenerate":
                    console.print("Regenerating...")
                    await app.db.update_post(post_id, status="draft")
                    # Recursive call
                    post_id2, content2 = await app.generate_content(topic, platform, style)
                    console.print(Panel(
                        f"[bold]{content2.title}[/bold]\n\n{content2.content}",
                        title=f"Regenerated Content (ID: {post_id2})",
                    ))
                else:
                    await app.db.update_post(post_id, status="draft")
                    console.print("[yellow]Cancelled.[/yellow]")
            else:
                await app.db.update_post(post_id, status="approved")
                console.print(f"[green]Auto-approved post {post_id}.[/green]")

        finally:
            await app.shutdown()

    run_async(_generate())


# --- Publish ---


@cli.command()
@click.option("--content-id", "-c", type=int, required=True, help="Post ID to publish")
@click.option("--dry-run", is_flag=True, help="Preview without publishing")
def publish(content_id: int, dry_run: bool) -> None:
    """Publish content to a platform."""
    app = get_app()

    async def _publish():
        await app.startup()
        try:
            post = await app.db.get_post(content_id)
            if not post:
                console.print(f"[red]Post {content_id} not found.[/red]")
                sys.exit(1)

            if dry_run:
                console.print(Panel(
                    f"Platform: {post['platform']}\n"
                    f"Title: {post['title']}\n"
                    f"Content: {post['content'][:200]}...\n"
                    f"Tags: {post['tags']}\n"
                    f"Status: {post['status']}",
                    title="[yellow]DRY RUN[/yellow]",
                ))
                return

            ok = await app.publish(content_id)
            if ok:
                console.print(f"[green]Post {content_id} published successfully![/green]")
            else:
                console.print(f"[red]Failed to publish post {content_id}.[/red]")
                sys.exit(1)
        finally:
            await app.shutdown()

    run_async(_publish())


# --- Schedule ---


@cli.group()
def schedule() -> None:
    """Manage publishing schedules."""


@schedule.command("add")
@click.option("--name", "-n", required=True, help="Schedule name")
@click.option("--platform", "-p", type=click.Choice(PLATFORMS), required=True)
@click.option("--topic", "-t", default="", help="Content topic")
@click.option("--style", "-s", type=click.Choice(STYLES), default="tutorial")
@click.option("--cron", required=True, help="Cron expression (e.g. '0 20 * * *')")
def schedule_add(name: str, platform: str, topic: str, style: str, cron: str) -> None:
    """Add a new schedule."""
    app = get_app()

    async def _add():
        await app.startup()
        try:
            sid = await app.scheduler.add_schedule(
                name=name, platform=platform, topic=topic, style=style,
                cron_expression=cron,
            )
            console.print(f"[green]Schedule '{name}' created (ID: {sid})[/green]")
            console.print(f"  Cron: {cron} | Platform: {platform} | Style: {style}")
        finally:
            await app.shutdown()

    run_async(_add())


@schedule.command("list")
def schedule_list() -> None:
    """List all schedules."""
    app = get_app()

    async def _list():
        await app.startup()
        try:
            schedules = await app.db.get_schedules()
            if not schedules:
                console.print("[yellow]No schedules configured.[/yellow]")
                return

            table = Table(title="Schedules")
            table.add_column("ID", justify="right")
            table.add_column("Name")
            table.add_column("Platform")
            table.add_column("Cron")
            table.add_column("Topic")
            table.add_column("Enabled")
            table.add_column("Last Run")

            for s in schedules:
                enabled = "[green]Yes[/green]" if s["enabled"] else "[red]No[/red]"
                table.add_row(
                    str(s["id"]), s["name"], s["platform"], s["cron_expression"],
                    s["topic"][:30] or "-", enabled, s["last_run_at"] or "Never",
                )
            console.print(table)
        finally:
            await app.shutdown()

    run_async(_list())


@schedule.command("remove")
@click.option("--id", "schedule_id", type=int, required=True, help="Schedule ID")
def schedule_remove(schedule_id: int) -> None:
    """Remove a schedule."""
    app = get_app()

    async def _remove():
        await app.startup()
        try:
            await app.scheduler.remove_schedule(schedule_id)
            console.print(f"[green]Schedule {schedule_id} removed.[/green]")
        finally:
            await app.shutdown()

    run_async(_remove())


@schedule.command("pause")
@click.option("--id", "schedule_id", type=int, required=True, help="Schedule ID")
def schedule_pause(schedule_id: int) -> None:
    """Pause a schedule."""
    app = get_app()

    async def _pause():
        await app.startup()
        try:
            await app.scheduler.pause_schedule(schedule_id)
            console.print(f"[yellow]Schedule {schedule_id} paused.[/yellow]")
        finally:
            await app.shutdown()

    run_async(_pause())


@schedule.command("resume")
@click.option("--id", "schedule_id", type=int, required=True, help="Schedule ID")
def schedule_resume(schedule_id: int) -> None:
    """Resume a paused schedule."""
    app = get_app()

    async def _resume():
        await app.startup()
        try:
            await app.scheduler.resume_schedule(schedule_id)
            console.print(f"[green]Schedule {schedule_id} resumed.[/green]")
        finally:
            await app.shutdown()

    run_async(_resume())


# --- Analytics ---


@cli.group()
def analytics() -> None:
    """View analytics and growth data."""


@analytics.command("summary")
@click.option("--platform", "-p", type=click.Choice(PLATFORMS), default=None)
def analytics_summary(platform: str | None) -> None:
    """Show analytics summary."""
    app = get_app()

    async def _summary():
        await app.startup()
        try:
            summary = await app.analytics.get_summary(platform)
            title = f"Analytics Summary - {platform}" if platform else "Analytics Summary - All Platforms"
            table = Table(title=title)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", justify="right")

            table.add_row("Total Posts", str(summary["total_posts"]))
            table.add_row("Published", str(summary["published_posts"]))
            table.add_row("Total Views", f"{summary['total_views']:,}")
            table.add_row("Total Likes", f"{summary['total_likes']:,}")
            table.add_row("Total Comments", f"{summary['total_comments']:,}")
            table.add_row("Total Shares", f"{summary['total_shares']:,}")
            table.add_row("Total Favorites", f"{summary['total_favorites']:,}")

            console.print(table)
        finally:
            await app.shutdown()

    run_async(_summary())


@analytics.command("growth")
@click.option("--platform", "-p", type=click.Choice(PLATFORMS), required=True)
@click.option("--days", "-d", type=int, default=30, help="Number of days")
def analytics_growth(platform: str, days: int) -> None:
    """Show follower growth trend."""
    app = get_app()

    async def _growth():
        await app.startup()
        try:
            data = await app.analytics.get_growth_trend(platform, days)
            if not data:
                console.print(f"[yellow]No growth data for {platform}.[/yellow]")
                return

            table = Table(title=f"Follower Growth - {platform} (Last {days} days)")
            table.add_column("Date")
            table.add_column("Followers", justify="right")
            table.add_column("Change", justify="right")

            for row in reversed(data):
                delta = row["follower_delta"]
                delta_str = f"+{delta}" if delta > 0 else str(delta)
                delta_style = "green" if delta > 0 else ("red" if delta < 0 else "")
                table.add_row(
                    row["recorded_date"],
                    f"{row['follower_count']:,}",
                    f"[{delta_style}]{delta_str}[/{delta_style}]" if delta_style else delta_str,
                )
            console.print(table)
        finally:
            await app.shutdown()

    run_async(_growth())


@analytics.command("post")
@click.option("--id", "post_id", type=int, required=True, help="Post ID")
def analytics_post(post_id: int) -> None:
    """Show analytics for a specific post."""
    app = get_app()

    async def _post():
        await app.startup()
        try:
            post = await app.db.get_post(post_id)
            if not post:
                console.print(f"[red]Post {post_id} not found.[/red]")
                return

            data = await app.db.get_post_analytics(post_id)
            if not data:
                console.print(f"[yellow]No analytics data for post {post_id}.[/yellow]")
                return

            latest = data[0]
            console.print(Panel(
                f"Title: {post['title']}\n"
                f"Platform: {post['platform']}\n"
                f"Views: {latest['views']:,}\n"
                f"Likes: {latest['likes']:,}\n"
                f"Comments: {latest['comments']:,}\n"
                f"Shares: {latest['shares']:,}\n"
                f"Favorites: {latest['favorites']:,}",
                title=f"Post {post_id} Analytics",
            ))
        finally:
            await app.shutdown()

    run_async(_post())


@analytics.command("export")
@click.option("--output", "-o", default="analytics_export.json", help="Output file")
@click.option("--platform", "-p", type=click.Choice(PLATFORMS), default=None)
def analytics_export(output: str, platform: str | None) -> None:
    """Export analytics data to JSON."""
    app = get_app()

    async def _export():
        await app.startup()
        try:
            summary = await app.analytics.get_summary(platform)
            posts = await app.db.get_posts(platform=platform, status="published")

            export_data = {
                "summary": summary,
                "posts": posts,
            }

            with open(output, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            console.print(f"[green]Exported to {output}[/green]")
        finally:
            await app.shutdown()

    run_async(_export())


# --- Config ---


@cli.group()
def config() -> None:
    """Manage configuration."""


@config.command("show")
def config_show() -> None:
    """Show current configuration."""
    from content_pilot.config import get_settings
    settings = get_settings()

    table = Table(title="Current Configuration")
    table.add_column("Section", style="cyan")
    table.add_column("Key")
    table.add_column("Value")

    for section_name in ["general", "ai", "database", "browser", "safety", "scheduler"]:
        section = getattr(settings, section_name)
        for key, value in section.model_dump().items():
            display_val = str(value)
            if "api_key" in key and value:
                display_val = value[:8] + "..." if len(value) > 8 else "***"
            table.add_row(section_name, key, display_val)

    console.print(table)

    # Enabled platforms
    console.print(f"\nEnabled platforms: {', '.join(settings.platforms.enabled)}")


@config.command("validate")
def config_validate() -> None:
    """Validate configuration."""
    try:
        from content_pilot.config import get_settings
        settings = get_settings()
        console.print("[green]Configuration is valid.[/green]")

        # Warnings
        if not settings.ai.anthropic_api_key and settings.ai.provider == "claude":
            console.print("[yellow]Warning: Anthropic API key not set.[/yellow]")
        if not settings.ai.openai_api_key and settings.ai.provider == "openai":
            console.print("[yellow]Warning: OpenAI API key not set.[/yellow]")
        if not settings.ai.qwen_api_key and settings.ai.provider == "qwen":
            console.print("[yellow]Warning: Qwen API key not set (CP_AI__QWEN_API_KEY).[/yellow]")
        if not settings.ai.glm_api_key and settings.ai.provider == "glm":
            console.print("[yellow]Warning: GLM API key not set (CP_AI__GLM_API_KEY).[/yellow]")
    except Exception as e:
        console.print(f"[red]Configuration error: {e}[/red]")


# --- Run daemon ---


@cli.command()
def run() -> None:
    """Start the scheduling daemon."""
    app = get_app()

    async def _run():
        await app.startup()
        try:
            console.print("[bold green]Content Pilot daemon starting...[/bold green]")
            console.print("Press Ctrl+C to stop.")
            await app.run_daemon()
        finally:
            await app.shutdown()

    try:
        run_async(_run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Daemon stopped.[/yellow]")


# --- GUI ---


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8080, type=int, help="Port to bind to")
def gui(host: str, port: int) -> None:
    """Launch the web-based GUI."""
    from content_pilot.gui import launch_gui

    launch_gui(host=host, port=port)


if __name__ == "__main__":
    cli()
