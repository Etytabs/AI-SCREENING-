import re
from dataclasses import dataclass, field
from typing import Literal

SourceType = Literal["api", "oai_pmh", "discovery"]


@dataclass(frozen=True)
class SourceDefinition:
    source_id: str
    name: str
    source_type: SourceType
    base_url: str
    scope: str
    full_text: bool
    metadata: bool
    enabled: bool = True
    notes: str = ""


@dataclass(frozen=True)
class ResearchRecord:
    record_id: str
    title: str
    abstract: str = ""
    authors: tuple[str, ...] = ()
    publication_date: str | None = None
    journal: str | None = None
    doi: str | None = None
    pmid: str | None = None
    arxiv_id: str | None = None
    source_id: str = ""
    source_url: str | None = None
    full_text_url: str | None = None
    keywords: tuple[str, ...] = ()
    affiliations: tuple[str, ...] = ()
    license: str | None = None
    provenance: dict[str, str] = field(default_factory=dict)

    def searchable_text(self) -> str:
        return " ".join(part for part in (self.title, self.abstract, " ".join(self.keywords)) if part)


def record_deduplication_key(record_id: str, doi: str | None = None) -> str:
    normalized_doi = (doi or "").strip().casefold()
    normalized_doi = re.sub(
        r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)",
        "",
        normalized_doi,
    )
    if normalized_doi:
        return f"doi:{normalized_doi.rstrip(' .')}"
    return f"record:{record_id.strip().casefold()}"
