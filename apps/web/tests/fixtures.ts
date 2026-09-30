import type {
  ApplicationRow,
  BatchProgress,
  DashboardSummary,
  DataSource,
  Finding,
  FindingDetail,
  FindingEvidence,
  GrantCall,
  RfpCriterion,
  UploadResponse,
} from "../lib/types";

const NOW = "2026-09-30T10:00:00Z";

export function grantCall(overrides: Partial<GrantCall> = {}): GrantCall {
  return {
    id: "call-1", name: "Climate Resilience Research Call", organization: "NCST (synthetic)", reference: "NRIF-DEMO-2026",
    description: null, open_date: "2026-01-01", close_date: "2026-03-31", funding_min: 10000000, funding_max: 50000000,
    currency: "RWF", domains: ["climate"], status: "READY_FOR_SUBMISSIONS", created_at: NOW, updated_at: NOW,
    created_by: "demo", data_origin: "SYNTHETIC", ...overrides,
  };
}

export function criterion(overrides: Partial<RfpCriterion> = {}): RfpCriterion {
  return {
    id: "crit-1", grant_call_id: "call-1", rfp_document_id: "rfp-1", criterion_code: "R01", category: "applicant_eligibility",
    title: "Applicant institution", description: null, requirement_text: "The lead applicant must be affiliated with a registered Rwandan institution.",
    source_page: 1, source_section: "Eligibility", citation_locator: "rfp.txt#p1", source_type: "rfp_document", required: true,
    active: true, extracted_confidence: 0.9, status: "EXTRACTED", parameters: {}, administrator_note: null, verified_by: null,
    verified_at: null, screening_use: "eligibility", is_confirmed: false, ...overrides,
  };
}

export function row(overrides: Partial<ApplicationRow> = {}): ApplicationRow {
  return {
    id: "app-1", application_reference: "APP-001", title: "Drought early warning", applicant_name: "A. Uwimana",
    institution_name: "University of Rwanda", country: "Rwanda", requested_amount: 40000000, currency: "RWF", domain: "climate",
    document_count: 5, unreadable_documents: 0, processing_status: "EXTRACTED", screening_status: "SCREENED", status: "IN_REVIEW",
    eligibility: "PASS", completeness: "PASS", duplication: "NO_SIGNIFICANT_SIMILARITY", text_similarity: "NO_SHARED_PASSAGES",
    novelty: "MEDIUM", open_findings: 0, reviewed_findings: 0, total_findings: 12, review_progress: "PENDING",
    last_screened_at: NOW, latest_run_id: "run-1", data_origin: "SYNTHETIC", ...overrides,
  };
}

export function evidence(overrides: Partial<FindingEvidence> = {}): FindingEvidence {
  return {
    evidence_id: "ev-1", finding_id: "f-1", source_id: "doc-1", source_type: "application_document", document_id: "doc-1",
    page: 1, section: "Budget", text: "Total requested amount: RWF 65,000,000", field: null, relationship: "CONTRADICTS",
    citation_locator: "proposal.txt#p1", citation_valid: true, ...overrides,
  };
}

export function finding(overrides: Partial<Finding> = {}): Finding {
  return {
    finding_id: "f-1", screening_run_id: "run-1", application_id: "app-1", grant_call_id: "call-1", criterion_id: "crit-6",
    type: "eligibility", status: "FAIL", title: "R06 · Maximum funding amount", signal: null, confidence: 0.8,
    explanation: "The requested amount exceeds the call maximum of RWF 50,000,000.", recommended_action: "Verify the budget total.",
    method: "call_criteria_rules_v0.1", created_at: NOW, review_state: "PENDING", evidence: [evidence()], matches: [], details: {},
    ...overrides,
  };
}

export function findingDetail(overrides: Partial<Finding> = {}): FindingDetail {
  return { finding: finding(overrides), decisions: [], notes: [] };
}

export function source(overrides: Partial<DataSource> = {}): DataSource {
  return {
    source_id: "same_call_applications", provider: "AI-SCREENING", source_name: "Applications in this call",
    source_type: "internal", access_status: "AVAILABLE", required_for_core_workflow: true, coverage: null, methodology: null,
    ...overrides,
  };
}

export function batch(overrides: Partial<BatchProgress> = {}): BatchProgress {
  return { batch_id: "batch-1", grant_call_id: "call-1", status: "COMPLETE", total: 5, finished: 5, stages: [], runs: [], ...overrides };
}

export function summary(overrides: Partial<DashboardSummary> = {}): DashboardSummary {
  return {
    grant_call: grantCall({ status: "REVIEW" }), requirements_total: 15, requirements_confirmed: 15, applications_total: 5,
    screening_status_counts: { SCREENED: 5 }, eligibility_counts: { PASS: 3, FAIL: 1, REVIEW_REQUIRED: 1 },
    completeness_counts: { PASS: 2, FAIL: 3 }, duplication_flags: 1, text_similarity_flags: 2,
    novelty_counts: { HIGH: 1, MEDIUM: 1, LOW: 2, REVIEW_REQUIRED: 1 }, findings_total: 60, findings_by_status: {},
    findings_reviewed: 4, findings_pending_review: 11, applications_review_complete: 0, latest_batch: batch(),
    sources: [source(), source({ source_id: "openalex", source_name: "OpenAlex", access_status: "NOT_CONFIGURED", required_for_core_workflow: false })],
    contains_synthetic_data: true, disclaimer: "AI screening signals support, and never replace, human review.", ...overrides,
  };
}

export function uploadResponse(overrides: Partial<UploadResponse> = {}): UploadResponse {
  return {
    files_received: 3, applications_created: ["APP-010"], applications_updated: [], documents_associated: 2,
    requires_manual_association: [], errors: [], duplicates: [], ...overrides,
  };
}
