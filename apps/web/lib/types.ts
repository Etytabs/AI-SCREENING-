// Mirrors services/grant_workflow/models.py and services/grant_workflow/views.py.

export type Role = "GRANT_ADMINISTRATOR" | "REVIEWER" | "SYSTEM_ADMINISTRATOR";
export type DataOrigin = "SYNTHETIC" | "UPLOADED" | "PROVIDER";
export type GrantCallStatus =
  | "DRAFT"
  | "REQUIREMENTS_PENDING"
  | "READY_FOR_SUBMISSIONS"
  | "SCREENING"
  | "REVIEW"
  | "CLOSED"
  | "ARCHIVED";
export type CriterionStatus = "EXTRACTED" | "VERIFIED" | "EDITED" | "REJECTED" | "NEEDS_REVIEW";
export type CriterionCategory =
  | "applicant_eligibility"
  | "institution_eligibility"
  | "geographic_eligibility"
  | "thematic_priority"
  | "research_domain"
  | "partnership"
  | "mandatory_document"
  | "budget_limit"
  | "funding_amount"
  | "project_duration"
  | "qualifications"
  | "ethics"
  | "permits"
  | "submission"
  | "deadline"
  | "evaluation_criteria"
  | "declarations"
  | "other";
export type RunState = "QUEUED" | "RUNNING" | "COMPLETE" | "PARTIAL" | "FAILED" | "BLOCKED";
export type StageName =
  | "DOCUMENT_EXTRACTION"
  | "REQUIREMENT_MAPPING"
  | "ELIGIBILITY"
  | "COMPLETENESS"
  | "DUPLICATION"
  | "TEXT_SIMILARITY"
  | "NOVELTY"
  | "EVIDENCE";
export type StageStatus = "PENDING" | "RUNNING" | "COMPLETE" | "FAILED" | "SKIPPED";
export type FindingType = "eligibility" | "completeness" | "duplication" | "plagiarism" | "novelty";
export type FindingStatus = "PASS" | "FAIL" | "REVIEW_REQUIRED";
export type ReviewState = "PENDING" | "CONFIRMED" | "DISMISSED" | "REVIEW_REQUESTED" | "ESCALATED";
export type ReviewerAction = "CONFIRM" | "DISMISS" | "REQUEST_REVIEW" | "ESCALATE";
export type EvidenceRelationship = "SUPPORTS" | "CONTRADICTS" | "PARTIALLY_SUPPORTS" | "UNCERTAIN";

export interface GrantCall {
  id: string;
  name: string;
  organization: string;
  reference: string | null;
  description: string | null;
  open_date: string | null;
  close_date: string | null;
  funding_min: number | null;
  funding_max: number | null;
  currency: string | null;
  domains: string[];
  status: GrantCallStatus;
  created_at: string;
  updated_at: string;
  created_by: string;
  data_origin: DataOrigin;
}

export interface GrantCallInput {
  name: string;
  organization: string;
  reference?: string | null;
  description?: string | null;
  open_date?: string | null;
  close_date?: string | null;
  funding_min?: number | null;
  funding_max?: number | null;
  currency?: string | null;
  domains?: string[];
}

export interface RfpDocument {
  id: string;
  grant_call_id: string;
  filename: string;
  version: number;
  file_hash: string | null;
  uploaded_at: string;
  uploaded_by: string;
  extraction_status: string;
  page_count: number | null;
}

export interface RfpCriterion {
  id: string;
  grant_call_id: string;
  rfp_document_id: string | null;
  criterion_code: string;
  category: CriterionCategory;
  title: string;
  description: string | null;
  requirement_text: string;
  source_page: number | null;
  source_section: string | null;
  citation_locator: string | null;
  source_type: string;
  required: boolean;
  active: boolean;
  extracted_confidence: number | null;
  status: CriterionStatus;
  parameters: Record<string, unknown>;
  administrator_note: string | null;
  verified_by: string | null;
  verified_at: string | null;
  screening_use: "eligibility" | "completeness" | "informational";
  is_confirmed: boolean;
}

export interface RfpUploadResponse {
  rfp_document: RfpDocument;
  requirements: RfpCriterion[];
  grant_call: GrantCall;
}

export interface Applicant {
  id: string;
  name: string | null;
  email: string | null;
  phone: string | null;
  country: string | null;
}

export interface Institution {
  id: string;
  name: string | null;
  country: string | null;
  type: string | null;
}

export interface Application {
  id: string;
  grant_call_id: string;
  application_reference: string;
  title: string | null;
  status: "SUBMITTED" | "IN_REVIEW" | "REVIEW_COMPLETE";
  processing_status: "UPLOADED" | "EXTRACTED" | "PARTIAL" | "EXTRACTION_FAILED";
  screening_status: string;
  requested_amount: number | null;
  currency: string | null;
  domain: string | null;
  latest_run_id: string | null;
  last_screened_at: string | null;
  data_origin: DataOrigin;
}

export interface ApplicationDocument {
  id: string;
  application_id: string;
  filename: string;
  document_type: string;
  file_hash: string | null;
  version: number;
  uploaded_at: string;
  extraction_status: string;
  page_count: number | null;
  error: string | null;
}

export interface PendingUpload {
  id: string;
  grant_call_id: string;
  filename: string;
  extraction_status: string;
  reason: string;
  uploaded_at: string;
}

export interface UploadResponse {
  files_received: number;
  applications_created: string[];
  applications_updated: string[];
  documents_associated: number;
  requires_manual_association: PendingUpload[];
  errors: string[];
  duplicates: string[];
}

export interface StageState {
  stage: StageName;
  status: StageStatus;
  started_at: string | null;
  completed_at: string | null;
  message: string | null;
}

