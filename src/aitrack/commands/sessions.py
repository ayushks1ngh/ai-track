import logging

from rich import box
from rich.table import Table

from aitrack.config import DEFAULT_DB_PATH
from aitrack.database.repository import UsageRepository
from aitrack.utils.formatters import console, format_cost, format_tokens

logger = logging.getLogger(__name__)


def _format_duration(seconds: float) -> str:
    if seconds is None:
        return "-"
    if seconds < 60:
        return f"{seconds:.0f}s"
    if seconds < 3600:
        return f"{seconds / 60:.0f}m"
    return f"{seconds / 3600:.1f}h"


def run_sessions(db_path: str = DEFAULT_DB_PATH) -> None:
    repo = UsageRepository(db_path)
    sessions = repo.get_unique_sessions()

    if not sessions:
        console.print("[yellow]No sessions found.[/]")
        return

    table = Table(title="Sessions", box=box.ROUNDED)
    table.add_column("Session ID", style="cyan")
    table.add_column("First Seen", style="green")
    table.add_column("Duration", style="magenta", justify="right")
    table.add_column("Requests", style="white", justify="right")
    table.add_column("Tokens", style="green", justify="right")
    table.add_column("Cost", style="yellow", justify="right")

    for s in sorted(sessions, key=lambda x: x["total_tokens"], reverse=True)[:50]:
        first_str = s["first_seen"].strftime("%Y-%m-%d %H:%M") if s["first_seen"] else "-"
        table.add_row(
            s["session_id"][:20],
            first_str,
            _format_duration(s["duration_seconds"]),
            str(s["requests"]),
            format_tokens(s["total_tokens"]),
            format_cost(s["total_cost"]),
        )

    console.print(table)
    console.print(f"Total sessions: {len(sessions)}")


def run_top_sessions(
    db_path: str = DEFAULT_DB_PATH,
    sort_by: str = "tokens",
    limit: int = 10,
) -> None:
    repo = UsageRepository(db_path)
    sessions = repo.get_unique_sessions()

    if not sessions:
        console.print("[yellow]No sessions found.[/]")
        return

    sort_key = {"tokens": "total_tokens", "duration": "duration_seconds", "cost": "total_cost"}
    key = sort_key.get(sort_by, "total_tokens")

    sessions.sort(key=lambda x: x.get(key, 0) or 0, reverse=True)

    table = Table(title=f"Top {limit} Sessions (by {sort_by})", box=box.ROUNDED)
    table.add_column("#", style="dim")
    table.add_column("Session ID", style="cyan")
    table.add_column("Duration", style="magenta", justify="right")
    table.add_column("Tokens", style="green", justify="right")
    table.add_column("Cost", style="yellow", justify="right")

    for i, s in enumerate(sessions[:limit]):
        table.add_row(
            str(i + 1),
            s["session_id"][:20],
            _format_duration(s["duration_seconds"]),
            format_tokens(s["total_tokens"]),
            format_cost(s["total_cost"]),
        )

    console.print(table)
