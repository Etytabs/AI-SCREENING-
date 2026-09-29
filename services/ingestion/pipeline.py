from dataclasses import dataclass

from ml.text_normalization.service import normalize_text

@dataclass(frozen=True)
class IngestionRecord:
    source_id: str
    content_type: str
    payload: dict

def ingest(source_id: str, content_type: str, payload: dict) -> IngestionRecord:
    normalized = {
        key: normalize_text(value) if isinstance(value, str) else value
        for key, value in payload.items()
    }
    return IngestionRecord(source_id=source_id, content_type=content_type, payload=normalized)
