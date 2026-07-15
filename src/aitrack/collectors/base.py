from abc import ABC, abstractmethod

from aitrack.models.discovery import DiscoveredSource
from aitrack.models.usage_record import UsageRecord


class BaseCollector(ABC):
    tool_name: str = "unknown"

    @abstractmethod
    def discover(self) -> list[DiscoveredSource]: ...

    @abstractmethod
    def collect(self, source: DiscoveredSource) -> list[UsageRecord]: ...
