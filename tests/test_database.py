from datetime import UTC, datetime, timedelta

from aitrack.database.repository import UsageRepository


class TestUsageRepository:
    def test_insert_and_count(self, repo: UsageRepository, sample_records):
        inserted = repo.insert_many(sample_records)
        assert inserted == 3
        assert repo.total_records() == 3

    def test_dedup(self, repo: UsageRepository, sample_records):
        repo.insert_many(sample_records)
        inserted = repo.insert_many(sample_records)
        assert inserted == 0
        assert repo.total_records() == 3

    def test_query_by_tool(self, repo: UsageRepository, sample_records):
        repo.insert_many(sample_records)
        records = repo.query(tool_name="opencode")
        assert len(records) == 2

    def test_query_by_provider(self, repo: UsageRepository, sample_records):
        repo.insert_many(sample_records)
        records = repo.query(provider="kiro")
        assert len(records) == 1

    def test_aggregate(self, repo: UsageRepository, sample_records):
        repo.insert_many(sample_records)
        result = repo.aggregate()
        assert len(result) == 1
        assert result[0]["total_tokens"] > 0

    def test_aggregate_group_by_tool(self, repo: UsageRepository, sample_records):
        repo.insert_many(sample_records)
        result = repo.aggregate(group_by="tool_name")
        assert len(result) == 2

    def test_get_unique_sessions(self, repo: UsageRepository, sample_records):
        repo.insert_many(sample_records)
        sessions = repo.get_unique_sessions()
        assert len(sessions) == 3

    def test_time_range_query(self, repo: UsageRepository, sample_records):
        repo.insert_many(sample_records)
        now = datetime.now(UTC)
        recent = repo.query(start=now - timedelta(minutes=30))
        assert len(recent) == 1

    def test_time_helpers(self, repo: UsageRepository):
        today = repo.get_today_start()
        assert today.hour == 0
        assert today.minute == 0
        assert today.second == 0

    def test_aggregate_with_costs_per_category(self, repo: UsageRepository):
        from aitrack.models.usage_record import UsageRecord

        record = UsageRecord(
            timestamp=datetime.now(UTC),
            tool_name="opencode",
            provider="anthropic",
            model="claude-sonnet-4",
            input_tokens=1000,
            output_tokens=1000,
            cache_read_tokens=1000,
            cache_write_tokens=1000,
            session_id="ses_cost_test",
            source_file="/test/cost.db",
        )
        repo.insert(record)
        result = repo.aggregate_with_costs()

        # claude-sonnet-4 pricing: input 0.003, output 0.015, cache_read 0.0003, cache_write 0.00375 per 1k
        assert result["total_input_cost"] > 0
        assert result["total_output_cost"] > 0
        assert result["total_cache_read_cost"] > 0
        assert result["total_cache_write_cost"] > 0
        assert result["total_output_cost"] > result["total_input_cost"]
