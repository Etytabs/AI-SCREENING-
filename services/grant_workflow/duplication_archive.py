"""Persistent, local comparison library for submitted and funded proposals.

Only explicitly uploaded records and snapshots of real submissions enter this store.
The archive is a duplication source, never a source of eligibility requirements.
"""
import hashlib
import json
import os
import sqlite3
import unicodedata
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from threading import Lock
from typing import Any, Iterator, Literal
from uuid import uuid4

from pydantic import BaseModel

from services.grant_workflow.documents import extract_bytes
from services.grant_workflow.models import Application, ApplicationDocument, DataOrigin
from services.grant_workflow.providers import HistoricalRecord, ProviderUnavailable
from services.ingestion.document import ExtractedDocument, ExtractedPage
from services.sources.registry import SourceAccessStatus

MAX_IMPORT_BYTES = 20 * 1024 * 1024
ProjectSourceType = Literal["historical_application", "funded_project"]


class ArchiveValidationError(ValueError):
    """A project cannot be compared because its content or metadata is invalid."""


class DuplicateProjectError(ValueError):
    def __init__(self, project: "ArchivedProject") -> None:
        self.project = project
        super().__init__(f'This content is already in the comparison library as "{project.title}" ({project.id}).')


class ArchivedProject(BaseModel):
    id: str
    title: str
    source_type: ProjectSourceType
    reference: str | None = None
    year: int | None = None
    organization: str | None = None
    filename: str | None = None
    text_length: int
    created_at: datetime
    data_origin: DataOrigin = DataOrigin.UPLOADED
    application_id: str | None = None
    grant_call_id: str | None = None


def _content_hash(text: str) -> str:
    canonical = " ".join(unicodedata.normalize("NFKC", text).casefold().split())
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _clean(value: str | None, name: str, limit: int) -> str | None:
    value = value.strip() if value else None
    if value and len(value) > limit:
        raise ArchiveValidationError(f"{name} must be at most {limit} characters")
    return value or None


def _readable(text: str) -> bool:
    return bool(text.strip()) and any(char.isalnum() for char in text) and "\x00" not in text


