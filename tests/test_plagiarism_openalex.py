"""Plagiarism check against published literature (OpenAlex), without live network calls."""
import pytest

from ml.evidence.state import RunState
from services.grant_workflow.literature import (
    PublishedLiteratureSource,
    build_queries,
    document_title,
    openalex_enabled,
)
from services.grant_workflow.models import FindingStatus
from services.research_sources.connectors import reconstruct_abstract, search_openalex
from services.research_sources.models import ResearchRecord
from services.research_sources.registry import get_source
from services.sources.registry import SourceAccessStatus

PROPOSAL = (
    "Unraveling the Physics of Light at Scale\n"
    "Keywords: computer graphics; differentiable rendering; inverse rendering; atmospheric optics\n"
    "Photons can act as probes of the physical world because light is reflected, refracted, "
    "scattered, and absorbed by the materials it encounters. Recovering useful physical "
    "information from images is an inverse problem: indirect measurements must be processed to "
    "estimate the properties that produced them. The central objective is to develop scalable "
    "methods for inverting the physics of light when simulations contain extremely large numbers "
    "of parameters, demonstrated across atmospheric optics, microscopy, and architecture."
)

# A published paper that demo application DEMO-APP-003 reproduces almost sentence for
# sentence: the case the plagiarism check exists to surface.
WORK = ResearchRecord(
    record_id="W2000000001",
    title="Solar irrigation scheduling for drought-prone hillside farms",
    abstract=(
        "We design solar-powered drip irrigation schedules for hillside farms facing recurrent "
        "drought and contribute to water resource management. We test whether soil moisture "
        "sensors combined with weather forecasts reduce irrigation water use while maintaining "
        "bean yields, comparing sensor-guided scheduling with farmer-managed irrigation on forty "
        "demonstration plots supported by farmer interviews and yield measurements."
    ),
    authors=("A Researcher", "B Co-author"),
    publication_date="2019-04-15",
    journal="Agricultural Water Management",
    doi="10.1016/j.agwat.2019.04.001",
    source_id="openalex",
    source_url="https://doi.org/10.1016/j.agwat.2019.04.001",
)


@pytest.fixture(autouse=True)
def openalex_on(monkeypatch):
    monkeypatch.setenv("AI_SCREENING_OPENALEX_ENABLED", "true")


def test_openalex_is_a_registered_research_source():
    source = get_source("openalex")
    assert source.source_type == "api" and source.metadata


def test_reconstruct_abstract_restores_word_order():
    assert reconstruct_abstract({"inverse": [1], "an": [0], "problem": [2]}) == "an inverse problem"
    assert reconstruct_abstract(None) == ""


def test_search_openalex_maps_fields_and_sends_credentials(monkeypatch):
    seen = {}

    def fake_get(url, headers=None):
        seen["url"], seen["headers"] = url, headers
        return b"""{"results": [{
            "id": "https://openalex.org/W123", "doi": "https://doi.org/10.1/abc",
            "display_name": "Inverse rendering at scale", "publication_date": "2022-03-04",
            "publication_year": 2022,
            "abstract_inverted_index": {"scalable": [0], "inverse": [1], "rendering": [2]},
            "authorships": [{"author": {"display_name": "A Researcher"},
                             "institutions": [{"display_name": "EPFL"}]}],
            "primary_location": {"source": {"display_name": "ACM TOG"},
                                 "landing_page_url": "https://acm.org/1"},
            "best_oa_location": {"pdf_url": "https://acm.org/1.pdf"}, "type": "article"}]}"""

    monkeypatch.setattr("services.research_sources.connectors._get", fake_get)
    monkeypatch.setenv("AI_SCREENING_OPENALEX_API_KEY", "test-key")
    monkeypatch.setenv("AI_SCREENING_OPENALEX_MAILTO", "reviewer@example.org")

    [record] = search_openalex("inverse rendering", rows=5)
    assert "api_key=test-key" in seen["url"] and "mailto=reviewer%40example.org" in seen["url"]
    assert "reviewer@example.org" in seen["headers"]["User-Agent"]
    assert record.record_id == "W123"
    assert record.title == "Inverse rendering at scale"
    assert record.abstract == "scalable inverse rendering"
    assert record.authors == ("A Researcher",) and record.affiliations == ("EPFL",)
    assert record.publication_date == "2022-03-04" and record.journal == "ACM TOG"
    assert record.doi == "10.1/abc" and record.source_url == "https://doi.org/10.1/abc"
    assert record.full_text_url == "https://acm.org/1.pdf"


PDF_LIKE = """Exploring Factors Associated with Research Involvement of
Undergraduate Students at the College of Medicine and
Health Sciences, University of Rwanda
Ndinayo Eric
PLAGIARISM-DETECTION TEST DOCUMENT - NOT FOR ACADEMIC SUBMISSION
Abstract
Early involvement of students in research processes is an important step in professional
development and can increase the academic output of the university.
"""


