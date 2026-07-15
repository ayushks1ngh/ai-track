import logging

from rich.progress import Progress, SpinnerColumn, TextColumn

from aitrack.collectors.generic import GenericCollector
from aitrack.collectors.kiro import KiroCollector
from aitrack.collectors.opencode import OpencodeCollector
from aitrack.config import DEFAULT_DB_PATH
from aitrack.database.repository import UsageRepository
from aitrack.utils.formatters import console

logger = logging.getLogger(__name__)


def run_scan(db_path: str = DEFAULT_DB_PATH, incremental: bool = True) -> None:
    repo = UsageRepository(db_path)
    collectors = [OpencodeCollector(), KiroCollector(), GenericCollector()]

    total_inserted = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for coll in collectors:
            task = progress.add_task(f"[cyan]Scanning {coll.tool_name}...", total=None)
            try:
                sources = coll.discover()
                for source in sources:
                    if not source.parser_compatible:
                        continue
                    try:
                        records = coll.collect(source)
                        if incremental:
                            inserted = repo.insert_many(records)
                        else:
                            inserted = len(records)
                            for r in records:
                                repo.insert(r)
                        total_inserted += inserted
                    except Exception as e:
                        logger.error(
                            "collection failed for %s [%s]: %s", source.path, source.source_type, e
                        )
            except Exception as e:
                logger.error("scan failed for %s: %s", coll.tool_name, e)
            progress.update(task, completed=True)

    total = repo.total_records()
    console.print("\n[green]Scan complete.[/]")
    console.print(f"  New records inserted: [bold]{total_inserted}[/]")
    console.print(f"  Total records in database: [bold]{total}[/]")
    console.print(f"  Database: {db_path}")
