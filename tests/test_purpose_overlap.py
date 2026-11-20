from ml.purpose_overlap.service import DIMENSIONS, compare_purposes, profile


LEFT = """
Research problem: hillside farms face recurrent drought.
Objectives: reduce irrigation water use and maintain bean yields.
Beneficiaries: smallholder farmers and bean growers.
Intervention: solar-powered drip irrigation with soil moisture sensors.
Methodology: compare sensor-guided plots with farmer-managed plots.
Outputs: irrigation schedules and field guidance.
Outcomes: lower water use and stable yields.
Geography and scope: hillside districts in Rwanda.
"""


RIGHT_DIFFERENT = """
Research problem: rural clinics need better maternal referral decisions.
Objectives: reduce delays and improve referral completion.
Beneficiaries: pregnant women and district clinics.
Intervention: a mobile clinical risk and referral dashboard.
Methodology: randomized facility rollout and referral tracking.
Outputs: referral dashboard and clinic protocol.
Outcomes: faster escalation and fewer missed referrals.
Geography and scope: urban and peri-urban clinics.
"""


RIGHT_REWRITTEN = """
Problem statement: recurrent drought affects hillside farming communities.
Aim: maintain bean production while reducing irrigation demand.
Target population: smallholders cultivating beans on sloped land.
Proposed solution: deploy solar drip systems guided by soil moisture probes.
Method: measure water use and bean yields against locally managed plots.
Deliverables: schedule recommendations and operational guidance.
Expected impact: reduced water use and resilient bean yields.
Study area: sloped agricultural communities in Rwanda.
"""


def test_same_purpose_with_different_wording_is_distinguished():
    result = compare_purposes(LEFT, RIGHT_REWRITTEN)
    assert result.disposition != "LEGITIMATE_REPLICATION"
    dimensions = {item.dimension for item in result.dimensions}
    assert {"beneficiaries", "geography_scope"}.issubset(dimensions)
    assert result.method == "deterministic_section_jaccard_v1"
    assert all(item.status in {"SIMILAR", "DIFFERENT", "DISTINCT", "NOT_PROVIDED"} for item in result.dimensions)
    assert "not a trained purpose classifier" in " ".join(result.limitations)


def test_different_objective_and_intervention_is_not_purpose_duplicate():
    result = compare_purposes(LEFT, RIGHT_DIFFERENT)
    assert result.disposition in {
        "SIMILAR_TOPIC_DIFFERENT_PURPOSE",
        "DIFFERENTIATED_FOLLOW_ON",
        "DISTINCT_PROJECT",
    }
    assert "POTENTIAL_OVERLAP" not in result.disposition


def test_missing_structured_dimensions_are_not_inferred():
    result = compare_purposes("A short project.", "Another short project.")
    assert result.disposition == "INSUFFICIENT_EVIDENCE"
    assert result.confidence == "LOW"


def test_classifier_never_claims_legitimate_replication_from_similarity():
    comparisons = (
        (LEFT, RIGHT_REWRITTEN),
        (LEFT, RIGHT_DIFFERENT),
        ("A short project.", "Another short project."),
    )
    for left_text, right_text in comparisons:
        result = compare_purposes(left_text, right_text)
        assert result.disposition != "LEGITIMATE_REPLICATION"


def test_profile_extracts_only_its_own_newline_separated_section():
    text = "Research problem: drought affects farms.\nObjectives: reduce water use.\nBeneficiaries: smallholder farmers."
    extracted = profile(text)
    assert extracted["research_problem"] == "drought affects farms"
    assert extracted["objectives"] == "reduce water use"
    assert extracted["beneficiaries"] == "smallholder farmers"
    assert extracted["intervention"] == ""


def test_profile_extracts_numbered_and_reordered_sections():
    text = (
        "3. Methodology: compare two irrigation systems.\n"
        "1. Objectives: reduce water use.\n"
        "2. Research problem: recurring drought."
    )
    extracted = profile(text)
    assert extracted["methodology"] == "compare two irrigation systems"
    assert extracted["objectives"] == "reduce water use"
    assert extracted["research_problem"] == "recurring drought"


def test_profile_extracts_inline_punctuation_separated_headings():
    text = (
        "Research problem: drought reduces yields; Objectives: improve resilience. "
        "Intervention: solar irrigation, Methodology: field trials."
    )
    extracted = profile(text)
    assert extracted["research_problem"] == "drought reduces yields"
    assert extracted["objectives"] == "improve resilience"
    assert extracted["intervention"] == "solar irrigation"
    assert extracted["methodology"] == "field trials"


def test_missing_sections_remain_empty_and_do_not_absorb_other_content():
    extracted = profile("Research problem: drought affects farms.\nOutputs: irrigation guidance.")
    assert extracted["research_problem"] == "drought affects farms"
    assert extracted["outputs"] == "irrigation guidance"
    assert extracted["objectives"] == ""
    assert set(extracted) == set(DIMENSIONS)
