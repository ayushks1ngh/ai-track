from pydantic import BaseModel


class DiscoveredSource(BaseModel):
    tool_name: str
    source_type: str
    path: str
    parser_compatible: bool
    record_count: int = 0


class DiscoveryResult(BaseModel):
    detected_tools: list[str]
    sources: list[DiscoveredSource]
    errors: list[str] = []
