import logging

from rich import box
from rich.panel import Panel
from rich.table import Table

from aitrack.config import DEFAULT_DB_PATH
from aitrack.database.repository import UsageRepository
from aitrack.utils.formatters import console, format_cost
from aitrack.utils.pricing import get_pricing

logger = logging.getLogger(__name__)


def run_cost(db_path: str = DEFAULT_DB_PATH) -> None:
    repo = UsageRepository(db_path)

    pricing = get_pricing()

    console.print(Panel("[bold]Pricing Configuration[/]", style="cyan"))
    price_table = Table(box=box.SIMPLE)
    price_table.add_column("Provider", style="cyan")
    price_table.add_column("Model", style="green")
    price_table.add_column("Input/1K", justify="right")
    price_table.add_column("Output/1K", justify="right")
    price_table.add_column("Cache R/1K", justify="right")
    price_table.add_column("Cache W/1K", justify="right")
    for mp in pricing.models:
        price_table.add_row(
            mp.provider,
            mp.model_id,
            format_cost(mp.input_price_per_1k),
            format_cost(mp.output_price_per_1k),
            format_cost(mp.cache_read_price_per_1k),
            format_cost(mp.cache_write_price_per_1k),
        )
    console.print(price_table)

    today_start = repo.get_today_start()
    week_start = repo.get_week_start()
    month_start = repo.get_month_start()

    today_data = repo.aggregate(start=today_start)
    week_data = repo.aggregate(start=week_start)
    month_data = repo.aggregate(start=month_start)
    lifetime_data = repo.aggregate()

    cost_rows = [
        ("Today", format_cost(today_data[0]["total_cost"]) if today_data else "$0.00"),
        ("This Week", format_cost(week_data[0]["total_cost"]) if week_data else "$0.00"),
        ("This Month", format_cost(month_data[0]["total_cost"]) if month_data else "$0.00"),
        ("Lifetime", format_cost(lifetime_data[0]["total_cost"]) if lifetime_data else "$0.00"),
    ]

    cost_table = Table(title="Cost Summary", box=box.ROUNDED)
    cost_table.add_column("Period", style="cyan")
    cost_table.add_column("Cost", style="yellow", justify="right")
    for period, cost in cost_rows:
        cost_table.add_row(period, cost)
    console.print(cost_table)

    provider_costs = repo.aggregate(group_by="provider")
    if provider_costs:
        prov_table = Table(title="Cost by Provider", box=box.ROUNDED)
        prov_table.add_column("Provider", style="cyan")
        prov_table.add_column("Tokens", style="green", justify="right")
        prov_table.add_column("Cost", style="yellow", justify="right")
        for pc in sorted(provider_costs, key=lambda x: -x["total_cost"]):
            if pc["total_tokens"] > 0:
                prov_table.add_row(
                    pc["group"], f"{pc['total_tokens']:,}", format_cost(pc["total_cost"])
                )
        console.print(prov_table)
