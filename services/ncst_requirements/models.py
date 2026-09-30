from dataclasses import dataclass

from typing import Literal

RequirementStatus = Literal["official_source", "configured", "demo_only", "needs_authorization"]
RequirementDomain = Literal[
    "application",
    "completeness",
    "eligibility",
    "plagiarism",
    "review",
    "budget",
    "team",
    "ethics_permits",
    "monitoring_evaluation",
    "closeout",
    "commercialization",
]


@dataclass(frozen=True)
class RequirementSource:
    source_id: str
    name: str
    source_type: str
    status: RequirementStatus
    authority: str
    notes: str = ""


@dataclass(frozen=True)
class Requirement:
    requirement_id: str
    domain: RequirementDomain
    name: str
    description: str
    status: RequirementStatus
    source_id: str
    source_locator: str
    call_specific: bool = True


@dataclass(frozen=True)
class LifecycleStage:
    stage_id: str
    name: str
    purpose: str
    ai_support: tuple[str, ...]
    human_owner: str


@dataclass(frozen=True)
class MonitoringIndicator:
    indicator_id: str
    name: str
    category: str
    evidence_required: tuple[str, ...]
    cadence: str
