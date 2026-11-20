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


def test_plagiarism_dispositions_use_only_the_matched_passage_context():
    from services.plagiarism.service import classify_disposition

    matched_uncited = "The intervention reduced crop losses through targeted irrigation."
    source_match = "The intervention reduced crop losses through targeted irrigation."
    full_proposal = "As cited from the original study. " + matched_uncited
    assert "cited from" in full_proposal
    assert classify_disposition(
        matched_uncited, source_match, 0.92
    ) == "POTENTIAL_VERBATIM_OR_NEAR_VERBATIM"


def test_boilerplate_elsewhere_does_not_relabel_a_substantive_match():
    from services.plagiarism.service import classify_disposition

    substantive_match = "The intervention reduced crop losses through targeted irrigation."
    full_proposal = (
        "The institutional research ethics committee will review the protocol. "
        + substantive_match
    )
    assert "institutional research ethics committee" in full_proposal
    assert classify_disposition(
        substantive_match, substantive_match, 0.92
    ) == "POTENTIAL_VERBATIM_OR_NEAR_VERBATIM"


def test_local_citation_and_boilerplate_context_remain_distinct():
    from services.plagiarism.service import classify_disposition

    assert classify_disposition(
        "Quoted from the original report: participants will receive information.",
        "participants will receive information",
        0.92,
    ) == "GENERIC_OR_BOILERPLATE"
    assert classify_disposition(
        "According to the cited source, this passage is reproduced.",
        "this passage is reproduced",
        0.92,
    ) == "PROPERLY_ATTRIBUTED_CONTEXT"
    assert classify_disposition(
        "A paraphrased project passage.",
        "A differently worded project passage.",
        0.50,
    ) == "POTENTIAL_PARAPHRASED_OVERLAP"
