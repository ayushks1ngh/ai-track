import logging

from rich import box
from rich.table import Table

from aitrack.collectors.generic import GenericCollector
from aitrack.collectors.kiro import KiroCollector
from aitrack.collectors.opencode import OpencodeCollector
from aitrack.utils.formatters import console

logger = logging.getLogger(__name__)


def run_discover() -> None:
    collectors = [OpencodeCollector(), KiroCollector(), GenericCollector()]

    all_sources = []
    detected_tools = set()

    table = Table(title="Discovery Results", box=box.ROUNDED)
    table.add_column("Tool", style="cyan")
    table.add_column("Source Type", style="magenta")
    table.add_column("Path", style="green")
    table.add_column("Parser Compatible", style="yellow")
    table.add_column("Records Found", style="white", justify="right")

    for collector in collectors:
        try:
            sources = collector.discover()
            for src in sources:
                detected_tools.add(src.tool_name)
                all_sources.append(src)
                compat = "[green]Yes[/]" if src.parser_compatible else "[red]No[/]"
                table.add_row(
                    src.tool_name,
                    src.source_type,
                    src.path,
                    compat,
                    str(src.record_count) if src.record_count > 0 else "-",
                )
        except Exception as e:
            logger.error("discovery failed for %s: %s", collector.tool_name, e)

    console.print(table)

    if detected_tools:
        console.print(f"\n[bold green]Detected tools:[/] {', '.join(sorted(detected_tools))}")
    else:
        console.print("\n[yellow]No AI coding assistant data sources found.[/]")

    console.print(f"\nTotal sources discovered: {len(all_sources)}")
