import logging
import os
from datetime import UTC, datetime

from rich import box
from rich.table import Table

from aitrack.config import DEFAULT_DB_PATH
from aitrack.database.repository import UsageRepository
from aitrack.utils.formatters import console

logger = logging.getLogger(__name__)


def run_status(db_path: str = DEFAULT_DB_PATH) -> None:
    """Show a quick health check: DB location, size, record count, last activity."""
    table = Table(title="aitrack status", box=box.ROUNDED)
    table.add_column("Item", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Database path", db_path)

    if not os.path.exists(db_path):
        table.add_row("Database size", "-")
        table.add_row("Total records", "0")
        table.add_row("Last activity", "-")
        console.print(table)
        console.print(
            "\n[yellow]No database found yet. Run [bold]aitrack scan[/] to import usage data.[/]"
        )
        return

    size_bytes = os.path.getsize(db_path)
    size_str = (
        f"{size_bytes / 1024:.1f} KB"
        if size_bytes < 1024 * 1024
        else f"{size_bytes / (1024 * 1024):.1f} MB"
    )
    table.add_row("Database size", size_str)

    repo = UsageRepository(db_path)
    total = repo.total_records()
    table.add_row("Total records", str(total))

    records = repo.query()
    if records:
        latest = max(r.timestamp for r in records)
        now = datetime.now(UTC) if latest.tzinfo else datetime.now()
        delta = now - latest
        hours = delta.total_seconds() / 3600
        if hours < 1:
            recency = f"{int(delta.total_seconds() / 60)}m ago"
        elif hours < 24:
            recency = f"{hours:.1f}h ago"
        else:
            recency = f"{hours / 24:.1f}d ago"
        table.add_row("Last activity", f"{latest.strftime('%Y-%m-%d %H:%M')} ({recency})")

        tools = sorted({r.tool_name for r in records})
        table.add_row("Tools tracked", ", ".join(tools))
    else:
        table.add_row("Last activity", "-")

    console.print(table)
