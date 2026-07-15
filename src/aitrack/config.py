"""Centralized configuration constants for aitrack."""

import os
import re

# Database paths
DEFAULT_DB_PATH = os.path.expanduser("~/.local/share/aitrack/usage.db")
AITRACK_LOG_DIR = os.path.expanduser("~/.local/share/aitrack/log")

# Opencode paths
OPENCODE_DB_PATH = os.path.expanduser("~/.local/share/opencode/opencode.db")
OPENCODE_LOG_DIR = os.path.expanduser("~/.local/share/opencode/log")
OPENCODE_CONFIG_DIR = os.path.expanduser("~/.config/opencode")

# Kiro paths
KIRO_DB_PATH = os.path.expanduser("~/.local/share/kiro-cli/data.sqlite3")
KIRO_CONFIG_DIR = os.path.expanduser("~/.kiro")

# Generic collector search patterns
SEARCH_PATTERNS = [
    os.path.expanduser("~/.local/share/*/log/*.log"),
    os.path.expanduser("~/.local/share/*/usage*"),
    os.path.expanduser("~/.cache/*/usage*"),
    os.path.expanduser("~/.config/*/usage*"),
]

# Regex to parse key=value pairs, handling quoted values with spaces
LOG_KV_PATTERN = re.compile(r'(\w+(?:\.\w+)*)=("(?:[^"\\]|\\.)*"|[^"\s]+)')


def _parse_log_kv_pairs(line: str) -> dict[str, str]:
    """Parse key=value pairs from a log line, handling quoted values with spaces."""
    result = {}
    for match in LOG_KV_PATTERN.finditer(line):
        key = match.group(1)
        value = match.group(2)
        # Remove surrounding quotes if present
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        result[key] = value
    return result


# Watch intervals
WATCH_DEBOUNCE_SECONDS = 5
LIVE_REFRESH_SECONDS = 5

# Session limits
TOP_SESSIONS_LIMIT = 10
LIVE_MODEL_LEADERBOARD_LIMIT = 10
