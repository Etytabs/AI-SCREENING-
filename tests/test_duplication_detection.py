"""Duplication-specific regression cases; no external model downloads."""
import pytest

from ml.evidence.state import RunState
from ml.semantic_matching.duplication import (
    EXACT,
    NONE,
    POSSIBLE,
    SUBSTANTIAL,
    compare_proposals,
    profile_proposal,
)
from services.evidence.coverage import SourceCoverage
from services.grant_workflow.documents import ApplicationMetadata
from services.grant_workflow.models import Application, ApplicationDocument, DataOrigin, GrantCall
from services.grant_workflow.screening.context import ComparisonRecord, ScreeningContext
from services.grant_workflow.screening.similarity import evaluate_duplication
from services.ingestion.document import ExtractedDocument, ExtractedPage

NARRATIVE = (
    "We will install twelve solar powered ultrasonic sensors along the Sebeya river to measure water levels "
    "and transmit hourly readings through a LoRaWAN gateway. Community volunteers will validate alert "
    "thresholds against satellite flood maps in six villages. A stepped wedge trial will measure evacuation "
    "uptake and warning lead times during the rainy season. Hydrological forecasts will integrate rainfall "
    "observations, soil moisture estimates and topographic elevation profiles."
)
UNRELATED = (
    "Laboratory technicians will investigate ceramic fracture propagation under compression and tensile loading. "
    "Kiln temperatures will vary across recycled clay specimens to quantify thermal resistance and porosity. "
    "Electron microscopy will reveal the crystal structure of slag additives. Construction panels will undergo "
    "accelerated weathering experiments before insulation performance assessment."
)


def compare(left, right):
    return compare_proposals(profile_proposal(left), profile_proposal(right))


def context(text=NARRATIVE, records=None, **kwargs):
    page = ExtractedPage(1, " ".join(text.splitlines()), tuple(text.splitlines()))
    doc = ExtractedDocument("proposal", "proposal.txt", "text/plain", page.text, 1, "success", pages=(page,))
    meta = ApplicationDocument(
        id="proposal", application_id="current", filename="proposal.txt", document_type="proposal",
        file_hash=None, uploaded_by="test", extraction_status="success",
    )
    return ScreeningContext(
        grant_call=GrantCall(id="call", name="Test", organization="Test", created_by="test"),
        application=Application(id="current", grant_call_id="call", application_reference="CURRENT"),
        applicant=None, institution=None, documents=[(meta, doc)], criteria=[], rfp_text="",
        universe=records if records is not None else [record("source", NARRATIVE)],
        coverage=[SourceCoverage("history", RunState.COMPLETE, "Authorized history")],
        metadata=ApplicationMetadata(), **kwargs,
    )


def record(record_id, text):
    return ComparisonRecord(record_id, "funded_project", record_id, text, DataOrigin.UPLOADED, year=2024, outcome="Funded")


def evaluate(ctx):
    return evaluate_duplication(ctx, "run")[0]


def test_exact_normalization_handles_unicode_case_whitespace_and_punctuation():
    transformed = NARRATIVE.upper().replace(" ", "\n").replace(".", "!")
    result = compare(NARRATIVE, transformed)
    assert result.match_type == EXACT
    assert result.score == result.query_coverage == result.source_coverage == 1
    assert compare(NARRATIVE.replace("twelve", "ＴＷＥＬＶＥ"), NARRATIVE).match_type == EXACT


def test_small_changes_and_reordered_sections_remain_substantially_similar():
    sentences = NARRATIVE.split(". ")
    revised = ". ".join(reversed(sentences)).replace("twelve", "twenty").replace("six villages", "eight villages")
    assert compare(NARRATIVE, revised).match_type == SUBSTANTIAL


def test_reused_material_beyond_former_sentence_limit_is_found_and_cited():
    introduction = "\n".join(f"Ceramic specimen {i} received tensile loading and electron microscopy inspection." for i in range(320))
    result = evaluate(context(introduction + "\n" + NARRATIVE))
    assert result.signal == "POSSIBLE_DUPLICATION"
    assert result.details["match_type"] == SUBSTANTIAL
    assert "Ceramic" not in result.matches[0].query_passage
    assert result.matches[0].query_passage in NARRATIVE
    assert result.matches[0].query_page == 1
    assert any(item.citation_valid is True for item in result.evidence)


def test_one_substantive_reused_passage_is_possible_not_whole_proposal_exact():
    shared = NARRATIVE.split(". ")[0] + "."
    result = compare(UNRELATED + " " + shared, NARRATIVE)
    assert result.match_type == POSSIBLE
    assert result.query_passage in shared


def test_same_broad_topic_different_projects_are_not_duplicates():
    different = (
        "River flood preparedness depends on local institutions and household trust. Interviews in urban "
        "settlements will compare community attitudes to emergency evacuation during historical flooding. "
        "Survey responses will reveal how insurance prices influence household relocation decisions. "
        "District volunteers will map economic vulnerability through participatory workshops."
    )
    assert compare(NARRATIVE, different).match_type == NONE


def test_common_form_fields_and_prompts_do_not_produce_duplication():
    form = (
        "Applicant: Shared Person\nInstitution: Shared National University\nCountry: Rwanda\n"
        "Please describe the research objectives, expected outcomes and proposed methodology.\n"
        "Provide a detailed timeline, budget justification and plan for dissemination of results.\n"
        "I declare that the submitted proposal is original and no conflict of interest exists.\n"
    )
    assert compare(form + NARRATIVE, form + UNRELATED).match_type == NONE
    finding = evaluate(context(form, [record("form", form)]))
    assert finding.signal == "NOT_ASSESSABLE"
    assert finding.details["compared_records"] == 0


