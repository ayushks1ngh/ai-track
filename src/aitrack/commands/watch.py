import logging
import os
import time
from datetime import UTC, datetime

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from aitrack.collectors.kiro import KiroCollector
from aitrack.collectors.opencode import OpencodeCollector
from aitrack.commands.scan import run_scan
from aitrack.config import DEFAULT_DB_PATH, WATCH_DEBOUNCE_SECONDS
from aitrack.utils.formatters import console

logger = logging.getLogger(__name__)


def _get_watch_dirs() -> list[str]:
    """Discover watch directories from collectors."""
    dirs = []
    for collector in [OpencodeCollector(), KiroCollector()]:
        sources = collector.discover()
        for src in sources:
            if src.parser_compatible and os.path.isdir(os.path.dirname(src.path)):
                dirs.append(os.path.dirname(src.path))
    # Deduplicate while preserving order
    seen = set()
    result = []
    for d in dirs:
        if d not in seen:
            seen.add(d)
            result.append(d)
    return result


class UsageFileHandler(FileSystemEventHandler):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.last_scan = 0

    def on_modified(self, event):
        if event.is_directory:
            return
        now = time.time()
        if now - self.last_scan < WATCH_DEBOUNCE_SECONDS:
            return
        self.last_scan = now
        ts = datetime.now(UTC).strftime("%H:%M:%S")
        console.print(
            f"[dim]{ts}[/] File change detected: [green]{os.path.basename(event.src_path)}[/]"
        )
        try:
            run_scan(db_path=self.db_path)
        except Exception as e:
            logger.error("auto-scan failed: %s", e)


def run_watch(db_path: str = DEFAULT_DB_PATH) -> None:
    console.print("[bold cyan]aitrack watch[/] - monitoring for changes...")
    console.print(f"  Database: {db_path}")

    watch_dirs = _get_watch_dirs()
    console.print(f"  Watching: {', '.join(watch_dirs)}")
    console.print("  Press Ctrl+C to stop.\n")

    run_scan(db_path=db_path)

    event_handler = UsageFileHandler(db_path)
    observer = Observer()
    for watch_dir in watch_dirs:
        if os.path.isdir(watch_dir):
            observer.schedule(event_handler, watch_dir, recursive=True)
            console.print(f"  [dim]Watching {watch_dir}[/]")

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    console.print("\n[yellow]Watcher stopped.[/]")
