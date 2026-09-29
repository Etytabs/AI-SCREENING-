from dataclasses import dataclass

@dataclass(frozen=True)
class IngestionRecord:
    source_id: str
    content_type: str
    payload: dict

def ingest(source_id: str, content_type: str, payload: dict) -> IngestionRecord:
    return IngestionRecord(source_id=source_id, content_type=content_type, payload=payload)
