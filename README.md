# aitrack

**Local-first AI token usage tracker for coding assistants (Opencode, Kiro, and more).**

Tracks token consumption, estimates costs, and provides live usage monitoring — all on your machine, no cloud needed.

## Features

- **Discovery** — automatically finds AI tool data sources on your machine
- **Incremental scanning** — avoids duplicate imports with SHA-256 dedup
- **Daily/weekly/monthly/lifetime stats** — tokens and cost summaries
- **Breakdowns** — by tool, model, and provider
- **Cost calculator** — configurable pricing for all major models
- **Live dashboard** — Textual-based real-time UI
- **File watching** — auto-rescans when data files change
- **Session analytics** — top sessions by tokens/duration/cost
- **Export** — CSV and JSON export for any period

## Supported Tools

| Tool | Data Source | Tokens | Model |
|------|-------------|--------|-------|
| Opencode | `~/.local/share/opencode/opencode.db` | Full (input/output/reasoning/cache) | Full |
| Opencode logs | `~/.local/share/opencode/log/*.log` | Full | Full |
| Kiro | `~/.local/share/kiro-cli/data.sqlite3` | Estimated from word count | Full |
| Generic | JSON/NDJSON/log files in search paths | When available | When available |

## Installation

```bash
# Clone the repo
git clone <url> aitrack
cd aitrack

# Install with pip
pip install -e .

# Or use the Makefile
make install
```

Requires Python 3.12+.

## Quick Start

```bash
# Discover AI tool data sources on your machine
aitrack discover

# Import all discovered data
aitrack scan

# View today's usage
aitrack today

# View lifetime stats
aitrack lifetime

# View cost breakdown
aitrack cost

# Launch the live dashboard
aitrack live

# Watch for file changes and auto-rescan
aitrack watch

# Export data for this month
aitrack export csv --period month
```

## CLI Reference

### `aitrack discover`

Detects AI tools and their data sources on the local machine.

Output: tool name, source type, path, parser compatibility, record count.

### `aitrack scan`

Reads all discovered sources and imports usage records. Skips duplicates using content hashing. Creates the SQLite database at `~/.local/share/aitrack/usage.db`.

### `aitrack today` / `week` / `month` / `lifetime`

Shows:
- Total input, output, reasoning, cache read/write tokens
- Estimated cost
- Breakdown by tool, model, and provider

### `aitrack cost`

- Pricing configuration for all models
- Cost summary by period (today, week, month, lifetime)
- Cost breakdown by provider

### `aitrack watch`

Monitors Opencode and Kiro data directories for file changes. Automatically rescans when changes are detected (debounced at 5s).

### `aitrack live`

Launches a Textual-based terminal dashboard that auto-refreshes every 5 seconds. Shows:
- Today/week/month/lifetime stats panels
- Model leaderboard
- Tool leaderboard

### `aitrack sessions`

Lists all tracked sessions with duration, token count, request count, and cost.

### `aitrack top-sessions`

```
aitrack top-sessions --sort-by tokens --limit 10
```

Sort by: `tokens` (default), `duration`, or `cost`.

### `aitrack export`

```
aitrack export csv --period lifetime --output ./my_data.csv
aitrack export json --period month
```

Periods: `today`, `week`, `month`, `lifetime`.

### `aitrack status`

Quick health check: database path, size, total record count, last activity, and tools tracked.

### `aitrack reset`

Deletes the local usage database. Prompts for confirmation unless `--force`/`-f` is passed. Use this to clear bad data and re-scan from scratch.

```
aitrack reset          # prompts for confirmation
aitrack reset --force  # skips confirmation
```

### Global options

- `--version` — print the installed version and exit.
- `--verbose` / `-v` — enable debug logging to stderr (in addition to the log file at `~/.local/share/aitrack/log/aitrack.log`).

## Pricing Configuration

Pricing is stored at `~/.config/aitrack/pricing.json`. You can edit this file to add or update model pricing.

Default pricing includes:
- GPT-5, Claude Sonnet 4, Claude Opus 4, Claude Haiku 4.5, Gemini 2.5 Pro
- OpenRouter models (catch-all with $0 default)
- Kiro models (auto, claude-haiku-4.5, claude-opus-4.8, glm-5)
- Opencode big-pickle (free)

