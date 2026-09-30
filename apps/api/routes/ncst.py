from dataclasses import asdict

from fastapi import APIRouter

from services.ncst_requirements.registry import (
    list_lifecycle,
    list_monitoring_indicators,
    list_requirements,
    list_sources,
)
from services.stakeholders import list_stakeholders

router = APIRouter(prefix="/api/v1/ncst", tags=["ncst-alignment"])


@router.get("/requirements")
def ncst_requirements() -> dict:
    return {
        "stakeholder": "NCST / NRIF",
        "status": "source-aligned, not an official NCST ruleset",
        "sources": [asdict(item) for item in list_sources()],
        "requirements": [asdict(item) for item in list_requirements()],
        "human_review_required": True,
        "activation_rule": "Call-specific rules require authorized source documents and human approval before becoming operational.",
    }


@router.get("/stakeholders")
def ncst_stakeholders() -> dict:
    return {
        "stakeholders": [asdict(item) for item in list_stakeholders()],
        "primary_user_order": [
            "ncst_grant_personnel",
            "grant_institutions",
            "researchers_applicants",
        ],
        "human_review_required": True,
    }


@router.get("/lifecycle")
def ncst_lifecycle() -> dict:
    return {
        "stakeholder": "NCST / NRIF",
        "stages": [asdict(item) for item in list_lifecycle()],
        "human_review_required": True,
    }


@router.get("/monitoring-indicators")
def ncst_monitoring_indicators() -> dict:
    return {
        "stakeholder": "NCST / NRIF",
        "cadence_note": "The Annual Report describes quarterly Monitoring, Evaluation and Learning field visits for NCST-funded research and innovation projects.",
        "indicators": [asdict(item) for item in list_monitoring_indicators()],
        "human_review_required": True,
    }
