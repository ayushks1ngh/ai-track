import csv
import json
import logging
from datetime import datetime

from aitrack.config import DEFAULT_DB_PATH
from aitrack.database.repository import UsageRepository

logger = logging.getLogger(__name__)


def _get_time_range(period: str, repo: UsageRepository):
    now = datetime.now()
    if period == "today":
        return repo.get_today_start(), now
    if period == "week":
        return repo.get_week_start(), now
    if period == "month":
        return repo.get_month_start(), now
    return None, None


def run_export_csv(
    period: str = "lifetime",
    output: str = "",
    db_path: str = DEFAULT_DB_PATH,
) -> None:
    repo = UsageRepository(db_path)
    start, end = _get_time_range(period, repo)
    records = repo.query(start=start, end=end)

    if not output:
        output = f"aitrack_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    with open(output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "timestamp",
                "tool_name",
                "provider",
                "model",
                "input_tokens",
                "output_tokens",
                "reasoning_tokens",
                "cache_read_tokens",
                "cache_write_tokens",
                "total_tokens",
                "estimated_cost",
                "session_id",
                "source_file",
            ]
        )
        for r in records:
            writer.writerow(
                [
                    r.timestamp.isoformat(),
                    r.tool_name,
                    r.provider,
                    r.model,
                    r.input_tokens,
                    r.output_tokens,
                    r.reasoning_tokens,
                    r.cache_read_tokens,
                    r.cache_write_tokens,
                    r.total_tokens,
                    r.estimated_cost,
                    r.session_id,
                    r.source_file,
                ]
            )

    print(f"Exported {len(records)} records to {output}")


def run_export_json(
    period: str = "lifetime",
    output: str = "",
    db_path: str = DEFAULT_DB_PATH,
) -> None:
    repo = UsageRepository(db_path)
    start, end = _get_time_range(period, repo)
    records = repo.query(start=start, end=end)

    if not output:
        output = f"aitrack_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    data = []
    for r in records:
        data.append(
            {
                "timestamp": r.timestamp.isoformat(),
                "tool_name": r.tool_name,
                "provider": r.provider,
                "model": r.model,
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "reasoning_tokens": r.reasoning_tokens,
                "cache_read_tokens": r.cache_read_tokens,
                "cache_write_tokens": r.cache_write_tokens,
                "total_tokens": r.total_tokens,
                "estimated_cost": r.estimated_cost,
                "session_id": r.session_id,
                "source_file": r.source_file,
            }
        )

    with open(output, "w") as f:
        json.dump({"records": data, "total_records": len(data)}, f, indent=2)

    print(f"Exported {len(records)} records to {output}")
