import json
import logging
import os
import sqlite3
from datetime import UTC, datetime

import tiktoken

from aitrack.collectors.base import BaseCollector
from aitrack.config import KIRO_CONFIG_DIR, KIRO_DB_PATH
from aitrack.models.discovery import DiscoveredSource
from aitrack.models.usage_record import UsageRecord
from aitrack.utils.pricing import calculate_cost

logger = logging.getLogger(__name__)

# Map model names to tiktoken encodings
_MODEL_ENCODING_MAP = {
    "claude-haiku-4.5": "cl100k_base",
    "claude-opus-4.8": "cl100k_base",
    "claude-sonnet-4": "cl100k_base",
    "claude-opus-4": "cl100k_base",
    "glm-5": "cl100k_base",
    "auto": "cl100k_base",
    "gpt-4": "cl100k_base",
    "gpt-4o": "o200k_base",
    "gpt-5": "o200k_base",
}

_DEFAULT_ENCODING = "cl100k_base"


def _get_encoding(model_id: str) -> tiktoken.Encoding:
    """Get the appropriate tiktoken encoding for a model."""
    encoding_name = _MODEL_ENCODING_MAP.get(model_id.lower(), _DEFAULT_ENCODING)
    try:
        return tiktoken.get_encoding(encoding_name)
    except Exception:
        return tiktoken.get_encoding(_DEFAULT_ENCODING)


class KiroCollector(BaseCollector):
    tool_name = "kiro"

    def discover(self) -> list[DiscoveredSource]:
        sources = []
        db_path = KIRO_DB_PATH
        if os.path.exists(db_path):
            count = 0
            try:
                conn = sqlite3.connect(db_path)
                count = conn.execute("SELECT COUNT(*) FROM conversations_v2").fetchone()[0]
                conn.close()
            except Exception as e:
                logger.warning("could not read kiro db: %s", e)
            sources.append(
                DiscoveredSource(
                    tool_name="kiro",
                    source_type="sqlite_db",
                    path=db_path,
                    parser_compatible=True,
                    record_count=count,
                )
            )
        config_dir = KIRO_CONFIG_DIR
        if os.path.isdir(config_dir):
            sources.append(
                DiscoveredSource(
                    tool_name="kiro",
                    source_type="config_dir",
                    path=config_dir,
                    parser_compatible=False,
                )
            )
        return sources

    def collect(self, source: DiscoveredSource) -> list[UsageRecord]:
        if source.source_type == "sqlite_db":
            return self._collect_db(source.path)
        return []

    def _collect_db(self, db_path: str) -> list[UsageRecord]:
        records = []
        try:
            conn = sqlite3.connect(db_path)
            rows = conn.execute(
                """
                SELECT conversation_id, value, created_at, updated_at
                FROM conversations_v2
                """
            ).fetchall()
            conn.close()
        except Exception as e:
            logger.error("failed to read kiro db: %s", e)
            return records

        for row in rows:
            try:
                conversation_id = row[0]
                val_str = row[1]
                created_ms = row[2]

                val = json.loads(val_str) if isinstance(val_str, str) else {}
                model_info = val.get("model_info", {})
                model_name = (
                    model_info.get("model_name", "auto") if isinstance(model_info, dict) else "auto"
                )
                model_id = (
                    model_info.get("model_id", model_name)
                    if isinstance(model_info, dict)
                    else model_name
                )

                timestamp = datetime.fromtimestamp(created_ms / 1000, tz=UTC)

                history = val.get("history", [])
                input_tokens = 0
                output_tokens = 0

                encoding = _get_encoding(model_id)

                for msg in history:
                    user_content = msg.get("user", {}).get("content", {})
                    if isinstance(user_content, dict):
                        prompt = user_content.get("Prompt", {})
                        if isinstance(prompt, dict):
                            input_tokens += len(encoding.encode(prompt.get("prompt", "")))
                    else:
                        input_tokens += len(encoding.encode(str(user_content)))

                    assistant = msg.get("assistant", {})
                    if isinstance(assistant, dict):
                        resp = assistant.get("Response", {})
                        if isinstance(resp, dict):
                            output_tokens += len(encoding.encode(resp.get("content", "")))
                        else:
                            tool_use = assistant.get("ToolUse", {})
                            if isinstance(tool_use, dict):
                                content = tool_use.get("content", "")
                                output_tokens += len(encoding.encode(str(content)))

                estimated_cost = calculate_cost(
                    provider="kiro",
                    model=model_id,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )

                record = UsageRecord(
                    timestamp=timestamp,
                    tool_name="kiro",
                    provider="kiro",
                    model=model_id,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    estimated_cost=estimated_cost,
                    session_id=conversation_id,
                    source_file=db_path,
                )
                records.append(record)
            except Exception as e:
                logger.warning("skipping kiro conversation %s: %s", row[0] if row else "?", e)
                continue

        return records
