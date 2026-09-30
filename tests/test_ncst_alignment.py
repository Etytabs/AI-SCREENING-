from services.ncst_requirements.registry import (
    list_lifecycle,
    list_monitoring_indicators,
    list_requirements,
    list_sources,
)


def test_ncst_source_registry_has_authoritative_layers():
    sources = {item.source_id for item in list_sources()}
    assert {"nrif_funding_procedures", "active_call_package", "rigms", "research_innovation_repository"}.issubset(sources)


def test_requirements_keep_call_specific_rules_distinct():
    requirements = {item.requirement_id: item for item in list_requirements()}
    assert requirements["ELG-01"].call_specific is True
    assert requirements["BUD-01"].call_specific is True
    assert requirements["PLG-01"].status == "configured"


def test_lifecycle_covers_post_award_monitoring_and_impact():
    stages = {item.stage_id for item in list_lifecycle()}
    assert {"application", "screening", "review", "implementation", "mel", "closeout", "impact"}.issubset(stages)


def test_monitoring_indicators_cover_technical_financial_and_impact_evidence():
    categories = {item.category for item in list_monitoring_indicators()}
    assert {"technical", "financial", "impact"}.issubset(categories)
