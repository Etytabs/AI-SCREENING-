"""Deterministic RFP requirement extractor.

Extracted criteria are proposals for an administrator to verify. Requirement text is
always a verbatim span of the RFP with a validated citation; titles are labels only.
An LLM-backed extractor can implement the same `extract_requirements` contract later,
but its output must go through the same verification workflow.
"""
import re
from dataclasses import dataclass, field
from typing import Any

from services.grant_workflow.models import CriterionCategory as Cat
from services.grant_workflow.models import CriterionStatus, RfpCriterion
from services.grant_workflow.text_utils import (
    content_words,
    iter_lines,
    locate_span,
    parse_amounts,
    parse_durations,
    split_sentences,
)
from services.ingestion.document import ExtractedDocument

EXTRACTOR_VERSION = "rfp-rules-v0.1"

_MODAL = re.compile(
    r"\b(must|shall|required|requires|mandatory|eligible|eligibility|only|maximum|minimum|"
    r"not exceed|no later than|will be evaluated|should|at least|up to)\b",
    re.IGNORECASE,
)
_STRONG_MODAL = re.compile(r"\b(must|shall|required|mandatory|not exceed|no later than)\b", re.IGNORECASE)
_SUBMIT_VERB = re.compile(r"\b(submit|attach|attached|include|included|provide|required|accompan|annex)", re.IGNORECASE)
_CONDITIONAL = re.compile(r"\b(involving|where applicable|if applicable|if |when |where )", re.IGNORECASE)
_DATE = re.compile(
    r"\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{4}\b|\b\d{4}-\d{2}-\d{2}\b",
    re.IGNORECASE,
)

DOCUMENT_TYPES: dict[str, tuple[str, ...]] = {
    "proposal": ("research proposal", "full proposal", "project proposal", "concept note"),
    "budget": ("budget",),
    "cv": ("curriculum vitae", "cv", "resume", "biosketch"),
    "partner_letter": ("partner letter", "letter of commitment", "letter of support", "letters of support"),
    "ethics": ("ethics approval", "ethical approval", "ethics clearance", "irb approval"),
    "workplan": ("workplan", "work plan", "gantt"),
    "declaration": ("declaration",),
    "registration_certificate": ("registration certificate", "certificate of registration"),
}
DOCUMENT_LABELS = {
    "proposal": "Research proposal",
    "budget": "Detailed budget",
    "cv": "CV of principal investigator",
    "partner_letter": "Partner letter of commitment",
    "ethics": "Ethics approval / clearance plan",
    "workplan": "Workplan",
    "declaration": "Signed declaration",
    "registration_certificate": "Registration certificate",
}

COUNTRIES = (
    "Rwanda", "Kenya", "Uganda", "Tanzania", "Burundi", "Democratic Republic of the Congo", "Ethiopia",
    "Nigeria", "Ghana", "South Africa", "Senegal", "Malawi", "Zambia", "Zimbabwe", "Mozambique",
    "Cameroon", "Botswana", "Namibia", "South Sudan", "Somalia", "Egypt", "Morocco", "Tunisia",
    "India", "Bangladesh", "Brazil", "United Kingdom", "United States", "Germany", "France",
)
QUALIFICATION_TERMS = {
    "phd": ("phd", "ph.d", "doctorate", "doctoral"),
    "doctoral": ("phd", "ph.d", "doctorate", "doctoral"),
    "master": ("master", "msc", "m.sc"),
    "degree": ("degree",),
}
INSTITUTION_TERMS = {
    "university": ("university",),
    "research institution": ("research institution", "research institute", "research centre", "research center"),
    "research institute": ("research institution", "research institute", "research centre", "research center"),
    "ngo": ("ngo", "non-governmental organisation", "non-governmental organization"),
}
PARTNERSHIP_TERMS = (
    "partner organisation", "partner organization", "letter of commitment", "committed partner", "consortium",
)
SECTION_HINTS: dict[str, Cat] = {
    "eligib": Cat.APPLICANT_ELIGIBILITY,
    "required document": Cat.MANDATORY_DOCUMENT,
    "documents": Cat.MANDATORY_DOCUMENT,
    "funding": Cat.BUDGET_LIMIT,
    "budget": Cat.BUDGET_LIMIT,
    "duration": Cat.PROJECT_DURATION,
    "priorit": Cat.THEMATIC_PRIORITY,
    "theme": Cat.THEMATIC_PRIORITY,
    "submission": Cat.SUBMISSION,
    "evaluation": Cat.EVALUATION_CRITERIA,
    "declaration": Cat.DECLARATIONS,
    "ethic": Cat.ETHICS,
    "partner": Cat.PARTNERSHIP,
}
_GENERIC_WORDS = {"applicant", "applicants", "proposal", "proposals", "project", "projects", "lead", "call"}


