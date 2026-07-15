# Contributing to aitrack

Thanks for your interest in improving aitrack.

## Setup

```bash
git clone <repo-url> aitrack
cd aitrack
make dev
```

Requires Python 3.12+.

## Development workflow

```bash
make test    # run the test suite
make lint    # ruff check + format check
make format  # auto-format with ruff
```

Please run `make lint` and `make test` before opening a PR — CI will run
the same checks.

## Adding a new collector

Collectors live in `src/aitrack/collectors/` and implement `BaseCollector`
(`discover()` + `collect()`). See `opencode.py` or `kiro.py` for reference.
When adding a collector:

1. Add discovery paths to `src/aitrack/config.py`.
2. Implement `discover()` to return `DiscoveredSource` entries.
3. Implement `collect()` to return `UsageRecord` entries.
4. Add pricing entries to `_DEFAULT_PRICING` in `utils/pricing.py` if the
   tool/model isn't already covered.
5. Add tests in `tests/test_collectors.py`.
6. Update the "Supported Tools" table in `README.md`.

## Reporting issues

Please include:
- `aitrack --version`
- OS and Python version
- Output of `aitrack discover` (redact any sensitive paths if needed)
- Steps to reproduce

## Pull requests

- Keep PRs focused on a single change.
- Add/update tests for behavior changes.
- Update `CHANGELOG.md` under `[Unreleased]`.