class DuplicationArchive:
    provider_id = "uploaded_project_library"

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path or os.getenv("AI_SCREENING_DUPLICATION_DB", "data/private/duplication.sqlite3")).expanduser().resolve()
        self._initialized = False
        self._initialization_lock = Lock()

    def _initialize(self) -> None:
        # Defer all storage access until a duplication operation. An unavailable
        # library must not prevent the API or the eligibility workflow starting.
        with self._initialization_lock:
            if self._initialized:
                return
            self.path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self.path, timeout=30)
            try:
                with conn:
                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.execute("""
                CREATE TABLE IF NOT EXISTS duplication_projects (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    source_type TEXT NOT NULL CHECK(source_type IN ('historical_application', 'funded_project')),
                    reference TEXT,
                    year INTEGER,
                    organization TEXT,
                    filename TEXT,
                    text TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    application_id TEXT UNIQUE,
                    grant_call_id TEXT,
                    provenance TEXT NOT NULL
                )
            """)
                    conn.execute("CREATE INDEX IF NOT EXISTS duplication_content_hash ON duplication_projects(content_hash)")
            finally:
                conn.close()
            self._initialized = True

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        # Each operation owns its connection, including operations from worker threads.
        self._initialize()
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    @staticmethod
    def _metadata(row: sqlite3.Row) -> ArchivedProject:
        return ArchivedProject(
            id=row["id"], title=row["title"], source_type=row["source_type"],
            reference=row["reference"], year=row["year"], organization=row["organization"],
            filename=row["filename"], text_length=row["text_length"], created_at=row["created_at"],
            application_id=row["application_id"], grant_call_id=row["grant_call_id"],
        )

    def status(self) -> SourceAccessStatus:
        try:
            with self._connection() as conn:
                conn.execute("SELECT 1 FROM duplication_projects LIMIT 1")
            return SourceAccessStatus.AVAILABLE
        except (sqlite3.Error, OSError):
            return SourceAccessStatus.UNAVAILABLE

    def list_projects(self) -> list[ArchivedProject]:
        with self._connection() as conn:
            rows = conn.execute("""
                SELECT id, title, source_type, reference, year, organization, filename,
                       length(text) AS text_length, created_at, application_id, grant_call_id
                FROM duplication_projects ORDER BY created_at DESC, id
            """).fetchall()
        return [self._metadata(row) for row in rows]

    def import_document(
        self, *, filename: str, data: bytes, title: str, source_type: ProjectSourceType,
        reference: str | None = None, year: int | None = None,
        organization: str | None = None, uploaded_by: str | None = None,
    ) -> ArchivedProject:
        if len(data) > MAX_IMPORT_BYTES:
            raise ArchiveValidationError("Project document exceeds the 20 MB upload limit")
        filename = PurePosixPath(filename.replace("\\", "/")).name
        if Path(filename).suffix.lower() == ".txt":
            try:
                decoded = data.decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                raise ArchiveValidationError("TXT documents must contain readable UTF-8 text") from exc
            if not _readable(decoded):
                raise ArchiveValidationError("Document contains no readable proposal text")
        record_id = f"project_{uuid4().hex}"
        try:
            extracted = extract_bytes(filename, data, record_id)
        except Exception as exc:
            raise ArchiveValidationError("Could not read this document; upload a valid PDF, DOCX or TXT file") from exc
        if extracted.extraction_status != "success" or not _readable(extracted.text):
            raise ArchiveValidationError("Document contains no readable proposal text; scanned PDFs need text extraction first")
        provenance = {
            "kind": "library_import", "uploaded_by": uploaded_by,
            "file_sha256": extracted.file_sha256,
            "content_type": extracted.content_type,
            "pages": [{"page_number": p.page_number, "text": p.text, "lines": list(p.lines)} for p in extracted.pages],
        }
        return self._store(
            record_id=record_id, title=title, source_type=source_type, text=extracted.text,
            reference=reference, year=year, organization=organization, filename=filename,
            application_id=None, grant_call_id=None, provenance=provenance,
        )

    def snapshot_submission(
        self, *, application_id: str, grant_call_id: str, title: str, text: str,
        reference: str | None = None, year: int | None = None,
        organization: str | None = None, filename: str | None = None,
        provenance: dict[str, Any] | None = None,
    ) -> ArchivedProject:
        """Idempotently replace one application's narrative; separate submissions stay separate."""
        if not application_id or not grant_call_id:
            raise ArchiveValidationError("Submission snapshots require application and grant call IDs")
        return self._store(
            record_id=f"project_{uuid4().hex}", title=title, source_type="historical_application",
            text=text, reference=reference, year=year, organization=organization, filename=filename,
            application_id=application_id, grant_call_id=grant_call_id,
            provenance={**(provenance or {}), "kind": "submission_snapshot"},
        )

    def snapshot_application(
        self, application: Application,
        documents: list[tuple[ApplicationDocument, ExtractedDocument]],
        organization: str | None = None,
    ) -> ArchivedProject | None:
        """Snapshot the service-selected narrative documents without archiving demo data."""
        if application.data_origin != DataOrigin.UPLOADED:
            return None
        readable = [(meta, doc) for meta, doc in documents if doc.extraction_status == "success" and _readable(doc.text)]
        if not readable:
            return None
        return self.snapshot_submission(
            application_id=application.id, grant_call_id=application.grant_call_id,
            title=application.title or application.application_reference,
            text="\n\n".join(
                "\n\n".join("\n".join(page.lines) if page.lines else page.text for page in doc.pages)
                if doc.pages else doc.text
                for _, doc in readable
            ),
            reference=application.application_reference,
            year=application.submitted_at.year, organization=organization,
            filename=readable[0][0].filename if len(readable) == 1 else None,
            provenance={
                "submitted_at": application.submitted_at.isoformat(),
                "documents": [
                    {
                        "document_id": meta.id, "filename": meta.filename,
                        "version": meta.version, "file_sha256": doc.file_sha256,
                        "content_type": doc.content_type, "document_type": meta.document_type,
                        "uploaded_at": meta.uploaded_at.isoformat(), "uploaded_by": meta.uploaded_by,
                        "pages": [{"page_number": p.page_number, "text": p.text, "lines": list(p.lines)} for p in doc.pages],
                    }
                    for meta, doc in readable
                ],
            },
        )

    def _store(
        self, *, record_id: str, title: str, source_type: str, text: str,
        reference: str | None, year: int | None, organization: str | None,
        filename: str | None, application_id: str | None, grant_call_id: str | None,
        provenance: dict[str, Any],
    ) -> ArchivedProject:
        title = _clean(title, "Title", 500)
        if not title:
            raise ArchiveValidationError("A project title is required")
        if source_type not in {"historical_application", "funded_project"}:
            raise ArchiveValidationError("Choose a previously submitted application or a funded project")
        if year is not None and not 1000 <= year <= 9999:
            raise ArchiveValidationError("Year must be a four-digit year")
        if not _readable(text):
            raise ArchiveValidationError("Document contains no readable proposal text")
        reference = _clean(reference, "Reference", 200)
        organization = _clean(organization, "Organization", 500)
        content_hash = _content_hash(text)
        now = datetime.now(UTC).isoformat()
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            if application_id is None:
                existing = conn.execute("""
                    SELECT *, length(text) AS text_length FROM duplication_projects
                    WHERE content_hash = ? AND application_id IS NULL AND source_type = ?
                    ORDER BY created_at, id LIMIT 1
                """, (content_hash, source_type)).fetchone()
                if existing is not None:
                    raise DuplicateProjectError(self._metadata(existing))
            conn.execute("""
                INSERT INTO duplication_projects (
                    id, title, source_type, reference, year, organization, filename, text,
                    content_hash, created_at, updated_at, application_id, grant_call_id, provenance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(application_id) DO UPDATE SET
                    title=excluded.title, reference=excluded.reference, year=excluded.year,
                    organization=excluded.organization, filename=excluded.filename,
                    text=excluded.text, content_hash=excluded.content_hash, updated_at=excluded.updated_at,
                    grant_call_id=excluded.grant_call_id, provenance=excluded.provenance
            """, (
                record_id, title, source_type, reference, year, organization, filename, text.strip(),
                content_hash, now, now, application_id, grant_call_id, json.dumps(provenance),
            ))
            if application_id is not None:
                row = conn.execute("SELECT *, length(text) AS text_length FROM duplication_projects WHERE application_id = ?", (application_id,)).fetchone()
            else:
                row = conn.execute("SELECT *, length(text) AS text_length FROM duplication_projects WHERE id = ?", (record_id,)).fetchone()
        assert row is not None
        return self._metadata(row)

    def historical_records(self, *, exclude_application_id: str | None = None) -> list[HistoricalRecord]:
        try:
            with self._connection() as conn:
                rows = conn.execute("""
                    SELECT * FROM duplication_projects
                    WHERE application_id IS NULL OR application_id != ?
                    ORDER BY created_at, id
                """, (exclude_application_id or "",)).fetchall()
        except (sqlite3.Error, OSError) as exc:
            raise ProviderUnavailable("The uploaded project comparison library could not be read") from exc
        records = []
        for row in rows:
            provenance = json.loads(row["provenance"])
            provenance.update({
                "filename": row["filename"], "reference": row["reference"],
                "created_at": row["created_at"], "provider_id": self.provider_id,
            })
            document = None
            document_meta = None
            text = row["text"]
            source = None
            if provenance.get("kind") == "submission_snapshot":
                documents = provenance.get("documents", [])
                if documents:
                    text = "\n\n".join(
                        "\n\n".join("\n".join(p["lines"]) if p.get("lines") else p["text"] for p in item.get("pages", []))
                        for item in documents
                    ) or text
                    if len(documents) == 1:
                        source = documents[0]
            elif provenance.get("kind") == "library_import":
                source = provenance
            if source is not None:
                pages = tuple(ExtractedPage(p["page_number"], p["text"], tuple(p.get("lines", []))) for p in source.get("pages", []))
                document_id = source.get("document_id", row["id"])
                filename = source.get("filename") or row["filename"] or row["title"]
                document = ExtractedDocument(
                    source_id=document_id, filename=filename,
                    content_type=source.get("content_type", "application/octet-stream"), text=text, page_count=len(pages),
                    extraction_status="success", file_sha256=source.get("file_sha256"), pages=pages,
                )
                document_meta = ApplicationDocument(
                    id=document_id, application_id=row["application_id"] or row["id"],
                    filename=filename, document_type=source.get("document_type", "proposal"), file_hash=source.get("file_sha256"),
                    version=source.get("version", 1), uploaded_at=source.get("uploaded_at", row["created_at"]),
                    uploaded_by=source.get("uploaded_by") or "library-import",
                    extraction_status="success", page_count=len(pages), provenance=provenance,
                )
            records.append(HistoricalRecord(
                record_id=row["id"], title=row["title"], text=text,
                source_type=row["source_type"], year=row["year"],
                outcome="funded" if row["source_type"] == "funded_project" else "submitted",
                organization=row["organization"], data_origin=DataOrigin.UPLOADED,
                application_id=row["application_id"], grant_call_id=row["grant_call_id"],
                provenance=provenance, document=document, document_meta=document_meta,
            ))
        return records
