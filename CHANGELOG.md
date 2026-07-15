# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- `aitrack status` command showing database size, record count, and last activity.
- `aitrack reset` command to clear the local database.
- `--version` flag.
- `--verbose` / `-v` flag for debug logging.
- Pricing entry for `opencode`/`nemotron-3-ultra-free`.

### Fixed
- Cost breakdown in `today`/`week`/`month`/`lifetime` no longer hardcodes `$0.00`
  for input/output/cache lines; now uses computed per-category costs.
- Opencode log collector no longer imports zero-token "session created" events
  as usage records.
- Generic collector no longer re-scans files already owned by the Opencode/Kiro
  collectors or aitrack's own database, avoiding duplicate/junk records.
- Removed duplicate `_parse_log_kv_pairs` implementation (now single source in
  `config.py`).
- Logging no longer streams to stderr by default (was polluting CLI table
  output); use `--verbose` to enable.

## [1.0.0] - 2026-07-09

### Added
- Initial release: discover, scan, today/week/month/lifetime stats, cost
  summary, live dashboard, watch, sessions, top-sessions, export (CSV/JSON).
- Opencode (SQLite + log) and Kiro (SQLite) collectors.
- Generic JSON/NDJSON/log collector for unknown tools.
- Configurable per-model pricing.
