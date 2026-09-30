from services.stakeholders import list_stakeholders


def test_primary_stakeholder_order_and_purposes() -> None:
    stakeholders = list_stakeholders()
    assert [item.stakeholder_id for item in stakeholders] == [
        "ncst_grant_personnel",
        "grant_institutions",
        "researchers_applicants",
    ]
    assert "pre-submission" in stakeholders[2].purpose
    assert "potentially" in stakeholders[2].purpose
