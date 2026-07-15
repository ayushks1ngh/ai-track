from rich import box
from rich.console import Console
from rich.table import Table

console = Console()


def format_tokens(count: int) -> str:
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    if count >= 1_000:
        return f"{count / 1_000:.1f}K"
    return str(count)


def format_cost(amount: float) -> str:
    if amount == 0:
        return "$0.00"
    if amount < 0.01:
        return f"${amount:.6f}"
    if amount < 1:
        return f"${amount:.4f}"
    return f"${amount:.2f}"


def make_summary_table(title: str, data: list[tuple[str, str, str]], caption: str = "") -> Table:
    table = Table(title=title, box=box.ROUNDED)
    table.add_column("Item", style="cyan")
    table.add_column("Tokens", style="green")
    table.add_column("Cost", style="yellow")
    for item, tokens, cost in data:
        table.add_row(item, tokens, cost)
    if caption:
        table.caption = caption
    return table


def make_breakdown_table(
    title: str,
    breakdown: list[tuple[str, int, float]],
    caption: str = "",
) -> Table:
    table = Table(title=title, box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Tokens", style="green", justify="right")
    table.add_column("%", style="white", justify="right")
    table.add_column("Cost", style="yellow", justify="right")
    if not breakdown:
        table.add_row("(no data)", "0", "0%", "$0.00")
        return table
    total_tokens = sum(t for _, t, _ in breakdown)
    for name, tokens, cost in sorted(breakdown, key=lambda x: -x[1]):
        pct = (tokens / total_tokens * 100) if total_tokens > 0 else 0
        table.add_row(name, format_tokens(tokens), f"{pct:.1f}%", format_cost(cost))
    if caption:
        table.caption = caption
    return table