@dataclass
class _Classification:
    category: Cat
    title: str
    parameters: dict[str, Any] = field(default_factory=dict)
    structured: bool = False


def _has(lower: str, term: str) -> bool:
    return re.search(rf"(?<![a-z]){re.escape(term)}(?![a-z])", lower) is not None


def _document_type(lower: str) -> str | None:
    for doc_type, terms in DOCUMENT_TYPES.items():
        if any(_has(lower, term) for term in terms):
            return doc_type
    return None


def _list_items(sentence: str) -> list[str]:
    if ":" not in sentence:
        return []
    tail = sentence.split(":", 1)[1].strip().rstrip(".")
    items = re.split(r",\s*(?:or\s+|and\s+)?|\s+or\s+|\s+and\s+", tail)
    return [item.strip() for item in items if len(item.strip()) > 2]


def _classify(sentence: str) -> _Classification | None:
    lower = sentence.lower()

    if "declaration" in lower or "conflict of interest" in lower:
        return _Classification(Cat.DECLARATIONS, "Signed declaration", {"document_type": "declaration"}, True)

    amounts = parse_amounts(sentence)
    if amounts:
        amount = amounts[0]
        if re.search(r"\b(maximum|ceiling|up to|not exceed|at most|cap)\b", lower):
            return _Classification(
                Cat.BUDGET_LIMIT, f"Maximum funding: {amount.currency} {amount.value:,.0f}",
                {"max_amount": amount.value, "currency": amount.currency}, True,
            )
        if re.search(r"\b(minimum|at least)\b", lower):
            return _Classification(
                Cat.FUNDING_AMOUNT, f"Minimum funding: {amount.currency} {amount.value:,.0f}",
                {"min_amount": amount.value, "currency": amount.currency}, True,
            )

    durations = parse_durations(sentence)
    if durations and re.search(r"\b(duration|period|not exceed|maximum|up to|at most)\b", lower):
        months = durations[0].months
        return _Classification(Cat.PROJECT_DURATION, f"Maximum duration: {months:g} months", {"max_months": months}, True)

    doc_type = _document_type(lower)
    if doc_type and _SUBMIT_VERB.search(sentence):
        parameters: dict[str, Any] = {"document_type": doc_type}
        if _CONDITIONAL.search(sentence):
            parameters["conditional"] = True
        return _Classification(Cat.MANDATORY_DOCUMENT, f"Required document: {DOCUMENT_LABELS[doc_type]}", parameters, True)

    if "deadline" in lower or "no later than" in lower or "closing date" in lower:
        date = _DATE.search(sentence)
        return _Classification(Cat.DEADLINE, "Submission deadline", {"date_text": date.group()} if date else {}, bool(date))
    if re.search(r"\b(ethic|consent|irb)", lower):
        return _Classification(Cat.ETHICS, "Ethics requirement")
    if re.search(r"\b(permit|licen[cs]e|authori[sz]ation)", lower):
        return _Classification(Cat.PERMITS, "Permit or authorization requirement")
    if re.search(r"\b(evaluated|assessed on|scoring|evaluation criteria)\b", lower):
        return _Classification(Cat.EVALUATION_CRITERIA, "Evaluation criteria")
    if re.search(r"\b(priorit|thematic|theme|focus area)", lower):
        items = _list_items(sentence)
        return _Classification(Cat.THEMATIC_PRIORITY, "Addresses a thematic priority", {"any_of": items} if items else {}, bool(items))
    if re.search(r"\b(research area|research domain|field of)\b", lower):
        items = _list_items(sentence)
        return _Classification(Cat.RESEARCH_DOMAIN, "Research domain", {"any_of": items} if items else {}, bool(items))

    qualification = next((term for term in QUALIFICATION_TERMS if _has(lower, term)), None)
    if qualification or "qualification" in lower or "years of experience" in lower:
        any_of = list(QUALIFICATION_TERMS[qualification]) if qualification else []
        return _Classification(Cat.QUALIFICATIONS, "Applicant qualification", {"any_of": any_of} if any_of else {}, bool(any_of))

    if re.search(r"\b(partner|consortium|collaborat)", lower):
        return _Classification(Cat.PARTNERSHIP, "Partnership requirement", {"any_of": list(PARTNERSHIP_TERMS)}, True)

    country = next((c for c in COUNTRIES if c.lower() in lower), None)
    if country or re.search(r"\b(based in|located in|resident|registered in)\b", lower):
        parameters = {"country": country} if country else {}
        title = f"Geographic eligibility: {country}" if country else "Geographic eligibility"
        return _Classification(Cat.GEOGRAPHIC_ELIGIBILITY, title, parameters, bool(country))

    institution_types = [term for term in INSTITUTION_TERMS if _has(lower, term)]
    if institution_types or re.search(r"\b(institution|organi[sz]ation|registered)\b", lower):
        any_of = sorted({alias for term in institution_types for alias in INSTITUTION_TERMS[term]})
        return _Classification(
            Cat.INSTITUTION_ELIGIBILITY, "Institutional eligibility", {"any_of": any_of} if any_of else {}, bool(any_of)
        )
    if re.search(r"\b(applicant|investigator|researcher|eligible)", lower):
        return _Classification(Cat.APPLICANT_ELIGIBILITY, "Applicant eligibility")
    if re.search(r"\b(submit|portal|format|page limit|font|language)\b", lower):
        return _Classification(Cat.SUBMISSION, "Submission requirement")
    return None


