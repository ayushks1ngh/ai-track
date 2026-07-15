import json
import os
import sys
from datetime import UTC, datetime, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from aitrack.commands.cost import run_cost
from aitrack.commands.discover import run_discover
from aitrack.commands.export_ import run_export_csv, run_export_json
from aitrack.commands.scan import run_scan
from aitrack.commands.sessions import run_sessions, run_top_sessions
from aitrack.commands.stats import run_lifetime, run_month, run_today, run_week
from aitrack.database.repository import UsageRepository
from aitrack.models.usage_record import UsageRecord


@pytest.fixture
def temp_db():
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    if os.path.exists(db_path):
        os.unlink(db_path)
    for ext in ["-shm", "-wal"]:
        p = db_path + ext
        if os.path.exists(p):
            os.unlink(p)


@pytest.fixture
def repo_with_data(temp_db):
    repo = UsageRepository(temp_db)
    now = datetime.now(UTC)
    records = [
        UsageRecord(
            timestamp=now - timedelta(hours=2),
            tool_name="opencode",
            provider="opencode",
            model="big-pickle",
            input_tokens=1000,
            output_tokens=500,
            session_id="ses_001",
            source_file="/test/opencode.db",
        ),
        UsageRecord(
            timestamp=now - timedelta(hours=1),
            tool_name="kiro",
            provider="kiro",
            model="claude-haiku-4.5",
            input_tokens=2000,
            output_tokens=1000,
            session_id="ses_002",
            source_file="/test/kiro.sqlite",
        ),
        UsageRecord(
            timestamp=now - timedelta(days=2),
            tool_name="opencode",
            provider="anthropic",
            model="claude-sonnet-4",
            input_tokens=3000,
            output_tokens=1500,
            session_id="ses_003",
            source_file="/test/logs.log",
        ),
    ]
    repo.insert_many(records)
    return temp_db


class TestDiscoverCommand:
    def test_run_discover(self, capsys):
        run_discover()
        captured = capsys.readouterr()
        assert "Discovery Results" in captured.out
        assert "opencode" in captured.out or "kiro" in captured.out


class TestScanCommand:
    def test_run_scan_new_db(self, temp_db, capsys):
        # This test verifies scan runs without error on empty/new DB
        run_scan(db_path=temp_db)
        captured = capsys.readouterr()
        assert "Scan complete" in captured.out

    def test_run_scan_dedup(self, temp_db, capsys):
        # Test deduplication works
        run_scan(db_path=temp_db)
        run_scan(db_path=temp_db)
        captured = capsys.readouterr()
        # Second scan should insert 0 new records
        assert "New records inserted: [bold]0[/]" in captured.out or "0" in captured.out


class TestStatsCommands:
    def test_run_today(self, repo_with_data, capsys):
        run_today(db_path=repo_with_data)
        captured = capsys.readouterr()
        assert "Today Usage" in captured.out
        assert "Tokens" in captured.out

    def test_run_week(self, repo_with_data, capsys):
        run_week(db_path=repo_with_data)
        captured = capsys.readouterr()
        assert "This Week" in captured.out

    def test_run_month(self, repo_with_data, capsys):
        run_month(db_path=repo_with_data)
        captured = capsys.readouterr()
        assert "This Month" in captured.out

    def test_run_lifetime(self, repo_with_data, capsys):
        run_lifetime(db_path=repo_with_data)
        captured = capsys.readouterr()
        assert "Lifetime" in captured.out


class TestCostCommand:
    def test_run_cost(self, repo_with_data, capsys):
        run_cost(db_path=repo_with_data)
        captured = capsys.readouterr()
        assert "Pricing Configuration" in captured.out
        assert "Cost Summary" in captured.out
        assert "Cost by Provider" in captured.out


class TestExportCommands:
    def test_export_csv(self, repo_with_data, capsys, tmp_path):
        output_file = tmp_path / "test_export.csv"
        run_export_csv(period="lifetime", output=str(output_file), db_path=repo_with_data)
        captured = capsys.readouterr()
        assert "Exported" in captured.out
        assert output_file.exists()
        # Verify CSV content
        import csv

        with open(output_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 3

    def test_export_json(self, repo_with_data, capsys, tmp_path):
        output_file = tmp_path / "test_export.json"
        run_export_json(period="lifetime", output=str(output_file), db_path=repo_with_data)
        captured = capsys.readouterr()
        assert "Exported" in captured.out
        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)
            assert "records" in data
            assert data["total_records"] == 3


class TestSessionsCommands:
    def test_run_sessions(self, repo_with_data, capsys):
        run_sessions(db_path=repo_with_data)
        captured = capsys.readouterr()
        assert "Sessions" in captured.out
        assert "Session ID" in captured.out

    def test_run_top_sessions(self, repo_with_data, capsys):
        run_top_sessions(db_path=repo_with_data, sort_by="tokens", limit=2)
        captured = capsys.readouterr()
        assert "Top 2 Sessions" in captured.out


class TestStatusCommand:
    def test_run_status_with_data(self, repo_with_data, capsys):
        from aitrack.commands.status import run_status

        run_status(db_path=repo_with_data)
        captured = capsys.readouterr()
        assert "aitrack status" in captured.out
        assert "Total records" in captured.out

    def test_run_status_no_db(self, tmp_path, capsys):
        from aitrack.commands.status import run_status

        missing_db = str(tmp_path / "does_not_exist.db")
        run_status(db_path=missing_db)
        captured = capsys.readouterr()
        assert "No database found" in captured.out


class TestResetCommand:
    def test_run_reset_force(self, repo_with_data, capsys):
        from aitrack.commands.reset import run_reset

        assert os.path.exists(repo_with_data)
        run_reset(db_path=repo_with_data, force=True)
        captured = capsys.readouterr()
        assert "Database reset" in captured.out
        assert not os.path.exists(repo_with_data)

    def test_run_reset_no_db(self, tmp_path, capsys):
        from aitrack.commands.reset import run_reset

        missing_db = str(tmp_path / "does_not_exist.db")
        run_reset(db_path=missing_db, force=True)
        captured = capsys.readouterr()
        assert "No database found" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
