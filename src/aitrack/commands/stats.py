import logging
from datetime import UTC, datetime

from aitrack.config import DEFAULT_DB_PATH
from aitrack.database.repository import UsageRepository
from aitrack.utils.formatters import (
    console,
    format_cost,
    format_tokens,
    make_breakdown_table,
    make_summary_table,
)

logger = logging.getLogger(__name__)


def _print_stats(repo: UsageRepository, start: datetime, end: datetime, label: str) -> None:
    overall = repo.aggregate_with_costs(start=start, end=end)
    if not overall or overall["total_tokens"] == 0:
        console.print(f"[yellow]No usage data for {label}.[/]")
        return

    data = overall
    summary_rows = [
        ("Input", format_tokens(data["total_input"]), format_cost(data["total_input_cost"])),
        ("Output", format_tokens(data["total_output"]), format_cost(data["total_output_cost"])),
        ("Reasoning", format_tokens(data["total_reasoning"]), "-"),
        (
            "Cache Read",
            format_tokens(data["total_cache_read"]),
            format_cost(data["total_cache_read_cost"]),
        ),
        (
            "Cache Write",
            format_tokens(data["total_cache_write"]),
            format_cost(data["total_cache_write_cost"]),
        ),
        ("Total", format_tokens(data["total_tokens"]), format_cost(data["total_cost"])),
    ]

    table = make_summary_table(
        f"{label} Usage",
        [(r[0], r[1], r[2]) for r in summary_rows],
        f"Records: {data['record_count']}",
    )
    console.print(table)

    tool_breakdown = repo.aggregate(start=start, end=end, group_by="tool_name")
    if tool_breakdown:
        tool_data = [
            (b["group"], b["total_tokens"], b["total_cost"])
            for b in tool_breakdown
            if b["total_tokens"] > 0
        ]
        if tool_data:
            console.print(make_breakdown_table(f"{label} by Tool", tool_data))

    model_breakdown = repo.aggregate(start=start, end=end, group_by="model")
    if model_breakdown:
        model_data = [
            (b["group"], b["total_tokens"], b["total_cost"])
            for b in model_breakdown
            if b["total_tokens"] > 0
        ]
        if model_data:
            console.print(make_breakdown_table(f"{label} by Model", model_data))

    provider_breakdown = repo.aggregate(start=start, end=end, group_by="provider")
    if provider_breakdown:
        provider_data = [
            (b["group"], b["total_tokens"], b["total_cost"])
            for b in provider_breakdown
            if b["total_tokens"] > 0
        ]
        if provider_data:
            console.print(make_breakdown_table(f"{label} by Provider", provider_data))


def run_today(db_path: str = DEFAULT_DB_PATH) -> None:
    repo = UsageRepository(db_path)
    start = repo.get_today_start()
    end = datetime.now(UTC)
    _print_stats(repo, start, end, "Today")


def run_week(db_path: str = DEFAULT_DB_PATH) -> None:
    repo = UsageRepository(db_path)
    start = repo.get_week_start()
    end = datetime.now(UTC)
    _print_stats(repo, start, end, "This Week")


def run_month(db_path: str = DEFAULT_DB_PATH) -> None:
    repo = UsageRepository(db_path)
    start = repo.get_month_start()
    end = datetime.now(UTC)
    _print_stats(repo, start, end, "This Month")


def run_lifetime(db_path: str = DEFAULT_DB_PATH) -> None:
    repo = UsageRepository(db_path)
    _print_stats(repo, None, None, "Lifetime")
