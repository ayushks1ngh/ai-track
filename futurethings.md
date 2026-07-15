# Future Improvements

Roadmap of features and enhancements to make aitrack more valuable for every user.

## Tier 1: High Impact, Low Effort

### Support more AI coding tools

Every new collector = a new audience of users.

| Tool | Data Location | Notes |
|------|--------------|-------|
| Cursor | `~/.cursor/` or `~/Library/Application Support/Cursor/` | IDE with built-in AI |
| Windsurf (Codeium) | `~/.codeium/` | AI-powered editor |
| Continue.dev | `~/.continue/` | JSON logs, easy to parse |
| Aider | `~/.aider.chat.history.md` | CLI coding assistant |
| Claude Code (CLI) | `~/.claude/` | Anthropic's CLI tool |
| GitHub Copilot | VS Code extension logs | Widely used |

### First-run experience (`aitrack init`)

Single command that:
- Runs discovery
- Shows what was found
- Asks to scan
- Prints a "here's what to do next" summary

New users shouldn't need to read docs to get started.

### Auto-scan on every command

If the DB hasn't been updated in >1 hour, auto-run a quick scan before showing stats. Users shouldn't need to remember to run `scan` manually.

### `aitrack summary` — daily briefing command

Combine today + this week + trend into one compact output:
```
Today: 45K tokens ($0.12) — 3 sessions
This week: 320K tokens ($0.85)
Trend: ↑ 23% vs last week
Top model today: claude-sonnet-4 (78%)
```

---

## Tier 2: Medium Impact, Medium Effort

### Date range filtering

```bash
aitrack stats --from 2026-07-01 --to 2026-07-07
aitrack cost --period "last 7 days"
```

### `aitrack config` command

```bash
aitrack config show
aitrack config set anthropic/claude-sonnet-4 --input 0.003 --output 0.015
aitrack config add-model <provider> <model> --input <price> --output <price>
```

### Daily/weekly budget alerts

```bash
aitrack config budget --daily 5.00
```

Then on every stat display:
```
⚠️  You've spent $4.20 today (84% of $5.00 daily budget)
```

### Kiro token estimation accuracy

Current approach uses tiktoken (GPT tokenizer) for Claude models — overestimates by ~15-20%. Options:
- Use a Claude-specific tokenizer when available
- Add a configurable correction factor (e.g. `0.85x`)
- Document the limitation clearly in README

### macOS path support

Detect OS and use appropriate paths:
- Linux: `~/.local/share/`, `~/.config/`
- macOS: `~/Library/Application Support/`, `~/Library/Preferences/`

---

## Tier 3: Polish & Community

### Rich one-liner install in README

```bash
pip install local-ai-track && aitrack init
```

### Comparison commands

```bash
aitrack compare --today-vs-yesterday
aitrack compare --this-week-vs-last
```

Shows delta in tokens, cost, and model usage patterns.

### Notifications / hooks

- Webhook on budget exceeded
- Desktop notification when daily spend crosses threshold
- Slack/Discord integration for team usage tracking

### Multi-machine sync

Export/import mechanism to merge usage data from multiple machines into a single view.

### Plugin system for collectors

Let people write their own collector as a pip-installable plugin using entry points:
```bash
pip install aitrack-cursor-collector
```

Discover plugins automatically via `importlib.metadata.entry_points()`.

### Interactive TUI improvements

- Sparkline graphs showing token usage over time
- Model switching patterns visualization
- Session timeline view in the live dashboard
- Color-coded cost thresholds (green/yellow/red)

### API / Web dashboard (stretch)

- Optional local web server (`aitrack serve`) with charts
- REST API for integrations
- Grafana-compatible metrics export

---

## Versioning Plan

| Version | Focus |
|---------|-------|
| v1.0.1 | Bug fixes (time filter fix, etc.) |
| v1.1.0 | `aitrack init`, auto-scan, `summary` command |
| v1.2.0 | Cursor + Claude Code collectors, date range filtering |
| v1.3.0 | Budget alerts, `config` command, macOS support |
| v2.0.0 | Plugin system, web dashboard |
