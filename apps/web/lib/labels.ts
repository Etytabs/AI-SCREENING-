import type { CriterionCategory, FindingType, GrantCallStatus, ReviewerAction, ReviewState, Role, StageName } from "./types";

export const ROLE_LABELS: Record<Role, string> = {
  NCST_GRANT_PERSONNEL: "NCST Grant Personnel",
  GRANT_INSTITUTION: "Grant Institution",
  RESEARCHER_APPLICANT: "Researcher / Applicant",
  GRANT_ADMINISTRATOR: "Grant Administrator (legacy)",
  REVIEWER: "Reviewer (legacy)",
  SYSTEM_ADMINISTRATOR: "System Administrator (legacy)",
};

export const CALL_STATUS_LABELS: Record<GrantCallStatus, string> = {
  DRAFT: "Draft",
  REQUIREMENTS_PENDING: "Requirements pending",
  READY_FOR_SUBMISSIONS: "Ready for submissions",
  SCREENING: "Screening",
  REVIEW: "In review",
  CLOSED: "Closed",
  ARCHIVED: "Archived",
};

export const FINDING_TYPE_LABELS: Record<FindingType, string> = {
  eligibility: "Eligibility",
  completeness: "Completeness",
  duplication: "Duplication signal",
  plagiarism: "Plagiarism check",
  novelty: "Novelty signal",
};

export const STAGE_LABELS: Record<StageName, string> = {
  DOCUMENT_EXTRACTION: "Document extraction",
  REQUIREMENT_MAPPING: "Requirement mapping",
  ELIGIBILITY: "Eligibility",
  COMPLETENESS: "Completeness",
  DUPLICATION: "Duplication",
  TEXT_SIMILARITY: "Text similarity",
  NOVELTY: "Novelty",
  EVIDENCE: "Evidence validation",
};

// What the screening column answers: has this submission been screened, and what came out of it.
export const SCREENING_STATE_LABELS: Record<string, string> = {
  NOT_SCREENED: "NOT SCREENED",
  QUEUED: "QUEUED",
  RUNNING: "SCREENING…",
  PROCESSING: "SCREENING…",
  SCREENED: "SCREENED · NO ISSUES",
  REVIEW_REQUIRED: "SCREENED · NEEDS REVIEW",
  PARTIAL: "SCREENED · INCOMPLETE",
  BLOCKED: "COULD NOT SCREEN",
  FAILED: "SCREENING FAILED",
};

export const REVIEW_STATE_LABELS: Record<ReviewState, string> = {
  PENDING: "Awaiting reviewer",
  CONFIRMED: "Confirmed by reviewer",
  DISMISSED: "Dismissed by reviewer",
  REVIEW_REQUESTED: "Further review requested",
  ESCALATED: "Escalated",
};

export const ACTION_LABELS: Record<ReviewerAction, string> = {
  CONFIRM: "Confirm finding",
  DISMISS: "Dismiss finding",
  REQUEST_REVIEW: "Request further review",
  ESCALATE: "Escalate",
};

export const CATEGORY_LABELS: Record<CriterionCategory, string> = {
  applicant_eligibility: "Applicant eligibility",
  institution_eligibility: "Institution eligibility",
  geographic_eligibility: "Geographic eligibility",
  thematic_priority: "Thematic priority",
  research_domain: "Research domain",
  partnership: "Partnership",
  mandatory_document: "Mandatory document",
  budget_limit: "Budget limit",
  funding_amount: "Funding amount",
  project_duration: "Project duration",
  qualifications: "Qualifications",
  ethics: "Ethics",
  permits: "Permits",
  submission: "Submission",
  deadline: "Deadline",
  evaluation_criteria: "Evaluation criteria",
  declarations: "Declarations",
  other: "Other",
};

export const SIGNAL_LABELS: Record<string, string> = {
  POSSIBLE_DUPLICATION: "Possible duplication",
  NO_SIGNIFICANT_SIMILARITY: "No significant similarity",
  SHARED_PASSAGES_FOUND: "Shared passages",
  NO_SHARED_PASSAGES: "No shared passages",
  NOT_ASSESSABLE: "Not assessable",
  HIGH: "High novelty signal",
  MEDIUM: "Medium novelty signal",
  LOW: "Low novelty signal",
  REVIEW_REQUIRED: "Review required",
  NOT_SCREENED: "Not screened",
};

export function humanize(value: string | null | undefined): string {
  if (!value) return "—";
  return value.replace(/_/g, " ").toLowerCase().replace(/^\w/, (c) => c.toUpperCase());
}

export function formatAmount(value: number | null | undefined, currency: string | null | undefined): string {
  if (value === null || value === undefined) return "Not stated";
  return `${currency ?? ""} ${value.toLocaleString("en-US")}`.trim();
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("en-GB", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}
