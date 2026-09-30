from services.research_sources.models import ResearchRecord
from services.research_sources.registry import get_source, list_sources


def test_source_registry_contains_core_research_sources():
    sources = {source.source_id for source in list_sources()}
    assert {"core", "crossref", "doaj", "pmc", "arxiv", "ajol", "google_scholar"}.issubset(sources)


def test_research_record_searchable_text():
    record = ResearchRecord(record_id="1", title="Crop disease detection", abstract="Machine learning", keywords=("maize",))
    assert "Crop disease detection" in record.searchable_text()
    assert "Machine learning" in record.searchable_text()
    assert "maize" in record.searchable_text()


def test_discovery_source_is_explicit():
    source = get_source("google_scholar")
    assert source.source_type == "discovery"
    assert "not scraped" in source.notes.lower()
