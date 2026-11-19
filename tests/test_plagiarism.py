from services.plagiarism.models import SourceAttribution, SourceCandidate


def test_source_attribution_preserves_provenance():
    attribution = SourceAttribution(
        title="Example research",
        authors=("Jane Doe",),
        publisher="Example University",
        source_url="https://example.org/paper",
        metadata_confidence=0.8,
    )
    source = SourceCandidate(
        source_id="google:1",
        title=attribution.title,
        url=attribution.source_url,
        attribution=attribution,
    )
    assert source.attribution.authors == ("Jane Doe",)
    assert source.attribution.publisher == "Example University"
    assert source.url == "https://example.org/paper"


def test_similarity_is_explicitly_review_required():
    from services.plagiarism.models import PlagiarismEvidence

    evidence = PlagiarismEvidence(
        finding_id="PLG-test",
        status="REVIEW_REQUIRED",
        match_type="near-verbatim",
        similarity=0.92,
        applicant_passage="sample",
        source_passage="sample",
        source=SourceCandidate("google:1", "Example", "https://example.org"),
        explanation="Potential text similarity detected.",
        confidence=0.92,
    )
    assert evidence.human_review_required is True
    assert evidence.status == "REVIEW_REQUIRED"


def test_plagiarism_dispositions_keep_quote_and_boilerplate_separate():
    from services.plagiarism.service import classify_disposition

    assert classify_disposition(
        "As cited from the original study.",
        "The original study method.",
        0.70,
    ) == "PROPERLY_ATTRIBUTED_CONTEXT"
    assert classify_disposition(
        "Ethical approval will be obtained from the institutional research ethics committee.",
        "The same institutional research ethics committee procedure.",
        0.80,
    ) == "GENERIC_OR_BOILERPLATE"
    assert classify_disposition("One passage copied.", "A matching passage.", 0.70) == "POTENTIAL_VERBATIM_OR_NEAR_VERBATIM"
    assert classify_disposition("A paraphrased project.", "A differently worded project.", 0.50) == "POTENTIAL_PARAPHRASED_OVERLAP"
