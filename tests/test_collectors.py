import json
import os
import sys
from unittest.mock import patch

import pytest
import tiktoken

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from aitrack.collectors.generic import GenericCollector
from aitrack.collectors.kiro import KiroCollector
from aitrack.collectors.opencode import OpencodeCollector
from aitrack.config import _parse_log_kv_pairs
from aitrack.models.discovery import DiscoveredSource


class TestOpencodeCollector:
    def test_parse_log_kv_pairs_simple(self):
        line = "timestamp=2026-07-08T09:06:42.927Z level=INFO id=ses_test cost=0 tokens.input=1000 tokens.output=500 model.id=big-pickle model.providerID=opencode"
        result = _parse_log_kv_pairs(line)
        assert result["timestamp"] == "2026-07-08T09:06:42.927Z"
        assert result["level"] == "INFO"
        assert result["id"] == "ses_test"
        assert result["cost"] == "0"
        assert result["tokens.input"] == "1000"
        assert result["tokens.output"] == "500"
        assert result["model.id"] == "big-pickle"
        assert result["model.providerID"] == "opencode"

    def test_parse_log_kv_pairs_with_quoted_values(self):
        line = 'message="hello world" key=value'
        result = _parse_log_kv_pairs(line)
        assert result["message"] == "hello world"
        assert result["key"] == "value"

    def test_parse_log_kv_pairs_with_spaces_in_value(self):
        line = 'model.id="claude sonnet 4" provider=anthropic'
        result = _parse_log_kv_pairs(line)
        assert result["model.id"] == "claude sonnet 4"

    def test_collector_discovery(self, tmp_path):
        db_file = tmp_path / "opencode.db"
        db_file.write_text("dummy")
        log_dir = tmp_path / "log"
        log_dir.mkdir()
        log_file = log_dir / "opencode.log"
        log_file.write_text("dummy")

        with patch("aitrack.collectors.opencode.OPENCODE_DB_PATH", str(db_file)):
            with patch("aitrack.collectors.opencode.OPENCODE_LOG_DIR", str(log_dir)):
                collector = OpencodeCollector()
                sources = collector.discover()
                assert len(sources) == 2
                assert sources[0].source_type == "sqlite_db"
                assert sources[1].source_type == "log_file"


class TestKiroCollector:
    def test_collector_discovery(self, tmp_path):
        db_file = tmp_path / "data.sqlite3"
        db_file.write_text("dummy")

        with patch("aitrack.collectors.kiro.KIRO_DB_PATH", str(db_file)):
            with patch("aitrack.collectors.kiro.KIRO_CONFIG_DIR", str(tmp_path / "kiro")):
                collector = KiroCollector()
                sources = collector.discover()
                assert len(sources) == 1
                assert sources[0].source_type == "sqlite_db"

    def test_get_encoding_for_model(self):
        from aitrack.collectors.kiro import _MODEL_ENCODING_MAP, _get_encoding

        # Test known models
        for model, expected_encoding in _MODEL_ENCODING_MAP.items():
            encoding = _get_encoding(model)
            assert encoding.name == expected_encoding

        # Test unknown model falls back to default
        encoding = _get_encoding("unknown-model-xyz")
        assert encoding.name == "cl100k_base"


class TestGenericCollector:
    def test_parse_log_kv_pairs(self):
        line = "timestamp=2026-07-08T09:06:42.927Z provider=openai model.id=gpt-5 tokens.input=1000 tokens.output=500"
        result = _parse_log_kv_pairs(line)
        assert result["provider"] == "openai"
        assert result["model.id"] == "gpt-5"

    def test_parse_json_list(self, tmp_path):
        data = [
            {
                "tool": "test",
                "provider": "test",
                "model": "test",
                "input_tokens": 100,
                "output_tokens": 50,
                "timestamp": "2026-07-08T09:06:42.927Z",
            }
        ]
        json_file = tmp_path / "usage.json"
        json_file.write_text(json.dumps(data))

        collector = GenericCollector()
        sources = [
            DiscoveredSource(
                tool_name="generic",
                source_type="file_json",
                path=str(json_file),
                parser_compatible=True,
            )
        ]
        records = []
        for source in sources:
            records.extend(collector.collect(source))

        assert len(records) == 1
        assert records[0].input_tokens == 100
        assert records[0].output_tokens == 50

    def test_parse_ndjson(self, tmp_path):
        lines = [
            json.dumps(
                {
                    "tool": "test",
                    "provider": "test",
                    "model": "test",
                    "input_tokens": 100,
                    "output_tokens": 50,
                }
            ),
            json.dumps(
                {
                    "tool": "test2",
                    "provider": "test2",
                    "model": "test2",
                    "input_tokens": 200,
                    "output_tokens": 100,
                }
            ),
        ]
        ndjson_file = tmp_path / "usage.ndjson"
        ndjson_file.write_text("\n".join(lines))

        collector = GenericCollector()
        sources = [
            DiscoveredSource(
                tool_name="generic",
                source_type="file_ndjson",
                path=str(ndjson_file),
                parser_compatible=True,
            )
        ]
        records = []
        for source in sources:
            records.extend(collector.collect(source))

        assert len(records) == 2

    def test_parse_log_line(self, tmp_path):
        line = "timestamp=2026-07-08T09:06:42.927Z provider=openai model.id=gpt-5 tokens.input=1000 tokens.output=500 session_id=ses_123"
        log_file = tmp_path / "usage.log"
        log_file.write_text(line)

        collector = GenericCollector()
        sources = [
            DiscoveredSource(
                tool_name="generic",
                source_type="file_log",
                path=str(log_file),
                parser_compatible=True,
            )
        ]
        records = []
        for source in sources:
            records.extend(collector.collect(source))

        assert len(records) == 1
        assert records[0].provider == "openai"
        assert records[0].model == "gpt-5"
        assert records[0].input_tokens == 1000
        assert records[0].output_tokens == 500
        assert records[0].session_id == "ses_123"


