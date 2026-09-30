from dataclasses import dataclass

from services.ingestion.document import ExtractedDocument


@dataclass(frozen=True)
class CitationLocator:
    document_id: str
    document_version: int
    page_number: int
    start: int
    end: int
    evidence: str

    @property
    def locator(self) -> str:
        return f"{self.document_id}:v{self.document_version}:p{self.page_number}:{self.start}-{self.end}"


def validate_citation(document: ExtractedDocument, citation: CitationLocator) -> bool:
    if citation.document_id != document.source_id:
        return False
    if citation.document_version < 1:
        return False
    if citation.page_number < 1 or citation.page_number > len(document.pages):
        return False
    if citation.start < 0 or citation.end <= citation.start:
        return False

    page = next(page for page in document.pages if page.page_number == citation.page_number)
    if citation.end > len(page.text):
        return False
    return page.text[citation.start:citation.end] == citation.evidence
