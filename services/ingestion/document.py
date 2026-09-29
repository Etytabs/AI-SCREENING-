from dataclasses import dataclass
from pathlib import Path
from ml.text_normalization.service import normalize_text

@dataclass(frozen=True)
class ExtractedDocument:
    source_id: str
    filename: str
    content_type: str
    text: str
    page_count: int | None
    extraction_status: str
    error: str | None = None

def extract_document(path: str, source_id: str) -> ExtractedDocument:
    file = Path(path)
    suffix = file.suffix.lower()
    try:
        if suffix == ".pdf":
            import fitz
            with fitz.open(file) as doc:
                pages = [normalize_text(page.get_text("text")) for page in doc]
            return ExtractedDocument(source_id, file.name, "application/pdf", "\n\n".join(pages), len(pages), "success")
        if suffix == ".docx":
            from docx import Document
            doc = Document(file)
            text = normalize_text("\n".join(p.text for p in doc.paragraphs if p.text.strip()))
            return ExtractedDocument(source_id, file.name, "application/vnd.openxmlformats-officedocument.wordprocessingml.document", text, None, "success")
        return ExtractedDocument(source_id, file.name, "application/octet-stream", "", None, "unsupported_type", f"Unsupported file type: {suffix or 'none'}")
    except Exception as exc:
        return ExtractedDocument(source_id, file.name, "application/octet-stream", "", None, "extraction_failed", str(exc))
