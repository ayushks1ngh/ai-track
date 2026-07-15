from sqlalchemy import Column, DateTime, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class UsageRecordDB(Base):
    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    tool_name = Column(String, nullable=False, index=True)
    provider = Column(String, nullable=False, index=True)
    model = Column(String, nullable=False, index=True)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    reasoning_tokens = Column(Integer, default=0)
    cache_read_tokens = Column(Integer, default=0)
    cache_write_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    session_id = Column(String, default="")
    source_file = Column(String, default="")
    source_hash = Column(String, default="", index=True)

    __table_args__ = (
        Index("idx_tool_timestamp", "tool_name", "timestamp"),
        Index("idx_provider_model", "provider", "model"),
        UniqueConstraint("source_hash", name="uq_source_hash"),
    )