## Database Schema

`~/.local/share/aitrack/usage.db`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| timestamp | DATETIME | When the usage occurred |
| tool_name | TEXT | Source tool (opencode, kiro, etc.) |
| provider | TEXT | AI provider (openai, anthropic, etc.) |
| model | TEXT | Model ID |
| input_tokens | INTEGER | Prompt/input tokens |
| output_tokens | INTEGER | Completion/output tokens |
| reasoning_tokens | INTEGER | Reasoning tokens |
| cache_read_tokens | INTEGER | Cache read tokens |
| cache_write_tokens | INTEGER | Cache write tokens |
| total_tokens | INTEGER | Sum of all token types |
| estimated_cost | FLOAT | Calculated cost |
| session_id | TEXT | Session or conversation ID |
| source_file | TEXT | Original data source path |
| source_hash | TEXT | SHA-256 dedup hash |

## Example Output

```
$ aitrack today

          Today Usage
╭─────────────┬────────┬───────╮
│ Item        │ Tokens │ Cost  │
├─────────────┼────────┼───────┤
│ Input       │ 70.0K  │ $0.00 │
│ Output      │ 28.7K  │ $0.00 │
│ Reasoning   │ 2.5K   │ -     │
│ Cache Read  │ 2.6M   │ -     │
│ Cache Write │ 0      │ -     │
│ Total       │ 2.7M   │ $0.00 │
╰─────────────┴────────┴───────╯
           Records: 3

             Today by Tool
╭──────────┬────────┬───────┬─────────╮
│ Name     │ Tokens │     % │    Cost │
├──────────┼────────┼───────┼─────────┤
│ opencode │  50.2M │ 99.8% │   $0.00 │
│ kiro     │  84.2K │  0.2% │ $0.3791 │
╰──────────┴────────┴───────┴─────────╯
```

## Architecture

```
aitrack/
├── src/aitrack/
│   ├── cli.py                  # Typer CLI entry point
│   ├── collectors/             # Data source collectors
│   │   ├── opencode.py         # Opencode DB + log scanner
│   │   ├── kiro.py             # Kiro DB scanner
│   │   └── generic.py          # Generic JSON/NDJSON/log scanner
│   ├── commands/               # CLI command implementations
│   │   ├── discover.py         # Source discovery
│   │   ├── scan.py             # Data import
│   │   ├── stats.py            # today/week/month/lifetime
│   │   ├── cost.py             # Cost summaries
│   │   ├── watch.py            # File watcher
│   │   ├── sessions.py         # Session analytics
│   │   ├── status.py           # DB health check
│   │   ├── reset.py            # Clear local database
│   │   └── export_.py          # CSV/JSON export
│   ├── database/               # SQLAlchemy + Repository
│   │   ├── models.py           # ORM models
│   │   └── repository.py       # Data access layer
│   ├── dashboard/              # Textual live dashboard
│   │   └── live_app.py         # Real-time UI
│   ├── models/                 # Pydantic models
│   │   ├── usage_record.py     # Usage data schema
│   │   ├── discovery.py        # Discovery schema
│   │   └── pricing.py          # Pricing schema
│   └── utils/                  # Utilities
│       ├── pricing.py          # Cost calculator
│       ├── formatters.py       # Rich terminal formatting
│       └── logging.py          # Logging setup
├── tests/                      # Test suite (57 tests)
├── pyproject.toml
├── Makefile
└── README.md
```

## Platform Support

Currently tested on Linux (`~/.local/share`, `~/.config` paths). macOS uses different standard paths (`~/Library/Application Support`, `~/Library/Preferences`) which are not yet auto-detected — contributions welcome.

## Testing

```bash
make test        # Run all tests
make lint        # Lint with ruff
make format      # Format with ruff
```

## Development

```bash
make dev    # Install with dev dependencies
make build  # Build distribution packages
make clean  # Clean build artifacts
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on adding new collectors and the development workflow.

## License

MIT — see [LICENSE](LICENSE).
