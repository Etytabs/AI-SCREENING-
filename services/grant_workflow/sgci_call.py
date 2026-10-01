"""The SGCI STISA 2034 multilateral research call.

Unlike services.grant_workflow.seed, this is a real call, so nothing here is marked
SYNTHETIC and nothing is auto-verified: the extracted requirements stay in the
administrator's verification queue, which is where category and required/optional
mistakes get corrected before any application is screened against them.

The call document below carries only the text supplied for this call. Where the source
is silent — submission deadline, project duration, required annexes beyond the support
letters — no value is stated rather than invented.
"""
from services.grant_workflow.models import GrantCall, Role
from services.grant_workflow.service import Actor, GrantWorkflowService

SGCI_SEED_ACTOR = Actor("sgci-call-administrator", Role.GRANT_ADMINISTRATOR)

SGCI_CALL = {
    "name": "Advancing Africa's STI Priorities: SGCI Multilateral Research Call in support of STISA 2034",
    "organization": "Science Granting Councils Initiative (SGCI)",
    "reference": "SGCI-STISA-2034",
    "description": (
        "Multilateral research call supporting consortia of institutions in three to five eligible "
        "African countries. Institutions in Rwanda are eligible for up to RWF 100,000,000. "
        "Matchmaking platform: https://call.sgci.africa"
    ),
    "funding_max": 100_000_000,
    "currency": "RWF",
    "domains": [
        "Health",
        "Agriculture",
        "Artificial Intelligence and Digital Technologies",
        "Energy",
        "Environment",
    ],
}

SGCI_RFP_FILENAME = "SGCI-STISA-2034_call_document.txt"

SGCI_RFP_TEXT = """SCIENCE GRANTING COUNCILS INITIATIVE
CALL FOR PROPOSALS
Advancing Africa's STI Priorities: SGCI Multilateral Research Call in support of STISA 2034
Reference: SGCI-STISA-2034
Matchmaking platform: https://call.sgci.africa
1. Purpose
The call supports multilateral research that advances Africa's science, technology and innovation priorities in support of STISA 2034.
2. Consortium
Applicants must build a research consortium with institutions in three to five eligible African countries.
3. Thematic priorities
Proposals must address at least one of the following priorities: Health, Agriculture, Artificial Intelligence and Digital Technologies, Energy, or Environment.
4. Funding
Institutions in Rwanda are eligible to receive up to RWF 100,000,000 in grants.
Funding will be disbursed through the host institution in Rwanda.
\f5. Annex 1 - Country eligibility requirements and funding ceilings
Rwanda: Health; Agriculture; Energy; Environment; AI. Funding ceiling 100,000,000 RWF.
The Principal Investigator must be a Rwandan national, affiliated with a recognized Rwandan university or research institution.
Projects must include collaboration with private-sector or industry partners in Rwanda.
Institutional support letters are mandatory.
Having at least 30% women represented on the research team is considered an asset in the competition.
Projects should demonstrate potential for job creation and socio-economic impact.
6. Consortium building
Visit the SGCI STISA Matchmaking platform at https://call.sgci.africa for tools that will help you build your research consortium.
"""


def sgci_rfp_bytes() -> bytes:
    return SGCI_RFP_TEXT.encode("utf-8")


def seed_sgci_call(service: GrantWorkflowService) -> GrantCall:
    """Create the call and extract its requirements, leaving them for an administrator.

    The call stays in REQUIREMENTS_PENDING until a human verifies and confirms the
    extracted criteria, so no application is ever screened against unreviewed rules.
    """
    existing = next(
        (call for call in service.list_calls() if call.reference == SGCI_CALL["reference"]), None
    )
    if existing is not None:
        return existing
    call = service.create_call(SGCI_SEED_ACTOR, dict(SGCI_CALL))
    service.upload_rfp(SGCI_SEED_ACTOR, call.id, SGCI_RFP_FILENAME, sgci_rfp_bytes())
    return service.get_call(call.id)
