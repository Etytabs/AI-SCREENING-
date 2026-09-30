"""Upload handling around the existing document extractor.

Text extraction always goes through services.ingestion.document.extract_document; this
module only stages bytes, expands ZIP archives, groups files into applications and reads
explicitly stated metadata. Missing metadata stays missing.
"""
import io
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from tempfile import NamedTemporaryFile

from services.grant_workflow.text_utils import parse_amounts, parse_durations
from services.ingestion.document import ExtractedDocument, extract_document

SUPPORTED_SUFFIXES = {".pdf", ".docx", ".txt"}
MAX_ZIP_FILES = 2000
MAX_ZIP_BYTES = 200 * 1024 * 1024


class UploadError(ValueError):
    pass


@dataclass(frozen=True)
class UploadedFile:
    path: str
    data: bytes

    @property
    def filename(self) -> str:
        return PurePosixPath(self.path).name

    @property
    def suffix(self) -> str:
        return PurePosixPath(self.path).suffix.lower()


def extract_bytes(filename: str, data: bytes, source_id: str) -> ExtractedDocument:
    suffix = Path(filename).suffix.lower()
    if not data:
        raise UploadError(f"{filename}: file is empty")
    if suffix not in SUPPORTED_SUFFIXES:
        raise UploadError(f"{filename}: unsupported file type {suffix or '(none)'}; use PDF, DOCX or TXT")
    # Windows cannot reopen a NamedTemporaryFile while it is still open.
    with NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
    try:
        extracted = extract_document(tmp.name, source_id)
    finally:
        Path(tmp.name).unlink(missing_ok=True)
    # Keep the user's filename rather than the temporary one.
    return ExtractedDocument(
        extracted.source_id, filename, extracted.content_type, extracted.text, extracted.page_count,
        extracted.extraction_status, extracted.file_sha256, extracted.pages, extracted.error,
    )


def expand_uploads(files: list[UploadedFile]) -> tuple[list[UploadedFile], list[str]]:
    """Expand ZIP archives into member files. Returns (files, errors)."""
    expanded: list[UploadedFile] = []
    errors: list[str] = []
    for upload in files:
        if upload.suffix != ".zip":
            expanded.append(upload)
            continue
        try:
            with zipfile.ZipFile(io.BytesIO(upload.data)) as archive:
                members = [m for m in archive.infolist() if not m.is_dir()]
                if len(members) > MAX_ZIP_FILES:
                    raise UploadError(f"{upload.filename}: more than {MAX_ZIP_FILES} files")
                if sum(m.file_size for m in members) > MAX_ZIP_BYTES:
                    raise UploadError(f"{upload.filename}: uncompressed size exceeds limit")
                for member in members:
                    parts = PurePosixPath(member.filename).parts
                    if not parts or parts[0] == "__MACOSX" or parts[-1].startswith("."):
                        continue
                    expanded.append(UploadedFile(member.filename, archive.read(member)))
        except (zipfile.BadZipFile, UploadError) as exc:
            errors.append(f"{upload.filename}: {exc}" if isinstance(exc, zipfile.BadZipFile) else str(exc))
    return expanded, errors


_REFERENCE_PREFIX = re.compile(r"^(?P<ref>[A-Za-z0-9][A-Za-z0-9\-]{2,})__(?P<rest>.+)$")


def group_uploads(files: list[UploadedFile]) -> tuple[dict[str, list[UploadedFile]], list[UploadedFile]]:
    """Associate files with application references.

    Recognized conventions: a folder per application (``REF/file.pdf``) or a
    double-underscore prefix (``REF__file.pdf``). Anything else needs manual association.
    """
    folder_parts = [PurePosixPath(f.path).parts for f in files if len(PurePosixPath(f.path).parts) > 1]
    roots = {parts[0] for parts in folder_parts}
    strip_root = len(roots) == 1 and all(len(parts) > 2 for parts in folder_parts) and bool(folder_parts)

    groups: dict[str, list[UploadedFile]] = {}
    unassigned: list[UploadedFile] = []
    for upload in files:
        parts = PurePosixPath(upload.path).parts
        if strip_root:
            parts = parts[1:]
        if len(parts) > 1:
            groups.setdefault(parts[0], []).append(upload)
            continue
        match = _REFERENCE_PREFIX.match(parts[-1])
        if match:
            groups.setdefault(match.group("ref"), []).append(upload)
        else:
            unassigned.append(upload)
    return groups, unassigned