class TestCollectorIntegration:
    """Integration tests using sample data structures."""

    def test_opencode_log_parsing_real_format(self):
        """Test parsing actual opencode log format from reconnaissance."""
        line = 'timestamp=2026-07-08T09:06:42.927Z level=INFO run=cd87041e message=created id=ses_0bf053f91ffelEQ3ixCQxarhuQ slug=nimble-sailor version=1.17.13 projectID=global directory=/home/ayush path=home/ayush workspaceID=undefined parentID=undefined title="New session - 2026-07-08T09:06:42.927Z" agent=plan model.id=big-pickle model.providerID=opencode metadata=undefined permission=undefined cost=0 tokens.input=0 tokens.output=0 tokens.reasoning=0 tokens.cache.read=0 tokens.cache.write=0 time.created=1783501602927 time.updated=1783501602927'

        result = _parse_log_kv_pairs(line)
        assert result["id"] == "ses_0bf053f91ffelEQ3ixCQxarhuQ"
        assert result["model.id"] == "big-pickle"
        assert result["model.providerID"] == "opencode"
        assert result["tokens.input"] == "0"
        assert result["tokens.output"] == "0"

    def test_opencode_log_skips_zero_token_records(self):
        """Session 'created' events with all-zero tokens should not become records."""
        line = "timestamp=2026-07-08T09:06:42.927Z level=INFO run=cd87041e message=created id=ses_zero model.id=big-pickle model.providerID=opencode cost=0 tokens.input=0 tokens.output=0 tokens.reasoning=0 tokens.cache.read=0 tokens.cache.write=0"
        collector = OpencodeCollector()
        record = collector._parse_log_line(line, "dummy.log")
        assert record is None

    def test_opencode_log_keeps_nonzero_token_records(self):
        line = "timestamp=2026-07-08T09:06:42.927Z level=INFO message=created id=ses_nonzero model.id=big-pickle model.providerID=opencode cost=0 tokens.input=100 tokens.output=50 tokens.reasoning=0 tokens.cache.read=0 tokens.cache.write=0"
        collector = OpencodeCollector()
        record = collector._parse_log_line(line, "dummy.log")
        assert record is not None
        assert record.input_tokens == 100
        assert record.output_tokens == 50

    def test_generic_collector_excludes_opencode_log_dir(self, tmp_path):
        """Generic collector should not double-scan files owned by dedicated collectors."""
        import aitrack.collectors.generic as generic_mod

        log_dir = tmp_path / "opencode_log"
        log_dir.mkdir()
        log_file = log_dir / "opencode.log"
        log_file.write_text("timestamp=x tokens.input=1 tokens.output=1")

        with (
            patch.object(generic_mod, "_EXCLUDED_DIRS", {str(log_dir)}),
            patch.object(generic_mod, "SEARCH_PATTERNS", [str(log_dir / "*.log")]),
        ):
            collector = GenericCollector()
            sources = collector.discover()
            assert all(s.path != str(log_file) for s in sources)


class TestTiktokenEncoding:
    """Test that tiktoken encoding works correctly for Kiro models."""

    def test_claude_haiku_encoding(self):
        encoding = tiktoken.get_encoding("cl100k_base")
        text = "Hello, world! This is a test."
        tokens = encoding.encode(text)
        assert len(tokens) > 0

    def test_multiline_text_encoding(self):
        encoding = tiktoken.get_encoding("cl100k_base")
        text = "def hello():\n    print('world')\n"
        tokens = encoding.encode(text)
        assert len(tokens) > 5  # Should tokenize code properly


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
