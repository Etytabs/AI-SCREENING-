from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    actor: str
    entity_id: str
    timestamp: datetime
    details: dict


class AuditStream:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def append(
        self,
        event_type: str,
        actor: str,
        entity_id: str,
        details: dict,
    ) -> AuditEvent:
        event = AuditEvent(
            event_type=event_type,
            actor=actor,
            entity_id=entity_id,
            timestamp=datetime.now(UTC),
            details=dict(details),
        )
        self._events.append(event)
        return event

    def history(self, entity_id: str) -> tuple[AuditEvent, ...]:
        return tuple(event for event in self._events if event.entity_id == entity_id)

    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)


def create_event(event_type: str, actor: str, entity_id: str, details: dict) -> AuditEvent:
    return AuditStream().append(event_type, actor, entity_id, details)