@pytest.mark.parametrize("text", ["", "---  ...", "Short heading", "Project proposal research objectives methodology"])
def test_empty_or_insufficient_proposal_is_not_assessed(text):
    assert evaluate(context(text)).signal == "NOT_ASSESSABLE"


def test_empty_or_unusable_library_is_not_a_clean_result():
    assert evaluate(context(records=[])).signal == "NOT_ASSESSABLE"
    finding = evaluate(context(records=[record("empty", ""), record("form", "Applicant: Person")]))
    assert finding.signal == "NOT_ASSESSABLE"
    assert finding.details["compared_records"] == 0
    assert finding.details["skipped_records"] == 2


def test_all_records_are_counted_before_display_limit_and_self_is_excluded():
    records = [record(f"duplicate-{index}", NARRATIVE) for index in range(8)]
    records.append(ComparisonRecord("self", "same_call_application", "Self", NARRATIVE, DataOrigin.UPLOADED, application_id="current"))
    finding = evaluate(context(records=records))
    assert finding.details["compared_records"] == finding.details["flagged"] == 8
    assert finding.details["displayed_matches"] == len(finding.matches) == 5
    assert all(item.record_id != "self" for item in finding.matches)


def test_unavailable_source_and_blank_record_are_reported_without_erasing_valid_search():
    ctx = context(records=[record("unrelated", UNRELATED), record("blank", "")])
    ctx.coverage.append(SourceCoverage("rigms", RunState.FAILED, "Unavailable"))
    finding = evaluate(ctx)
    assert finding.signal == NONE
    assert finding.details["compared_records"] == 1
    assert finding.details["coverage_complete"] is False
    assert finding.details["skipped_records"] == 1
    assert "rigms" in finding.explanation
    assert "not evidence of originality" in finding.explanation


def test_readable_cv_cannot_replace_an_unreadable_proposal():
    ctx = context()
    meta, doc = ctx.documents[0]
    cv = meta.model_copy(update={"id": "cv", "filename": "cv.txt", "document_type": "cv"})
    ctx.documents = [(meta, None), (cv, doc)]
    assert evaluate(ctx).signal == "NOT_ASSESSABLE"


def test_partial_readable_proposal_cannot_receive_a_clean_result():
    ctx = context(records=[record("unrelated", UNRELATED)])
    meta, _ = ctx.documents[0]
    ctx.documents.append((meta.model_copy(update={"id": "missing", "filename": "part-two.pdf"}), None))
    finding = evaluate(ctx)
    assert finding.signal == "NOT_ASSESSABLE"
    assert finding.details["match_type"] == "NOT_ASSESSABLE"
    assert finding.status.value == "REVIEW_REQUIRED"
    assert finding.details["compared_records"] == 1
    assert finding.details["coverage_complete"] is False


def test_partial_readable_proposal_can_still_report_a_found_duplicate():
    ctx = context()
    meta, _ = ctx.documents[0]
    ctx.documents.append((meta.model_copy(update={"id": "missing", "filename": "part-two.pdf"}), None))
    finding = evaluate(ctx)
    assert finding.signal == "POSSIBLE_DUPLICATION"
    assert finding.details["coverage_complete"] is False


def test_source_and_query_passages_are_verbatim_with_origin_and_funding_metadata():
    result = evaluate(context())
    match = result.matches[0]
    assert match.query_passage in NARRATIVE and match.matched_passage in NARRATIVE
    assert match.query_document_id == "proposal" and match.query_page == 1
    assert match.year == 2024 and match.outcome == "Funded"
    assert match.data_origin == DataOrigin.UPLOADED
    assert {item.source_type for item in result.evidence} == {"application_document", "funded_project"}


class BrokenEmbedder:
    model_name = "offline"

    def encode(self, texts):
        raise RuntimeError("Model unavailable")


class ConstantEmbedder:
    model_name = "constant-test-model"

    def encode(self, texts):
        return [[1.0, 0.0] for _ in texts]


class NegativeReranker:
    model_name = "negative-test-reranker"

    def score(self, query, candidates):
        return [-12.0 for _ in candidates]


def test_optional_model_failure_preserves_exact_detection_and_reports_fallback():
    finding = evaluate(context(embedder=BrokenEmbedder()))
    assert finding.details["match_type"] == EXACT
    assert finding.matches[0].semantic_score is None
    assert any("Semantic model unavailable" in item for item in finding.details["limitations"])


def test_high_semantic_score_alone_does_not_flag_unrelated_projects():
    finding = evaluate(context(records=[record("unrelated", UNRELATED)], embedder=ConstantEmbedder()))
    assert finding.signal == NONE
    assert finding.matches[0].semantic_score == 1


def test_negative_reranker_logit_cannot_suppress_identical_proposals():
    finding = evaluate(context(reranker=NegativeReranker()))
    assert finding.details["match_type"] == EXACT
    assert finding.matches[0].reranker_score == -12
    assert finding.matches[0].similarity_score == 1


def test_malformed_semantic_output_falls_back_instead_of_hiding_result():
    class MalformedEmbedder:
        model_name = "malformed"

        def encode(self, texts):
            return [[float("nan")]] * len(texts)

    finding = evaluate(context(embedder=MalformedEmbedder()))
    assert finding.details["match_type"] == EXACT
    assert finding.matches[0].semantic_score is None
    assert any("Semantic model unavailable" in item for item in finding.details["limitations"])
