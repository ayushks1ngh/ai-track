import logging
from datetime import UTC, datetime, timedelta

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import DataTable, Footer, Header, Static

from aitrack.config import LIVE_MODEL_LEADERBOARD_LIMIT, LIVE_REFRESH_SECONDS
from aitrack.database.repository import UsageRepository
from aitrack.utils.formatters import format_cost, format_tokens

logger = logging.getLogger(__name__)


class StatsPanel(Static):
    def __init__(self, label: str, panel_id: str) -> None:
        super().__init__(id=panel_id)
        self.label = label
        self.panel_id = panel_id

    def compose(self) -> ComposeResult:
        yield Static(f"[bold]{self.label}[/]", id=f"{self.panel_id}-title")
        yield Static("Loading...", id=f"{self.panel_id}-content")


class LiveDashboard(App):
    TITLE = "aitrack live"
    CSS = """
    StatsPanel {
        height: 5;
        padding: 1;
        border: solid $primary;
    }
    #today-panel { background: $success 10%; }
    #week-panel { background: $accent 10%; }
    #month-panel { background: $warning 10%; }
    #lifetime-panel { background: $error 10%; }
    DataTable { height: 12; }
    """

    def __init__(self, db_path: str):
        super().__init__()
        self.db_path = db_path
        self.repo = UsageRepository(db_path)

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            with Horizontal():
                yield StatsPanel("Today", "today-panel")
                yield StatsPanel("This Week", "week-panel")
                yield StatsPanel("This Month", "month-panel")
                yield StatsPanel("Lifetime", "lifetime-panel")
            yield Static("[bold]Model Leaderboard[/]", classes="section-title")
            yield DataTable(id="model-table")
            yield Static("[bold]Tool Leaderboard[/]", classes="section-title")
            yield DataTable(id="tool-table")
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(LIVE_REFRESH_SECONDS, self.refresh_data)
        self.refresh_data()

    def refresh_data(self) -> None:
        try:
            now = datetime.now(UTC)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - timedelta(days=now.weekday())
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            today = self.repo.aggregate(start=today_start)
            week = self.repo.aggregate(start=week_start)
            month = self.repo.aggregate(start=month_start)
            lifetime = self.repo.aggregate()

            self._update_panel("today-panel", today)
            self._update_panel("week-panel", week)
            self._update_panel("month-panel", month)
            self._update_panel("lifetime-panel", lifetime)

            self._update_model_table()
            self._update_tool_table()
        except Exception as e:
            logger.error("refresh error: %s", e)

    def _update_panel(self, panel_id: str, data: list) -> None:
        panel = self.query_one(f"#{panel_id}", StatsPanel)
        content = panel.query_one(f"#{panel_id}-content", Static)
        if data and data[0]["total_tokens"] > 0:
            d = data[0]
            content.update(
                f"Tokens: [green]{format_tokens(d['total_tokens'])}[/]  "
                f"Cost: [yellow]{format_cost(d['total_cost'])}[/]  "
                f"Records: {d['record_count']}"
            )
        else:
            content.update("No data yet")

    def _update_model_table(self) -> None:
        table = self.query_one("#model-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Model", "Tokens", "Cost")

        model_data = self.repo.aggregate(group_by="model")
        for m in sorted(model_data, key=lambda x: -x["total_tokens"])[
            :LIVE_MODEL_LEADERBOARD_LIMIT
        ]:
            if m["total_tokens"] > 0:
                table.add_row(
                    m["group"], format_tokens(m["total_tokens"]), format_cost(m["total_cost"])
                )

    def _update_tool_table(self) -> None:
        table = self.query_one("#tool-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Tool", "Tokens", "Cost")

        tool_data = self.repo.aggregate(group_by="tool_name")
        for t in sorted(tool_data, key=lambda x: -x["total_tokens"]):
            if t["total_tokens"] > 0:
                table.add_row(
                    t["group"], format_tokens(t["total_tokens"]), format_cost(t["total_cost"])
                )
