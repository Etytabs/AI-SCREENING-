from dataclasses import dataclass
from enum import StrEnum


class SourceAccessStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    RATE_LIMITED = "RATE_LIMITED"
    EXPIRED = "EXPIRED"
    NOT_CONFIGURED = "NOT_CONFIGURED"


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    provider: str
    source_name: str
    source_type: str
    base_url: str | None = None
    dataset: str | None = None
    dataset_version: str | None = None
    coverage: str | None = None
    license: str | None = None
    methodology: str | None = None
    last_success: str | None = None
    last_attempt: str | None = None
    access_status: SourceAccessStatus = SourceAccessStatus.NOT_CONFIGURED
    quota: str | None = None
    freshness: str | None = None


class SourceRegistry:
    def __init__(self, sources: list[SourceRecord] | None = None) -> None:
        self._sources = {source.source_id: source for source in sources or []}

    def register(self, source: SourceRecord) -> None:
        self._sources[source.source_id] = source

    def get(self, source_id: str) -> SourceRecord:
        return self._sources[source_id]

    def list(self) -> tuple[SourceRecord, ...]:
        return tuple(self._sources.values())

    def availability(self, source_id: str) -> SourceAccessStatus:
        return self.get(source_id).access_status
