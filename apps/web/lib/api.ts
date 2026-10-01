import type {
  ApplicationDetail,
  ApplicationRow,
  ArchivedProject,
  ArchivedProjectInput,
  AuditLogEntry,
  BatchProgress,
  DashboardSummary,
  DataSource,
  DocumentContent,
  Finding,
  FindingDetail,
  GrantCall,
  GrantCallInput,
  PendingUpload,
  ReviewerAction,
  ReviewerDecision,
  ReviewerNote,
  RfpCriterion,
  RfpUploadResponse,
  Role,
  ScreeningBatch,
  ScreeningReport,
  StakeholderResponse,
  UploadResponse,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "https://ai-screening-dhdm.onrender.com";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

export interface Identity {
  role: Role;
  userId: string;
}

function detailMessage(body: unknown, status: number): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item) => (item && typeof item === "object" && "msg" in item ? String((item as { msg: unknown }).msg) : String(item)))
        .join("; ");
    }
  }
  return `Request failed (${status})`;
}

export function createClient(identity: Identity, base: string = API_BASE) {
  async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
    // The deployed API may still be running the legacy role enum while it rolls forward.
    // Keep the product role as NCST_GRANT_PERSONNEL in the UI, but use the legacy
    // administrator wire-role for backward compatibility with that deployment.
    const apiRole = identity.role === "NCST_GRANT_PERSONNEL" ? "GRANT_ADMINISTRATOR" : identity.role;
    const headers: Record<string, string> = { "X-User-Role": apiRole, "X-User-Id": identity.userId };
    let payload: BodyInit | undefined;
    if (body instanceof FormData) payload = body;
    else if (body !== undefined) {
      headers["Content-Type"] = "application/json";
      payload = JSON.stringify(body);
    }
    let response: Response;
    try {
      response = await fetch(`${base}${path}`, { method, headers, body: payload });
    } catch {
      throw new ApiError(0, `The screening API is unreachable at ${base}. No data is shown until it responds.`);
    }
    const text = await response.text();
    let data: unknown = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      if (response.ok) throw new ApiError(response.status, "The API returned a response that is not JSON.");
    }
    if (!response.ok) throw new ApiError(response.status, detailMessage(data, response.status));
    return data as T;
  }

  const q = (params: Record<string, string | undefined>) => {
    const entries = Object.entries(params).filter(([, v]) => v) as [string, string][];
    return entries.length ? `?${new URLSearchParams(entries).toString()}` : "";
  };

  return {
    listCalls: () => request<GrantCall[]>( "GET", "/api/v1/grants"),
    getCall: (id: string) => request<GrantCall>("GET", `/api/v1/grants/${id}`),
    createCall: (input: GrantCallInput) => request<GrantCall>("POST", "/api/v1/grants", input),
    updateCall: (id: string, input: Partial<GrantCallInput> & { status?: string }) =>
      request<GrantCall>("PATCH", `/api/v1/grants/${id}`, input),

    uploadRfp: (id: string, file: File) => {
      const form = new FormData();
      form.append("file", file);
      return request<RfpUploadResponse>("POST", `/api/v1/grants/${id}/rfp`, form);
    },
    listRequirements: (id: string) => request<RfpCriterion[]>("GET", `/api/v1/grants/${id}/requirements`),
    addRequirement: (id: string, input: Partial<RfpCriterion>) =>
      request<RfpCriterion>("POST", `/api/v1/grants/${id}/requirements`, input),
    updateRequirement: (id: string, input: Partial<RfpCriterion>) =>
      request<RfpCriterion>("PATCH", `/api/v1/requirements/${id}`, input),
    verifyRequirement: (id: string, decision: "VERIFY" | "REJECT", note?: string) =>
      request<RfpCriterion>("POST", `/api/v1/requirements/${id}/verify`, { decision, note }),
    setRequirementActive: (id: string, active: boolean) =>
      request<RfpCriterion>("POST", `/api/v1/requirements/${id}/active`, { active }),
    confirmRequirements: (id: string) => request<GrantCall>("POST", `/api/v1/grants/${id}/requirements/confirm`),

    createApplication: (id: string, files: File[], reference?: string) => {
      const form = new FormData();
      files.forEach((f) => form.append("files", f));
      if (reference) form.append("reference", reference);
      return request<UploadResponse>("POST", `/api/v1/grants/${id}/applications`, form);
    },
    batchUpload: (id: string, files: File[]) => {
      const form = new FormData();
      files.forEach((f) => form.append("files", f, (f as File & { webkitRelativePath?: string }).webkitRelativePath || f.name));
      return request<UploadResponse>("POST", `/api/v1/grants/${id}/applications/batch`, form);
    },
    listApplications: (id: string, filters: Record<string, string | undefined> = {}) =>
      request<ApplicationRow[]>( "GET", `/api/v1/grants/${id}/applications${q(filters)}`),
    pendingUploads: (id: string) => request<PendingUpload[]>( "GET", `/api/v1/grants/${id}/pending-uploads`),
    associateUpload: (uploadId: string, body: { application_id?: string; new_reference?: string }) =>
      request<ApplicationRow>("POST", `/api/v1/pending-uploads/${uploadId}/associate`, body),
    getApplication: (id: string) => request<ApplicationDetail>("GET", `/api/v1/applications/${id}`),
    documentContent: (id: string) => request<DocumentContent>("GET", `/api/v1/documents/${id}/content`),

    screenCall: (id: string, applicationIds?: string[]) =>
      request<ScreeningBatch>("POST", `/api/v1/grants/${id}/screen`, applicationIds ? { application_ids: applicationIds } : undefined),
    screenApplication: (id: string) => request<ScreeningBatch>("POST", `/api/v1/applications/${id}/screen`),
    batchProgress: (id: string) => request<BatchProgress>("GET", `/api/v1/screening-batches/${id}`),

    listFindings: (applicationId: string) => request<Finding[]>( "GET", `/api/v1/applications/${applicationId}/findings`),
    getFinding: (id: string) => request<FindingDetail>("GET", `/api/v1/findings/${id}`),
    decide: (id: string, action: ReviewerAction, note: string) =>
      request<ReviewerDecision>("POST", `/api/v1/findings/${id}/decision`, { action, note }),
    addNote: (id: string, note: string) => request<ReviewerNote>("POST", `/api/v1/findings/${id}/notes`, { note }),

    dashboard: (id: string) => request<DashboardSummary>("GET", `/api/v1/grants/${id}/dashboard`),
    audit: (id: string) => request<AuditLogEntry[]>( "GET", `/api/v1/grants/${id}/audit`),
    report: (id: string) => request<ScreeningReport>("GET", `/api/v1/grants/${id}/report`),
    sources: () => request<DataSource[]>("GET", "/api/v1/sources"),
    listDuplicationProjects: () => request<ArchivedProject[]>("GET", "/api/v1/duplication/projects"),
    importDuplicationProject: (input: ArchivedProjectInput) => {
      const form = new FormData();
      form.append("file", input.file);
      form.append("title", input.title);
      form.append("source_type", input.source_type);
      if (input.reference) form.append("reference", input.reference);
      if (input.year !== undefined) form.append("year", String(input.year));
      if (input.organization) form.append("organization", input.organization);
      return request<ArchivedProject>("POST", "/api/v1/duplication/projects", form);
    },
  };
}

export type ApiClient = ReturnType<typeof createClient>;
