from services.ncst_requirements.models import (
    LifecycleStage,
    MonitoringIndicator,
    Requirement,
    RequirementSource,
)


SOURCE_REGISTRY: tuple[RequirementSource, ...] = (
    RequirementSource(
        "ncst_annual_report_2025_2026",
        "NCST Annual Report FY 2025-2026",
        "official_report",
        "official_source",
        "NCST",
        "Strategic and operational alignment source; not a substitute for a call-specific rule document.",
    ),
    RequirementSource(
        "rigms",
        "Research Innovation Grants Management System (RIGMS)",
        "institutional_system",
        "needs_authorization",
        "NCST",
        "Direct integration requires authorized NCST/RIGMS access or API credentials.",
    ),
    RequirementSource(
        "nrif_funding_procedures",
        "NRIF Funding Procedures Manual",
        "procedure_manual",
        "official_source",
        "NCST",
        "Use the active/revised manual version when configuring operational rules.",
    ),
    RequirementSource(
        "active_call_package",
        "Active NRIF/RFP/RFA call package",
        "call_document",
        "needs_authorization",
        "NCST",
        "The authoritative source for call-specific eligibility, documents, budget and deadlines.",
    ),
    RequirementSource(
        "research_innovation_repository",
        "Rwanda Research and Innovation Repository",
        "national_repository",
        "needs_authorization",
        "NCST",
        "Use authorized access for synchronization; do not scrape or overwrite records without approval.",
    ),
)


REQUIREMENTS: tuple[Requirement, ...] = (
    Requirement("APP-01", "application", "Call-specific application fields", "Validate required fields against the active call package.", "needs_authorization", "active_call_package", "active call package"),
    Requirement("CMP-01", "completeness", "Mandatory documents and sections", "Detect missing required application components before technical review.", "configured", "nrif_funding_procedures", "administrative screening"),
    Requirement("ELG-01", "eligibility", "Applicant and institutional eligibility", "Evaluate applicant/institution conditions from the active call rules.", "configured", "active_call_package", "call-specific eligibility"),
    Requirement("PLG-01", "plagiarism", "Similarity/plagiarism screening", "Surface similarity evidence for authorized technical-team review; never declare plagiarism from a score alone.", "configured", "nrif_funding_procedures", "plagiarism/similarity screening"),
    Requirement("REV-01", "review", "Reviewer evidence package", "Provide findings, evidence, provenance and unresolved questions to reviewers.", "configured", "rigms", "review workflow"),
    Requirement("BUD-01", "budget", "Budget compliance", "Check budget fields and ceilings against the active call configuration.", "needs_authorization", "active_call_package", "call-specific budget rules"),
    Requirement("TEAM-01", "team", "PI, collaborators and partnerships", "Validate required team, affiliation and partnership evidence.", "needs_authorization", "active_call_package", "call-specific team requirements"),
    Requirement("ETH-01", "ethics_permits", "Ethics and research permits", "Track evidence where the call or research activity requires approvals or permits.", "needs_authorization", "active_call_package", "call-specific ethics/permit requirements"),
    Requirement("MEL-01", "monitoring_evaluation", "Technical and financial progress", "Structure evidence for progress, outputs, financial compliance and implementation status.", "configured", "ncst_annual_report_2025_2026", "M&E objectives"),
    Requirement("CLO-01", "closeout", "Project closing evidence", "Preserve final outputs, financial evidence, lessons and unresolved actions.", "configured", "rigms", "project closeout"),
    Requirement("COM-01", "commercialization", "Research-to-impact pathway", "Track technology transfer, industry linkage, uptake and commercialization evidence where applicable.", "configured", "ncst_annual_report_2025_2026", "research-to-impact alignment"),
)


LIFECYCLE: tuple[LifecycleStage, ...] = (
    LifecycleStage("application", "Application", "Capture and validate a submitted proposal.", ("document extraction", "completeness detection"), "Applicant / NCST grants team"),
    LifecycleStage("screening", "Administrative screening", "Prepare consistent evidence for completeness, eligibility and similarity review.", ("rules evaluation", "semantic retrieval", "text-overlap analysis"), "NCST technical team"),
    LifecycleStage("review", "Technical review", "Support reviewer assessment without replacing human judgment.", ("evidence retrieval", "candidate comparison", "explanation"), "Authorized reviewers"),
    LifecycleStage("award", "Award and contracting", "Preserve approved conditions and the baseline against which implementation is monitored.", ("structured extraction", "baseline validation"), "NCST / host institution"),
    LifecycleStage("implementation", "Implementation", "Track project evidence against objectives and approved plans.", ("document reconciliation", "anomaly detection"), "PI / project team"),
    LifecycleStage("mel", "Monitoring, evaluation and learning", "Support recurring evidence-based monitoring of technical and financial progress.", ("evidence summarization", "indicator extraction", "change detection"), "NCST M&E team"),
    LifecycleStage("closeout", "Project closeout", "Consolidate outputs, financial evidence, lessons and final records.", ("output reconciliation", "document completeness"), "NCST / host institution"),
    LifecycleStage("impact", "Research-to-impact", "Connect research outputs to technology transfer, commercialization and uptake evidence.", ("publication reconciliation", "entity resolution", "impact evidence linking"), "NCST / researchers / partners"),
)


MONITORING_INDICATORS: tuple[MonitoringIndicator, ...] = (
    MonitoringIndicator("MEL-TECH", "Technical progress", "technical", ("progress report", "milestone evidence", "outputs"), "quarterly"),
    MonitoringIndicator("MEL-OUT", "Expected outputs and achievements", "outputs", ("deliverables", "datasets", "publications", "prototypes"), "quarterly"),
    MonitoringIndicator("MEL-FIN", "Financial management and compliance", "financial", ("financial report", "approved budget", "variance evidence"), "quarterly"),
    MonitoringIndicator("MEL-DATA", "Data and experimental evidence", "research", ("datasets", "laboratory/field evidence", "analysis artifacts"), "quarterly"),
    MonitoringIndicator("MEL-SUP", "Implementation support needs", "management", ("risk/issues log", "support request", "corrective action"), "quarterly"),
    MonitoringIndicator("MEL-IMP", "Impact and uptake", "impact", ("adoption evidence", "industry linkage", "technology transfer", "commercialization"), "milestone / closeout"),
)


def list_sources() -> list[RequirementSource]:
    return list(SOURCE_REGISTRY)


def list_requirements() -> list[Requirement]:
    return list(REQUIREMENTS)


def list_lifecycle() -> list[LifecycleStage]:
    return list(LIFECYCLE)


def list_monitoring_indicators() -> list[MonitoringIndicator]:
    return list(MONITORING_INDICATORS)
