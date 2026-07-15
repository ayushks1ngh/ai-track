from datetime import datetime

from pydantic import BaseModel


class UsageRecord(BaseModel):
    timestamp: datetime
    tool_name: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    session_id: str = ""
    source_file: str = ""

    def model_post_init(self, _context) -> None:
        self.total_tokens = (
            self.input_tokens
            + self.output_tokens
            + self.reasoning_tokens
            + self.cache_read_tokens
            + self.cache_write_tokens
        )
