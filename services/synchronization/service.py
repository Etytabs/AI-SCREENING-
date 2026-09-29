from dataclasses import dataclass

@dataclass(frozen=True)
class SyncDecision:
    record_id: str
    action: str
    approved_by: str | None = None

def prepare_sync(record_id: str, action: str) -> SyncDecision:
    if action not in {"create", "update", "skip"}:
        raise ValueError("action must be create, update, or skip")
    return SyncDecision(record_id=record_id, action=action)