_CONTENT_CUES = {
    "cv": ("curriculum vitae",),
    "budget": ("budget",),
    "partner_letter": ("letter of commitment", "letter of support"),
    "ethics": ("ethics",),
    "declaration": ("declaration",),
}


def classify_document(filename: str, extracted: ExtractedDocument | None) -> str:
    name = re.sub(r"[_\-.]+", " ", Path(filename).stem.lower())
    filename_cues = {
        "partner_letter": ("partner", "letter", "support", "commitment"),
        "cv": ("cv", "resume", "curriculum", "biosketch"),
        "budget": ("budget",),
        "ethics": ("ethic", "irb"),
        "declaration": ("declaration",),
        "workplan": ("workplan", "work plan", "gantt"),
        "proposal": ("proposal", "narrative", "concept"),
    }
    for doc_type, cues in filename_cues.items():
        if any(re.search(rf"(?<![a-z]){cue}", name) for cue in cues):
            return doc_type
    if extracted and extracted.pages and extracted.pages[0].lines:
        first = extracted.pages[0].lines[0].lower()
        for doc_type, cues in _CONTENT_CUES.items():
            if any(cue in first for cue in cues):
                return doc_type
    return "other"


@dataclass
class ApplicationMetadata:
    title: str | None = None
    applicant_name: str | None = None
    email: str | None = None
    phone: str | None = None
    institution_name: str | None = None
    institution_type: str | None = None
    country: str | None = None
    domain: str | None = None
    requested_amount: float | None = None
    currency: str | None = None
    duration_months: float | None = None
    sources: dict[str, str] = field(default_factory=dict)


_FIELD_KEYS = {
    "title": "title",
    "project title": "title",
    "applicant": "applicant_name",
    "principal investigator": "applicant_name",
    "lead applicant": "applicant_name",
    "email": "email",
    "phone": "phone",
    "institution": "institution_name",
    "organisation": "institution_name",
    "organization": "institution_name",
    "institution type": "institution_type",
    "country": "country",
    "domain": "domain",
    "research domain": "domain",
}


def parse_metadata(documents: list[tuple[str, ExtractedDocument]]) -> ApplicationMetadata:
    """Read explicit ``Key: value`` fields, proposal documents first. Never guesses."""
    metadata = ApplicationMetadata()
    ordered = sorted(documents, key=lambda item: 0 if item[0] == "proposal" else 1)
    for _, document in ordered:
        for page in document.pages:
            for line in page.lines:
                key, sep, value = line.partition(":")
                if not sep or not value.strip():
                    continue
                key_norm = key.strip().lower()
                value = value.strip()
                attribute = _FIELD_KEYS.get(key_norm)
                if attribute and getattr(metadata, attribute) is None:
                    setattr(metadata, attribute, value)
                    metadata.sources[attribute] = f"{document.filename} p.{page.page_number}"
                if key_norm in {"requested amount", "total requested", "amount requested"} and metadata.requested_amount is None:
                    amounts = parse_amounts(value)
                    if amounts:
                        metadata.requested_amount, metadata.currency = amounts[0].value, amounts[0].currency
                        metadata.sources["requested_amount"] = f"{document.filename} p.{page.page_number}"
                if key_norm in {"duration", "project duration"} and metadata.duration_months is None:
                    durations = parse_durations(value)
                    if durations:
                        metadata.duration_months = durations[0].months
                        metadata.sources["duration_months"] = f"{document.filename} p.{page.page_number}"
    return metadata
