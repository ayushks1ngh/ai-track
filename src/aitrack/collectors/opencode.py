import json
import logging
import os
import sqlite3
from datetime import UTC, datetime

from aitrack.collectors.base import BaseCollector
from aitrack.config import OPENCODE_DB_PATH, OPENCODE_LOG_DIR, _parse_log_kv_pairs
from aitrack.models.discovery import DiscoveredSource
from aitrack.models.usage_record import UsageRecord
from aitrack.utils.pricing import calculate_cost

logger = logging.getLogger(__name__)


class OpencodeCollector(BaseCollector):
    tool_name = "opencode"

    def discover(self) -> list[DiscoveredSource]:
        sources = []
        db_path = OPENCODE_DB_PATH
        if os.path.exists(db_path):
            count = 0
            try:
                conn = sqlite3.connect(db_path)
                count = conn.execute("SELECT COUNT(*) FROM session").fetchone()[0]
                conn.close()
            except Exception as e:
                logger.warning("could not read opencode db: %s", e)
            sources.append(
                DiscoveredSource(
                    tool_name="opencode",
                    source_type="sqlite_db",
                    path=db_path,
                    parser_compatible=True,
                    record_count=count,
                )
            )
        log_dir = OPENCODE_LOG_DIR
        if os.path.isdir(log_dir):
            for f in os.listdir(log_dir):
                if f.endswith(".log"):
                    fpath = os.path.join(log_dir, f)
                    sources.append(
                        DiscoveredSource(
                            tool_name="opencode",
                            source_type="log_file",
                            path=fpath,
                            parser_compatible=True,
                        )
                    )
        return sources

    def collect(self, source: DiscoveredSource) -> list[UsageRecord]:
        if source.source_type == "sqlite_db":
            return self._collect_db(source.path)
        if source.source_type == "log_file":
            return self._collect_log(source.path)
        return []

    def _collect_db(self, db_path: str) -> list[UsageRecord]:
        records = []
        try:
            conn = sqlite3.connect(db_path)
            rows = conn.execute(
                """
                SELECT id, slug, model, agent, cost,
                       tokens_input, tokens_output, tokens_reasoning,
                       tokens_cache_read, tokens_cache_write,
                       time_created, time_updated
                FROM session
                """
            ).fetchall()
            conn.close()
        except Exception as e:
            logger.error("failed to read opencode db: %s", e)
            return records

        for row in rows:
            try:
                session_id = row[0]
                _ = row[1] or ""
                model_raw = row[2] or "{}"
                _ = row[3] or ""
                cost_val = row[4] or 0
                tokens_input = row[5] or 0
                tokens_output = row[6] or 0
                tokens_reasoning = row[7] or 0
                tokens_cache_read = row[8] or 0
                tokens_cache_write = row[9] or 0
                time_created_ms = row[10]

                model_data = json.loads(model_raw) if isinstance(model_raw, str) else model_raw
                model_id = (
                    model_data.get("id", "unknown") if isinstance(model_data, dict) else "unknown"
                )
                provider_id = (
                    model_data.get("providerID", "opencode")
                    if isinstance(model_data, dict)
                    else "opencode"
                )

                timestamp = datetime.fromtimestamp(time_created_ms / 1000, tz=UTC)

                estimated_cost = calculate_cost(
                    provider=provider_id,
                    model=model_id,
                    input_tokens=tokens_input,
                    output_tokens=tokens_output,
                    cache_read_tokens=tokens_cache_read,
                    cache_write_tokens=tokens_cache_write,
                )
                if cost_val and cost_val > 0:
                    estimated_cost = cost_val

                record = UsageRecord(
                    timestamp=timestamp,
                    tool_name="opencode",
                    provider=provider_id,
                    model=model_id,
                    input_tokens=tokens_input,
                    output_tokens=tokens_output,
                    reasoning_tokens=tokens_reasoning,
                    cache_read_tokens=tokens_cache_read,
                    cache_write_tokens=tokens_cache_write,
                    estimated_cost=estimated_cost,
                    session_id=session_id,
                    source_file=db_path,
                )
                records.append(record)
            except Exception as e:
                logger.warning("skipping opencode session %s: %s", row[0] if row else "?", e)
                continue
        return records

    def _collect_log(self, log_path: str) -> list[UsageRecord]:
        records = []
        try:
            with open(log_path) as f:
                for line in f:
                    line = line.strip()
                    if "message=created" not in line:
                        continue
                    record = self._parse_log_line(line, log_path)
                    if record:
                        records.append(record)
        except Exception as e:
            logger.error("failed to read opencode log: %s", e)
        return records

    def _parse_log_line(self, line: str, log_path: str = "") -> UsageRecord | None:
        try:
            parts = _parse_log_kv_pairs(line)

            timestamp_str = parts.get("timestamp", "")
            timestamp = (
                datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                if timestamp_str
                else datetime.now(UTC)
            )

            session_id = parts.get("id", "")
            cost_val = float(parts.get("cost", 0))
            tokens_input = int(parts.get("tokens.input", 0))
            tokens_output = int(parts.get("tokens.output", 0))
            tokens_reasoning = int(parts.get("tokens.reasoning", 0))
            tokens_cache_read = int(parts.get("tokens.cache.read", 0))
            tokens_cache_write = int(parts.get("tokens.cache.write", 0))
            model_id = parts.get("model.id", "unknown")
            provider_id = parts.get("model.providerID", "opencode")
            _ = parts.get("agent", "")

            estimated_cost = calculate_cost(
                provider=provider_id,
                model=model_id,
                input_tokens=tokens_input,
                output_tokens=tokens_output,
                cache_read_tokens=tokens_cache_read,
                cache_write_tokens=tokens_cache_write,
            )
            if cost_val > 0:
                estimated_cost = cost_val

            # Skip zero-token records (e.g. session "created" events carry no
            # usage data; actual token counts are tracked in the sqlite DB).
            if (
                tokens_input == 0
                and tokens_output == 0
                and tokens_reasoning == 0
                and tokens_cache_read == 0
                and tokens_cache_write == 0
            ):
                return None

            return UsageRecord(
                timestamp=timestamp,
                tool_name="opencode",
                provider=provider_id,
                model=model_id,
                input_tokens=tokens_input,
                output_tokens=tokens_output,
                reasoning_tokens=tokens_reasoning,
                cache_read_tokens=tokens_cache_read,
                cache_write_tokens=tokens_cache_write,
                estimated_cost=estimated_cost,
                session_id=session_id,
                source_file=log_path,
            )
        except Exception as e:
            logger.debug("failed to parse opencode log line: %s", e)
            return None
