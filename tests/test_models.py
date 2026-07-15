from datetime import UTC, datetime

from aitrack.models.discovery import DiscoveredSource, DiscoveryResult
from aitrack.models.usage_record import UsageRecord


class TestUsageRecord:
    def test_total_tokens_auto(self):
        r = UsageRecord(
            timestamp=datetime.now(UTC),
            tool_name="test",
            provider="test",
            model="test",
            input_tokens=100,
            output_tokens=50,
        )
        assert r.total_tokens == 150

    def test_total_tokens_with_reasoning(self):
        r = UsageRecord(
            timestamp=datetime.now(UTC),
            tool_name="test",
            provider="test",
            model="test",
            input_tokens=100,
            output_tokens=50,
            reasoning_tokens=25,
            cache_read_tokens=500,
            cache_write_tokens=100,
        )
        assert r.total_tokens == 775


class TestDiscoveryResult:
    def test_discovery_creation(self):
        src = DiscoveredSource(
            tool_name="opencode",
            source_type="sqlite_db",
            path="/test/db.sqlite",
            parser_compatible=True,
            record_count=10,
        )
        result = DiscoveryResult(
            detected_tools=["opencode"],
            sources=[src],
        )
        assert len(result.detected_tools) == 1
        assert result.sources[0].record_count == 10
