"""Persistence boundary for the grant workflow.

`WorkflowRepository` is the interface the service layer depends on. The in-memory
implementation backs the MVP; a PostgreSQL/pgvector implementation can replace it
without changing the service layer or the API contract.
"""
import threading
from typing import Protocol, TypeVar

from pydantic import BaseModel

from services.grant_workflow.models import (
    Applicant,
    Application,
    ApplicationDocument,
    Finding,
    GrantCall,
    Institution,
    PendingUpload,
    ReviewerDecision,
    ReviewerNote,
    RfpCriterion,
    RfpDocument,
    ScreeningBatch,
    ScreeningRun,
)
from services.ingestion.document import ExtractedDocument

T = TypeVar("T", bound=BaseModel)


class WorkflowRepository(Protocol):
    lock: threading.RLock

    def save(self, item: BaseModel) -> None: ...
    def get(self, model: type[T], item_id: str) -> T | None: ...
    def list(self, model: type[T], **filters: object) -> list[T]: ...
    def delete(self, model: type[BaseModel], item_id: str) -> None: ...
    def save_content(self, document_id: str, document: ExtractedDocument) -> None: ...
    def get_content(self, document_id: str) -> ExtractedDocument | None: ...


_ID_FIELDS: dict[type[BaseModel], str] = {
    GrantCall: "id",
    RfpDocument: "id",
    RfpCriterion: "id",
    Applicant: "id",
    Institution: "id",
    Application: "id",
    ApplicationDocument: "id",
    PendingUpload: "id",
    ScreeningRun: "id",
    ScreeningBatch: "id",
    Finding: "finding_id",
    ReviewerDecision: "id",
    ReviewerNote: "id",
}


class InMemoryWorkflowRepository:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self._items: dict[type[BaseModel], dict[str, BaseModel]] = {model: {} for model in _ID_FIELDS}
        self._content: dict[str, ExtractedDocument] = {}

    def save(self, item: BaseModel) -> None:
        model = type(item)
        if model not in _ID_FIELDS:
            raise TypeError(f"Unsupported entity type: {model.__name__}")
        with self.lock:
            self._items[model][getattr(item, _ID_FIELDS[model])] = item.model_copy(deep=True)

    def get(self, model: type[T], item_id: str) -> T | None:
        with self.lock:
            item = self._items[model].get(item_id)
            return item.model_copy(deep=True) if item is not None else None  # type: ignore[return-value]

    def list(self, model: type[T], **filters: object) -> list[T]:
        with self.lock:
            return [
                item.model_copy(deep=True)  # type: ignore[misc]
                for item in self._items[model].values()
                if all(getattr(item, key) == value for key, value in filters.items())
            ]

    def delete(self, model: type[BaseModel], item_id: str) -> None:
        with self.lock:
            self._items[model].pop(item_id, None)

    def save_content(self, document_id: str, document: ExtractedDocument) -> None:
        with self.lock:
            self._content[document_id] = document

    def get_content(self, document_id: str) -> ExtractedDocument | None:
        with self.lock:
            return self._content.get(document_id)
