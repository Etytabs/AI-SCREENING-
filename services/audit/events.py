from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    actor: str
    entity_id: str
    timestamp: datetime
    details: dict


def create_event(event_type: str, actor: str, entity_id: str, details: dict) -> AuditEvent:
    return AuditEvent(event_type, actor, entity_id, datetime.now(UTC), details)
