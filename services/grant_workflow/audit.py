"""Workflow audit trail on top of services.audit.events.AuditStream."""
import threading
from typing import Any

from services.audit.events import AuditEvent, AuditStream
from services.grant_workflow.models import AuditLogEntry


def _entry(event: AuditEvent) -> AuditLogEntry:
    details = dict(event.details)
    return AuditLogEntry(
        event_type=event.event_type,
        actor=event.actor,
        entity_id=event.entity_id,
        grant_call_id=details.pop("grant_call_id", None),
        timestamp=event.timestamp,
        details=details,
    )


class WorkflowAudit:
    def __init__(self, stream: AuditStream | None = None) -> None:
        self.stream = stream or AuditStream()
        self._lock = threading.Lock()

    def record(self, event_type: str, actor: str, entity_id: str, grant_call_id: str | None, **details: Any) -> AuditLogEntry:
        with self._lock:
            event = self.stream.append(event_type, actor, entity_id, {**details, "grant_call_id": grant_call_id})
        return _entry(event)

    def entries(self, *, grant_call_id: str | None = None, entity_id: str | None = None) -> list[AuditLogEntry]:
        with self._lock:
            events = self.stream.history(entity_id) if entity_id else self.stream.events()
        entries = [_entry(event) for event in events]
        if grant_call_id is not None:
            entries = [entry for entry in entries if entry.grant_call_id == grant_call_id]
        return entries
