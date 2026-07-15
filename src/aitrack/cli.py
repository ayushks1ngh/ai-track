import os

import typer

from aitrack import __version__
from aitrack.utils.formatters import console
from aitrack.utils.logging import setup_logging

DEFAULT_DB = os.path.expanduser("~/.local/share/aitrack/usage.db")


def _ensure_dirs() -> None:
    os.makedirs(os.path.dirname(DEFAULT_DB), exist_ok=True)
    os.makedirs(os.path.expanduser("~/.local/share/aitrack/log"), exist_ok=True)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"aitrack {__version__}")
        raise typer.Exit()


app = typer.Typer(
    name="aitrack",
    help="Local-first AI token usage tracker for coding assistants",
    no_args_is_help=True,
)


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False, "--version", callback=_version_callback, is_eager=True, help="Show version and exit."
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose/debug logging to stderr."
    ),
) -> None:
    _ensure_dirs()
    setup_logging(verbose=verbose)


@app.command()
def discover():
    """Detect AI tools and their data sources on this machine."""
    from aitrack.commands.discover import run_discover

    run_discover()


@app.command()
def scan():
    """Scan all detected sources and import usage records."""
    from aitrack.commands.scan import run_scan

    run_scan(db_path=DEFAULT_DB)


@app.command()
def today():
    """Show token usage for today."""
    from aitrack.commands.stats import run_today

    run_today(db_path=DEFAULT_DB)


@app.command()
def week():
    """Show token usage for this week."""
    from aitrack.commands.stats import run_week

    run_week(db_path=DEFAULT_DB)


@app.command()
def month():
    """Show token usage for this month."""
    from aitrack.commands.stats import run_month

    run_month(db_path=DEFAULT_DB)


@app.command()
def lifetime():
    """Show all-time token usage."""
    from aitrack.commands.stats import run_lifetime

    run_lifetime(db_path=DEFAULT_DB)


@app.command()
def cost():
    """Show cost summary and pricing configuration."""
    from aitrack.commands.cost import run_cost

    run_cost(db_path=DEFAULT_DB)


@app.command()
def watch():
    """Watch for changes and auto-rescan."""
    from aitrack.commands.watch import run_watch

    run_watch(db_path=DEFAULT_DB)


@app.command()
def live():
    """Launch the live Textual dashboard."""
    from aitrack.dashboard.live_app import LiveDashboard

    app_dash = LiveDashboard(db_path=DEFAULT_DB)
    app_dash.run()


@app.command()
def sessions():
    """List tracked sessions with token/cost data."""
    from aitrack.commands.sessions import run_sessions

    run_sessions(db_path=DEFAULT_DB)


@app.command(name="top-sessions")
def top_sessions(
    sort_by: str = typer.Option("tokens", help="Sort by: tokens, duration, cost"),
    limit: int = typer.Option(10, help="Number of top sessions to show"),
):
    """Show top sessions by tokens, duration, or cost."""
    from aitrack.commands.sessions import run_top_sessions

    run_top_sessions(db_path=DEFAULT_DB, sort_by=sort_by, limit=limit)


@app.command()
def export(
    fmt: str = typer.Argument("csv", help="Export format: csv or json"),
    period: str = typer.Option("lifetime", help="Period: today, week, month, lifetime"),
    output: str | None = typer.Option(None, help="Output file path"),
):
    """Export usage data to CSV or JSON."""
    from aitrack.commands.export_ import run_export_csv, run_export_json

    if fmt == "csv":
        run_export_csv(period=period, output=output or "", db_path=DEFAULT_DB)
    elif fmt == "json":
        run_export_json(period=period, output=output or "", db_path=DEFAULT_DB)
    else:
        console.print(f"[red]Unsupported format: {fmt}. Use 'csv' or 'json'.[/]")


@app.command()
def status():
    """Show database health: size, record count, last activity."""
    from aitrack.commands.status import run_status

    run_status(db_path=DEFAULT_DB)


@app.command()
def reset(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt."),
):
    """Delete the local usage database (irreversible)."""
    from aitrack.commands.reset import run_reset

    run_reset(db_path=DEFAULT_DB, force=force)


def main():
    app()


if __name__ == "__main__":
    main()
