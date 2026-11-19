from ml.purpose_overlap.service import compare_purposes


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
    assert result.disposition in {"POTENTIAL_OVERLAP", "LEGITIMATE_REPLICATION"}
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
