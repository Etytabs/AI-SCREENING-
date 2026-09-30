from dataclasses import dataclass


@dataclass(frozen=True)
class Stakeholder:
    stakeholder_id: str
    name: str
    role: str
    purpose: str
    access_scope: str
    lifecycle_stage: str


STAKEHOLDERS: tuple[Stakeholder, ...] = (
    Stakeholder(
        "ncst_grant_personnel",
        "NCST grant personnel",
        "Primary institutional user",
        "Manage calls, ingest requirements, screen applications, inspect evidence and coordinate human review.",
        "Grant calls, applications, screening evidence and review workflow",
        "Application → screening → review → award → M&E",
    ),
    Stakeholder(
        "grant_institutions",
        "Grant institutions",
        "Submission stakeholder",
        "Prepare institutional proposals and supporting documents against call-specific requirements.",
        "Call requirements, submission status and authorized proposal records",
        "Application",
    ),
    Stakeholder(
        "researchers_applicants",
        "Researchers / applicants",
        "Pre-submission research user",
        "pre-submission check: assess whether a proposed research topic may overlap with existing or previously submitted research before submission.",
        "Authorized research-topic and similarity evidence; no access to confidential applicant records",
        "Pre-submission → application",
    ),
)


def list_stakeholders() -> list[Stakeholder]:
    return list(STAKEHOLDERS)
