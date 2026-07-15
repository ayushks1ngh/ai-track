import logging
import os

import typer

from aitrack.config import DEFAULT_DB_PATH
from aitrack.utils.formatters import console

logger = logging.getLogger(__name__)


def run_reset(db_path: str = DEFAULT_DB_PATH, force: bool = False) -> None:
    """Delete the local usage database, clearing all imported records."""
    if not os.path.exists(db_path):
        console.print(f"[yellow]No database found at {db_path}.[/]")
        return

    if not force:
        confirm = typer.confirm(f"This will permanently delete {db_path}. Continue?")
        if not confirm:
            console.print("[yellow]Aborted.[/]")
            return

    for suffix in ("", "-shm", "-wal"):
        path = db_path + suffix
        if os.path.exists(path):
            os.remove(path)

    console.print(f"[green]Database reset.[/] Removed {db_path}")
    console.print("Run [bold]aitrack scan[/] to re-import your usage data.")