def _section_category(section: str | None) -> Cat | None:
    if not section:
        return None
    lower = section.lower()
    return next((cat for hint, cat in SECTION_HINTS.items() if hint in lower), None)


def extract_requirements(document: ExtractedDocument, *, grant_call_id: str, rfp_document_id: str) -> list[RfpCriterion]:
    criteria: list[RfpCriterion] = []
    seen: set[str] = set()
    for context in iter_lines(document):
        section_category = _section_category(context.section)
        for sentence in split_sentences(context.line):
            if len(sentence.split()) < 4 or sentence.lower() in seen:
                continue
            listed_under_requirements = section_category == Cat.MANDATORY_DOCUMENT
            if not _MODAL.search(sentence) and not listed_under_requirements:
                continue
            classification = _classify(sentence)
            if classification is None:
                classification = _Classification(Cat.OTHER, " ".join(sentence.split()[:8]) + "…")
            span = locate_span(document, sentence)
            if span is None:
                continue  # never emit a requirement we cannot cite verbatim
            seen.add(sentence.lower())

            confidence = 0.55
            if _STRONG_MODAL.search(sentence):
                confidence += 0.2
            if section_category is not None and (
                section_category == classification.category
                or (section_category == Cat.APPLICANT_ELIGIBILITY and classification.category in {
                    Cat.QUALIFICATIONS, Cat.INSTITUTION_ELIGIBILITY, Cat.GEOGRAPHIC_ELIGIBILITY, Cat.PARTNERSHIP,
                })
                or (section_category == Cat.BUDGET_LIMIT and classification.category == Cat.PROJECT_DURATION)
            ):
                confidence += 0.1
            if classification.structured:
                confidence += 0.1
            if classification.category == Cat.OTHER:
                confidence = 0.4
            confidence = round(min(confidence, 0.95), 2)

            keywords = [w for w in dict.fromkeys(content_words(sentence)) if w not in _GENERIC_WORDS][:6]
            parameters = {**classification.parameters, "keywords": keywords}
            criteria.append(RfpCriterion(
                grant_call_id=grant_call_id,
                rfp_document_id=rfp_document_id,
                criterion_code=f"R{len(criteria) + 1:02d}",
                category=classification.category,
                title=classification.title,
                requirement_text=span.text,
                source_page=span.page_number,
                source_section=span.section,
                citation_locator=span.citation_locator,
                required="should" not in sentence.lower(),
                extracted_confidence=confidence,
                status=CriterionStatus.EXTRACTED if confidence >= 0.7 else CriterionStatus.NEEDS_REVIEW,
                parameters=parameters,
            ))
    return criteria
