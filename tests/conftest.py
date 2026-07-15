import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from datetime import UTC, datetime, timedelta

import pytest

from aitrack.database.repository import UsageRepository
from aitrack.models.usage_record import UsageRecord


@pytest.fixture
def db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def repo(db_path):
    return UsageRepository(db_path)


@pytest.fixture
def sample_records():
    now = datetime.now(UTC)
    return [
        UsageRecord(
            timestamp=now - timedelta(hours=2),
            tool_name="opencode",
            provider="opencode",
            model="big-pickle",
            input_tokens=1000,
            output_tokens=500,
            session_id="ses_001",
            source_file="/test/db.sqlite",
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
            timestamp=now,
            tool_name="opencode",
            provider="anthropic",
            model="claude-sonnet-4",
            input_tokens=3000,
            output_tokens=1500,
            session_id="ses_003",
            source_file="/test/logs.log",
        ),
    ]
