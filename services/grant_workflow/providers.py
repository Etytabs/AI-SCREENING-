"""Replaceable grant-data providers and the research-source registry.

The core workflow runs entirely on local/synthetic data. RIGMS and external scholarly
sources are optional, authorization-dependent connectors.
"""
import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from services.grant_workflow.literature import PublishedLiteratureSource

from services.grant_workflow.models import ApplicationDocument, DataOrigin
from services.ingestion.document import ExtractedDocument
from services.sources.registry import SourceAccessStatus, SourceRecord, SourceRegistry


class ProviderUnavailable(RuntimeError):
    """Raised when a provider cannot be searched. Not equivalent to zero results."""


@dataclass(frozen=True)
class HistoricalRecord:
    record_id: str
    title: str
    text: str
    source_type: str
    year: int | None
    outcome: str | None
    organization: str | None
    data_origin: DataOrigin
    application_id: str | None = None
    grant_call_id: str | None = None
    document_meta: ApplicationDocument | None = None
    document: ExtractedDocument | None = None
    provenance: dict = field(default_factory=dict)


class GrantDataProvider(Protocol):
    provider_id: str

    def status(self) -> SourceAccessStatus: ...

    def historical_records(self) -> list[HistoricalRecord]: ...


class MockGrantDataProvider:
    """Synthetic historical applications and funded projects for local demonstration."""

    provider_id = "historical_applications"

    def __init__(self, records: list[HistoricalRecord] | None = None) -> None:
        from services.grant_workflow.demo_data import HISTORICAL_RECORDS

        self._records = list(HISTORICAL_RECORDS if records is None else records)

    def status(self) -> SourceAccessStatus:
        return SourceAccessStatus.AVAILABLE

    def historical_records(self) -> list[HistoricalRecord]:
        return list(self._records)


class RIGMSGrantDataProvider:
    """Placeholder for an authorized RIGMS integration.

    No RIGMS API contract or credentials are available to this project, so no endpoint is
    invented here. Until an authorized specification exists, every call reports the source
    as unavailable instead of returning empty (and misleading) results.
    """

    provider_id = "rigms"

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url if base_url is not None else os.getenv("AI_SCREENING_RIGMS_URL") or None

    def status(self) -> SourceAccessStatus:
        return SourceAccessStatus.AUTH_REQUIRED if self.base_url else SourceAccessStatus.NOT_CONFIGURED

    def historical_records(self) -> list[HistoricalRecord]:
        raise ProviderUnavailable(
            "RIGMS integration requires authorized access and an agreed API specification; "
            "it is not searched in this environment."
        )


# Sources that the core workflow never requires.
_OPTIONAL_EXTERNAL = [
    ("crossref", "Crossref", "Crossref Works"),
    ("pubmed_central", "NCBI", "PubMed Central"),
    ("arxiv", "arXiv", "arXiv preprints"),
    ("doaj", "DOAJ", "Directory of Open Access Journals"),
    ("core", "CORE", "CORE open research aggregator"),
]


def default_source_registry(
    rigms: RIGMSGrantDataProvider | None = None,
    literature: "PublishedLiteratureSource | None" = None,
) -> SourceRegistry:
    from services.grant_workflow.literature import PublishedLiteratureSource

    rigms = rigms or RIGMSGrantDataProvider()
    literature = literature or PublishedLiteratureSource()
    sources = [
        SourceRecord(
            source_id="same_call_applications",
            provider="shakaHive",
            source_name="Applications in the same grant call",
            source_type="internal",
            coverage="All applications uploaded to the grant call",
            methodology="Local comparison; always available",
            access_status=SourceAccessStatus.AVAILABLE,
        ),
        SourceRecord(
            source_id="historical_applications",
            provider="shakaHive demo",
            source_name="Historical applications and funded projects (synthetic)",
            source_type="internal_synthetic",
            coverage="Synthetic demonstration records only",
            methodology="MockGrantDataProvider",
            access_status=SourceAccessStatus.AVAILABLE,
        ),
        SourceRecord(
            source_id="rigms",
            provider="RIGMS",
            source_name="Research and Innovation Grant Management System",
            source_type="authorized_integration",
            coverage="Applications, applicants, institutions, historical grants (when authorized)",
            methodology="RIGMSGrantDataProvider (requires authorized API specification)",
            access_status=rigms.status(),
        ),
        SourceRecord(
            source_id="institutional_repository",
            provider="Institution",
            source_name="Institutional research repository",
            source_type="authorized_integration",
            coverage="Requires institutional authorization",
            access_status=SourceAccessStatus.NOT_CONFIGURED,
        ),
        SourceRecord(
            source_id=literature.provider_id,
            provider="OpenAlex",
            source_name=literature.source_name,
            source_type="external_optional",
            base_url="https://api.openalex.org",
            coverage="Published works with abstracts; searched by the plagiarism check only",
            methodology="PublishedLiteratureSource (OpenAlex works API)",
            access_status=literature.status(),
        ),
    ]
    sources.extend(
        SourceRecord(
            source_id=source_id,
            provider=provider,
            source_name=name,
            source_type="external_optional",
            coverage="Optional scholarly connector; not required for screening",
            access_status=SourceAccessStatus.NOT_CONFIGURED,
        )
        for source_id, provider, name in _OPTIONAL_EXTERNAL
    )
    return SourceRegistry(sources)