export interface ScreeningRun {
  id: string;
  grant_call_id: string;
  application_id: string;
  batch_id: string | null;
  status: RunState;
  started_at: string | null;
  completed_at: string | null;
  pipeline_version: string;
  error: string | null;
  stages: StageState[];
  finding_ids: string[];
  coverage: {
    sources?: { source_id: string; state: RunState; message: string }[];
    criteria_applied?: number;
    evidence?: { evidence_items: number; valid_citations: number; downgraded_findings: number };
  };
}

export interface ScreeningBatch {
  id: string;
  grant_call_id: string;
  run_ids: string[];
  created_by: string;
  created_at: string;
}

export interface StageProgress {
  stage: StageName;
  completed: number;
  failed: number;
  total: number;
  percent_processed: number;
}

export interface BatchProgress {
  batch_id: string;
  grant_call_id: string;
  status: RunState;
  total: number;
  finished: number;
  stages: StageProgress[];
  runs: ScreeningRun[];
}

export interface FindingEvidence {
  evidence_id: string;
  finding_id: string;
  source_id: string;
  source_type: string;
  document_id: string | null;
  page: number | null;
  section: string | null;
  text: string;
  field: string | null;
  relationship: EvidenceRelationship;
  citation_locator: string | null;
  citation_valid: boolean | null;
}

export interface SimilarityMatch {
  match_id: string;
  source_type: string;
  record_id: string;
  application_id: string | null;
  document_id: string | null;
  title: string | null;
  similarity_score: number;
  lexical_score: number | null;
  semantic_score: number | null;
  reranker_score: number | null;
  matched_section: string | null;
  matched_passage: string | null;
  matching_concepts: string[];
  explanation: string;
  method: string;
  data_origin: DataOrigin;
}

export interface Finding {
  finding_id: string;
  screening_run_id: string;
  application_id: string;
  grant_call_id: string;
  criterion_id: string | null;
  type: FindingType;
  status: FindingStatus;
  title: string;
  signal: string | null;
  confidence: number | null;
  explanation: string;
  recommended_action: string;
  method: string;
  created_at: string;
  review_state: ReviewState;
  evidence: FindingEvidence[];
  matches: SimilarityMatch[];
  details: Record<string, unknown>;
}

export interface ReviewerDecision {
  id: string;
  finding_id: string;
  action: ReviewerAction;
  reviewer_id: string;
  reviewer_role: Role;
  note: string;
  previous_state: ReviewState;
  new_state: ReviewState;
  created_at: string;
}

export interface ReviewerNote {
  id: string;
  finding_id: string;
  author_id: string;
  note: string;
  created_at: string;
}

export interface FindingDetail {
  finding: Finding;
  decisions: ReviewerDecision[];
  notes: ReviewerNote[];
}

export interface AuditLogEntry {
  event_type: string;
  actor: string;
  entity_id: string;
  grant_call_id: string | null;
  timestamp: string;
  details: Record<string, unknown>;
}

export interface DataSource {
  source_id: string;
  provider: string;
  source_name: string;
  source_type: string;
  access_status: string;
  required_for_core_workflow: boolean;
  coverage: string | null;
  methodology: string | null;
}

export interface DocumentContent {
  document_id: string;
  filename: string;
  owner_type: "application" | "grant_call";
  owner_id: string;
  extraction_status: string;
  pages: { page_number: number; text: string; lines: string[] }[];
}

export type Rollup = FindingStatus | "NOT_SCREENED";

export interface ApplicationRow {
  id: string;
  application_reference: string;
  title: string | null;
  applicant_name: string | null;
  institution_name: string | null;
  country: string | null;
  requested_amount: number | null;
  currency: string | null;
  domain: string | null;
  document_count: number;
  unreadable_documents: number;
  processing_status: string;
  screening_status: string;
  status: string;
  eligibility: Rollup;
  completeness: Rollup;
  duplication: string;
  text_similarity: string;
  novelty: string;
  open_findings: number;
  reviewed_findings: number;
  total_findings: number;
  review_progress: "NOT_SCREENED" | "PENDING" | "IN_PROGRESS" | "COMPLETE";
  last_screened_at: string | null;
  latest_run_id: string | null;
  data_origin: DataOrigin;
}

export interface ApplicationDetail {
  application: Application;
  row: ApplicationRow;
  applicant: Applicant | null;
  institution: Institution | null;
  documents: ApplicationDocument[];
  latest_run: ScreeningRun | null;
}

export interface DashboardSummary {
  grant_call: GrantCall;
  requirements_total: number;
  requirements_confirmed: number;
  applications_total: number;
  screening_status_counts: Record<string, number>;
  eligibility_counts: Record<string, number>;
  completeness_counts: Record<string, number>;
  duplication_flags: number;
  text_similarity_flags: number;
  novelty_counts: Record<string, number>;
  findings_total: number;
  findings_by_status: Record<string, number>;
  findings_reviewed: number;
  findings_pending_review: number;
  applications_review_complete: number;
  latest_batch: BatchProgress | null;
  sources: DataSource[];
  contains_synthetic_data: boolean;
  disclaimer: string;
}

export interface ReportFinding {
  finding_id: string;
  type: FindingType;
  status: FindingStatus;
  signal: string | null;
  title: string;
  explanation: string;
  review_state: ReviewState;
  evidence_count: number;
  valid_citations: number;
  decisions: ReviewerDecision[];
}

export interface ScreeningReport {
  generated_at: string;
  grant_call: GrantCall;
  requirements: RfpCriterion[];
  summary: DashboardSummary;
  applications: { row: ApplicationRow; findings: ReportFinding[] }[];
  disclaimer: string;
  synthetic_notice: string | null;
}

export interface SessionInfo {
  user_id: string;
  role: Role | null;
  roles: Role[];
  identity_mode: string;
  notice: string;
}