def test_document_title_is_read_from_the_document_when_no_title_was_parsed():
    """An uploaded PDF usually has no application title; its own title block is the
    strongest query for finding the work it was copied from."""
    assert document_title(PDF_LIKE) == (
        "Exploring Factors Associated with Research Involvement of Undergraduate Students "
        "at the College of Medicine and Health Sciences, University of Rwanda"
    )
    queries = build_queries(None, PDF_LIKE)
    assert queries[0].startswith("Exploring Factors Associated with Research Involvement")


def test_document_title_stops_before_authors_headings_and_notices():
    assert document_title("Abstract\nSomething about a study of things") is None
    # a heading immediately after the title closes it
    assert document_title("A Study of Maize Disease Detection\n1. Introduction\nText") == (
        "A Study of Maize Disease Detection"
    )
    # an author line ends the wrapped title rather than joining it
    assert document_title("Inverting the Physics of Light at Scale\nEric Ndinayo\nAbstract") == (
        "Inverting the Physics of Light at Scale"
    )


def test_build_queries_uses_title_keywords_and_terms():
    queries = build_queries("Unraveling the Physics of Light at Scale (UNRAVEL)", PROPOSAL)
    assert queries[0] == "Unraveling the Physics of Light at Scale"
    assert "differentiable rendering" in queries[1]
    assert len(queries) <= 3 and len(set(queries)) == len(queries)


def test_literature_source_reports_blocked_when_not_configured(monkeypatch):
    monkeypatch.setenv("AI_SCREENING_OPENALEX_ENABLED", "false")
    assert openalex_enabled() is False
    source = PublishedLiteratureSource()
    assert source.status() == SourceAccessStatus.NOT_CONFIGURED
    result = source.search(["inverse rendering"])
    assert result.state == RunState.BLOCKED and not result.records
    assert "not configured" in result.message


def test_literature_source_drops_abstract_less_works_and_deduplicates():
    calls = []

    def fake_search(query, rows):
        calls.append(query)
        return [WORK, WORK.__class__(record_id="W2", title="No abstract", abstract="too short")]

    source = PublishedLiteratureSource(search=fake_search)
    assert source.status() == SourceAccessStatus.AVAILABLE
    result = source.search(["one", "two"])
    assert calls == ["one", "two"]
    assert [r.record_id for r in result.records] == ["W2000000001"]
    assert result.state == RunState.COMPLETE


def test_literature_source_reports_partial_when_a_query_fails():
    def flaky(query, rows):
        if query == "bad":
            raise TimeoutError("upstream timeout")
        return [WORK]

    result = PublishedLiteratureSource(search=flaky).search(["good", "bad"])
    assert result.state == RunState.PARTIAL and len(result.records) == 1
    assert "1 query(ies) failed" in result.message


def test_literature_source_failure_is_not_a_clean_result():
    def broken(query, rows):
        raise ConnectionError("no route to host")

    result = PublishedLiteratureSource(search=broken).search(["anything"])
    assert result.state == RunState.FAILED and not result.records
    assert "could not be searched" in result.message


def _run_plagiarism(service, application_id):
    from services.grant_workflow.models import Finding, FindingType

    return next(
        f for f in service.repo.list(Finding, application_id=application_id)
        if f.type == FindingType.PLAGIARISM
    )


def test_published_work_is_reported_with_percentage_and_publication_details():
    from services.grant_workflow.jobs import InlineJobRunner
    from services.grant_workflow.models import Application
    from services.grant_workflow.seed import seed_demo
    from services.grant_workflow.service import GrantWorkflowService

    service = GrantWorkflowService(
        jobs=InlineJobRunner(),
        literature=PublishedLiteratureSource(search=lambda query, rows: [WORK]),
    )
    call = seed_demo(service)
    apps = {a.application_reference: a for a in service.repo.list(Application, grant_call_id=call.id)}
    finding = _run_plagiarism(service, apps["DEMO-APP-003"].id)

    assert finding.details["published_literature_searched"] is True
    assert finding.details["published_works_compared"] == 1
    published = [m for m in finding.matches if m.source_type == "published_work"]
    assert published, finding.explanation
    match = published[0]
    assert match.published_on == "2019-04-15"
    assert match.authors == ["A Researcher", "B Co-author"]
    assert match.publisher == "Agricultural Water Management"
    assert match.doi == "10.1016/j.agwat.2019.04.001"
    assert match.source_url.startswith("https://doi.org/")
    assert 0 < match.similarity_score <= 1
    assert finding.status == FindingStatus.REVIEW_REQUIRED
    assert finding.signal == "SHARED_PASSAGES_FOUND"
    assert finding.details["similarity_index"] >= 20.0
    assert finding.details["band"] in {"MODERATE_SIMILARITY", "HIGH_SIMILARITY"}
