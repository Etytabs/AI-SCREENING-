from dataclasses import dataclass
from enum import StrEnum


class SourceHealth(StrEnum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    RATE_LIMITED = "RATE_LIMITED"
    EXPIRED = "EXPIRED"
    NOT_CONFIGURED = "NOT_CONFIGURED"


@dataclass(frozen=True)
class SourceHealthRecord:
    source_id: str
    status: SourceHealth
    last_success: str | None
    last_attempt: str | None
    response_status: int | None = None
    quota_status: str | None = None
    coverage: str | None = None

    @property
    def searchable(self) -> bool:
        return self.status in {SourceHealth.AVAILABLE, SourceHealth.DEGRADED}
