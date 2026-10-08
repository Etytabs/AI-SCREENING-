export interface GrantApplication {
  id: string;
  title: string;
  abstract: string;
  full_proposal: string;
  author_name: string;
  institution: string;
  email: string;
  phone?: string;
  budget_amount: number;
  research_area: string;
  keywords?: string[];
  team_members?: any[];
  attachments?: any[];
  submission_date: string;
  status: 'pending' | 'screening' | 'completed' | 'approved' | 'rejected';
  grant_type: string;
  funding_program: string;
  project_duration_months: number;
  expected_outcomes?: any[];
  tenant_id?: string;
}

export interface ScreeningResult {
  application_id: string;
  eligibility_result: any;
  plagiarism_result: any;
  duplication_result: any;
  novelty_result: any;
  overall_score: number;
  recommendation: string;
  requires_human_review: boolean;
  priority_level: string;
  processing_time_seconds: number;
  generated_at: string;
}

export interface ResearcherIdentity {
  permanent_id: string;
  orcid_id?: string;
  email: string;
  email_verified: boolean;
  given_name: string;
  family_name: string;
  name_variants?: string[];
  primary_institution: string;
  affiliations?: any[];
  verification_status: 'pending' | 'verified' | 'rejected';
  verification_method?: string;
  verified_at?: string;
  created_at: string;
  created_by_tenant: string;
  is_active: boolean;
}

export interface ReviewAssignment {
  assignment_id: string;
  application_id: string;
  reviewer_id: string;
  assigned_by: string;
  assigned_at: string;
  due_date?: string;
  status: 'pending' | 'assigned' | 'in_progress' | 'completed';
  priority: string;
}

export interface EvidenceRecord {
  evidence_id: string;
  evidence_type: 'publication' | 'patent' | 'grant' | 'website' | 'report';
  source: 'crossref' | 'openalex' | 'epo' | 'manual' | 'integration';
  source_id: string;
  title: string;
  authors: string[];
  year?: number;
  url?: string;
  similarity_score?: number;
  relevance_score?: number;
  extracted_at: string;
}

export interface User {
  user_id: string;
  tenant_id: string;
  email: string;
  given_name: string;
  family_name: string;
  role: 'admin' | 'reviewer' | 'submitter' | 'viewer';
  is_active: boolean;
  permissions: string[];
}
