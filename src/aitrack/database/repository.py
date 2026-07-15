import hashlib
import logging
import os
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, func
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session as DBSession

from aitrack.database.models import Base, UsageRecordDB
from aitrack.models.usage_record import UsageRecord
from aitrack.utils.pricing import get_pricing

logger = logging.getLogger(__name__)


class UsageRepository:
    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)

    def _make_hash(self, record: UsageRecord) -> str:
        raw = f"{record.session_id}|{record.tool_name}|{record.timestamp.isoformat()}|{record.input_tokens}|{record.output_tokens}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def record_exists(self, session: DBSession, record_hash: str) -> bool:
        return (
            session.query(UsageRecordDB).filter(UsageRecordDB.source_hash == record_hash).first()
            is not None
        )

    def insert(self, record: UsageRecord) -> bool:
        record_hash = self._make_hash(record)
        with DBSession(self.engine) as session:
            if self.record_exists(session, record_hash):
                return False
            db_record = UsageRecordDB(
                timestamp=record.timestamp,
                tool_name=record.tool_name,
                provider=record.provider,
                model=record.model,
                input_tokens=record.input_tokens,
                output_tokens=record.output_tokens,
                reasoning_tokens=record.reasoning_tokens,
                cache_read_tokens=record.cache_read_tokens,
                cache_write_tokens=record.cache_write_tokens,
                total_tokens=record.total_tokens,
                estimated_cost=record.estimated_cost,
                session_id=record.session_id,
                source_file=record.source_file,
                source_hash=record_hash,
            )
            session.add(db_record)
            session.commit()
            return True

    def insert_many(self, records: list[UsageRecord]) -> int:
        """Bulk insert using INSERT OR IGNORE for deduplication."""
        if not records:
            return 0

        # Prepare data for bulk insert
        insert_data = []
        for record in records:
            record_hash = self._make_hash(record)
            insert_data.append(
                {
                    "timestamp": record.timestamp,
                    "tool_name": record.tool_name,
                    "provider": record.provider,
                    "model": record.model,
                    "input_tokens": record.input_tokens,
                    "output_tokens": record.output_tokens,
                    "reasoning_tokens": record.reasoning_tokens,
                    "cache_read_tokens": record.cache_read_tokens,
                    "cache_write_tokens": record.cache_write_tokens,
                    "total_tokens": record.total_tokens,
                    "estimated_cost": record.estimated_cost,
                    "session_id": record.session_id,
                    "source_file": record.source_file,
                    "source_hash": record_hash,
                }
            )

        with DBSession(self.engine) as session:
            # Use INSERT OR IGNORE to skip duplicates based on unique constraint
            stmt = sqlite_insert(UsageRecordDB).values(insert_data)
            # Use the unique column name for ON CONFLICT
            stmt = stmt.on_conflict_do_nothing(index_elements=["source_hash"])
            result = session.execute(stmt)
            session.commit()
            # rowcount returns number of rows inserted (not ignored)
            return result.rowcount

    def query(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        tool_name: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> list[UsageRecordDB]:
        with DBSession(self.engine) as session:
            q = session.query(UsageRecordDB)
            if start:
                q = q.filter(UsageRecordDB.timestamp >= start)
            if end:
                q = q.filter(UsageRecordDB.timestamp <= end)
            if tool_name:
                q = q.filter(UsageRecordDB.tool_name == tool_name)
            if provider:
                q = q.filter(UsageRecordDB.provider == provider)
            if model:
                q = q.filter(UsageRecordDB.model == model)
            return list(q.all())

    def aggregate(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        group_by: str | None = None,
    ) -> list[dict]:
        with DBSession(self.engine) as session:
            base = session.query(
                func.sum(UsageRecordDB.input_tokens).label("total_input"),
                func.sum(UsageRecordDB.output_tokens).label("total_output"),
                func.sum(UsageRecordDB.reasoning_tokens).label("total_reasoning"),
                func.sum(UsageRecordDB.cache_read_tokens).label("total_cache_read"),
                func.sum(UsageRecordDB.cache_write_tokens).label("total_cache_write"),
                func.sum(UsageRecordDB.total_tokens).label("total_tokens"),
                func.sum(UsageRecordDB.estimated_cost).label("total_cost"),
                func.count(UsageRecordDB.id).label("record_count"),
            )
            if start:
                base = base.filter(UsageRecordDB.timestamp >= start)
            if end:
                base = base.filter(UsageRecordDB.timestamp <= end)
            if group_by:
                col = getattr(UsageRecordDB, group_by, None)
                if col:
                    base = session.query(
                        col.label("group_name"),
                        func.sum(UsageRecordDB.input_tokens).label("total_input"),
                        func.sum(UsageRecordDB.output_tokens).label("total_output"),
                        func.sum(UsageRecordDB.reasoning_tokens).label("total_reasoning"),
                        func.sum(UsageRecordDB.cache_read_tokens).label("total_cache_read"),
                        func.sum(UsageRecordDB.cache_write_tokens).label("total_cache_write"),
                        func.sum(UsageRecordDB.total_tokens).label("total_tokens"),
                        func.sum(UsageRecordDB.estimated_cost).label("total_cost"),
                        func.count(UsageRecordDB.id).label("record_count"),
                    ).group_by(col)
                    rows = base.all()
                    return [
                        {
                            "group": r.group_name or "unknown",
                            "total_input": r.total_input or 0,
                            "total_output": r.total_output or 0,
                            "total_reasoning": r.total_reasoning or 0,
                            "total_cache_read": r.total_cache_read or 0,
                            "total_cache_write": r.total_cache_write or 0,
                            "total_tokens": r.total_tokens or 0,
                            "total_cost": float(r.total_cost or 0),
                            "record_count": r.record_count or 0,
                        }
                        for r in rows
                    ]
            result = base.first()
            return [
                {
                    "group": "overall",
                    "total_input": result.total_input or 0,
                    "total_output": result.total_output or 0,
                    "total_reasoning": result.total_reasoning or 0,
                    "total_cache_read": result.total_cache_read or 0,
                    "total_cache_write": result.total_cache_write or 0,
                    "total_tokens": result.total_tokens or 0,
                    "total_cost": float(result.total_cost or 0),
                    "record_count": result.record_count or 0,
                }
            ]

    def aggregate_with_costs(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> dict:
        """Aggregate tokens and compute costs using per-token rates from pricing config."""
        pricing = get_pricing()
        with DBSession(self.engine) as session:
            base = session.query(
                UsageRecordDB.provider,
                UsageRecordDB.model,
                func.sum(UsageRecordDB.input_tokens).label("total_input"),
                func.sum(UsageRecordDB.output_tokens).label("total_output"),
                func.sum(UsageRecordDB.reasoning_tokens).label("total_reasoning"),
                func.sum(UsageRecordDB.cache_read_tokens).label("total_cache_read"),
                func.sum(UsageRecordDB.cache_write_tokens).label("total_cache_write"),
                func.sum(UsageRecordDB.total_tokens).label("total_tokens"),
                func.sum(UsageRecordDB.estimated_cost).label("total_cost"),
                func.count(UsageRecordDB.id).label("record_count"),
            )
            if start:
                base = base.filter(UsageRecordDB.timestamp >= start)
            if end:
                base = base.filter(UsageRecordDB.timestamp <= end)
            rows = base.group_by(UsageRecordDB.provider, UsageRecordDB.model).all()

        total_input = 0
        total_output = 0
        total_reasoning = 0
        total_cache_read = 0
        total_cache_write = 0
        total_tokens = 0
        total_cost = 0.0
        total_input_cost = 0.0
        total_output_cost = 0.0
        total_cache_read_cost = 0.0
        total_cache_write_cost = 0.0
        record_count = 0

        for r in rows:
            provider = r.provider or "unknown"
            model = r.model or "unknown"
            pricing_entry = pricing.find(provider, model)
            if pricing_entry is None:
                pricing_entry = pricing.find(provider, "*")

            input_cost = 0.0
            output_cost = 0.0
            cache_read_cost = 0.0
            cache_write_cost = 0.0

            if pricing_entry:
                input_cost = (r.total_input or 0) / 1000 * pricing_entry.input_price_per_1k
                output_cost = (r.total_output or 0) / 1000 * pricing_entry.output_price_per_1k
                cache_read_cost = (
                    (r.total_cache_read or 0) / 1000 * pricing_entry.cache_read_price_per_1k
                )
                cache_write_cost = (
                    (r.total_cache_write or 0) / 1000 * pricing_entry.cache_write_price_per_1k
                )

            row_cost = input_cost + output_cost + cache_read_cost + cache_write_cost

            total_input += r.total_input or 0
            total_output += r.total_output or 0
            total_reasoning += r.total_reasoning or 0
            total_cache_read += r.total_cache_read or 0
            total_cache_write += r.total_cache_write or 0
            total_tokens += r.total_tokens or 0
            total_cost += row_cost
            total_input_cost += input_cost
            total_output_cost += output_cost
            total_cache_read_cost += cache_read_cost
            total_cache_write_cost += cache_write_cost
            record_count += r.record_count or 0

        return {
            "group": "overall",
            "total_input": total_input,
            "total_output": total_output,
            "total_reasoning": total_reasoning,
            "total_cache_read": total_cache_read,
            "total_cache_write": total_cache_write,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "total_input_cost": total_input_cost,
            "total_output_cost": total_output_cost,
            "total_cache_read_cost": total_cache_read_cost,
            "total_cache_write_cost": total_cache_write_cost,
            "record_count": record_count,
        }

    def get_unique_sessions(self) -> list[dict]:
        with DBSession(self.engine) as session:
            rows = (
                session.query(
                    UsageRecordDB.session_id,
                    func.min(UsageRecordDB.timestamp).label("first_seen"),
                    func.max(UsageRecordDB.timestamp).label("last_seen"),
                    func.sum(UsageRecordDB.total_tokens).label("total_tokens"),
                    func.sum(UsageRecordDB.estimated_cost).label("total_cost"),
                    func.count(UsageRecordDB.id).label("requests"),
                )
                .filter(UsageRecordDB.session_id != "")
                .group_by(UsageRecordDB.session_id)
                .all()
            )
            result = []
            for r in rows:
                duration = None
                if r.last_seen and r.first_seen:
                    duration = (r.last_seen - r.first_seen).total_seconds()
                result.append(
                    {
                        "session_id": r.session_id,
                        "first_seen": r.first_seen,
                        "last_seen": r.last_seen,
                        "duration_seconds": duration,
                        "total_tokens": r.total_tokens or 0,
                        "total_cost": float(r.total_cost or 0),
                        "requests": r.requests or 0,
                    }
                )
            return result

    def get_today_start(self) -> datetime:
        return datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    def get_week_start(self) -> datetime:
        now = datetime.now(UTC)
        start = now - timedelta(days=now.weekday())
        return start.replace(hour=0, minute=0, second=0, microsecond=0)

    def get_month_start(self) -> datetime:
        now = datetime.now(UTC)
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def total_records(self) -> int:
        with DBSession(self.engine) as session:
            return session.query(func.count(UsageRecordDB.id)).scalar() or 0
