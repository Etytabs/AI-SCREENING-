import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ApplicationUpload } from "../components/workflow/ApplicationUpload";
import { CallForm } from "../components/workflow/CallForm";
import { DashboardSummaryView } from "../components/workflow/DashboardSummaryView";
import { DecisionPanel } from "../components/workflow/DecisionPanel";
import { DocumentViewer } from "../components/workflow/DocumentViewer";
import { EvidenceDrawer } from "../components/workflow/EvidenceDrawer";
import { FindingList } from "../components/workflow/FindingList";
import { RequirementReview } from "../components/workflow/RequirementReview";
import { ResultsTable } from "../components/workflow/ResultsTable";
import { StatusBadge } from "../components/workflow/ui";
import type { DocumentContent } from "../lib/types";
import * as fx from "./fixtures";

const noop = async () => {};

describe("grant creation", () => {
  it("requires a name and organization before submitting", async () => {
    const onSubmit = vi.fn();
    render(<CallForm onSubmit={onSubmit} />);
    fireEvent.submit(screen.getByRole("form", { name: "Create grant call" }));
    expect((await screen.findByRole("alert")).textContent).toContain("Call name and organization are required");
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("rejects a minimum above the maximum", async () => {
    const onSubmit = vi.fn();
    render(<CallForm onSubmit={onSubmit} />);
    fireEvent.change(screen.getByLabelText(/Call name/), { target: { value: "Climate call" } });
    fireEvent.change(screen.getByLabelText(/Organization/), { target: { value: "NCST" } });
    fireEvent.change(screen.getByLabelText("Minimum funding"), { target: { value: "500" } });
    fireEvent.change(screen.getByLabelText("Maximum funding"), { target: { value: "100" } });
    fireEvent.submit(screen.getByRole("form", { name: "Create grant call" }));
    expect((await screen.findByRole("alert")).textContent).toContain("Minimum funding cannot exceed maximum");
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits parsed values and reports the created call", async () => {
    const created = fx.grantCall({ status: "DRAFT" });
    const onSubmit = vi.fn().mockResolvedValue(created);
    const onCreated = vi.fn();
    render(<CallForm onSubmit={onSubmit} onCreated={onCreated} />);
    fireEvent.change(screen.getByLabelText(/Call name/), { target: { value: "  Climate call " } });
    fireEvent.change(screen.getByLabelText(/Organization/), { target: { value: "NCST" } });
    fireEvent.change(screen.getByLabelText("Maximum funding"), { target: { value: "50000000" } });
    fireEvent.change(screen.getByLabelText(/Research domains/), { target: { value: "climate, water ," } });
    fireEvent.submit(screen.getByRole("form", { name: "Create grant call" }));
    await waitFor(() => expect(onCreated).toHaveBeenCalledWith(created));
    expect(onSubmit.mock.calls[0][0]).toMatchObject({ name: "Climate call", organization: "NCST", funding_max: 50000000, funding_min: null, domains: ["climate", "water"] });
  });
});

describe("requirement confirmation", () => {
  const actions = { onVerify: vi.fn(noop), onReject: vi.fn(noop), onEdit: vi.fn(noop), onToggleActive: vi.fn(noop), onAdd: vi.fn(noop), onConfirm: vi.fn(noop) };

  it("blocks confirmation while a requirement is unverified and verifies on click", async () => {
    render(<RequirementReview requirements={[fx.criterion()]} canEdit confirmed={false} {...actions} />);
    const confirm = screen.getByRole("button", { name: /Confirm requirements/ }) as HTMLButtonElement;
    expect(confirm.disabled).toBe(true);
    expect(screen.getByText(/1 requirement\(s\) must be verified/)).toBeTruthy();
    fireEvent.click(within(screen.getByTestId("requirement-R01")).getByRole("button", { name: "Verify" }));
    await waitFor(() => expect(actions.onVerify).toHaveBeenCalledWith("crit-1"));
  });

  it("requires a reason to reject", async () => {
    render(<RequirementReview requirements={[fx.criterion()]} canEdit confirmed={false} {...actions} />);
    fireEvent.click(screen.getByRole("button", { name: "Reject" }));
    const submit = screen.getByRole("button", { name: "Reject requirement" }) as HTMLButtonElement;
    expect(submit.disabled).toBe(true);
    fireEvent.change(screen.getByLabelText(/Reason for rejection/), { target: { value: "Not in this call" } });
    fireEvent.click(submit);
    await waitFor(() => expect(actions.onReject).toHaveBeenCalledWith("crit-1", "Not in this call"));
  });

  it("confirms once every active requirement is verified", async () => {
    const verified = [fx.criterion({ status: "VERIFIED", is_confirmed: true }), fx.criterion({ id: "crit-2", criterion_code: "R02", active: false })];
    render(<RequirementReview requirements={verified} canEdit confirmed={false} {...actions} />);
    const confirm = screen.getByRole("button", { name: /Confirm requirements/ }) as HTMLButtonElement;
    expect(confirm.disabled).toBe(false);
    fireEvent.click(confirm);
    await waitFor(() => expect(actions.onConfirm).toHaveBeenCalled());
  });

  it("is read-only for reviewers", () => {
    render(<RequirementReview requirements={[fx.criterion()]} canEdit={false} confirmed={false} {...actions} />);
    expect(screen.queryByRole("button", { name: "Verify" })).toBeNull();
    expect(screen.queryByRole("button", { name: /Confirm requirements/ })).toBeNull();
  });
});

describe("application upload", () => {
  it("sends batch files and shows the upload summary including problems", async () => {
    const onBatch = vi.fn().mockResolvedValue(fx.uploadResponse({ errors: ["notes.exe: unsupported file type"], duplicates: ["APP-001/budget.txt"] }));
    render(<ApplicationUpload onBatch={onBatch} onSingle={vi.fn()} />);
    const file = new File(["Title: Test"], "APP-010__proposal.txt", { type: "text/plain" });
    fireEvent.change(screen.getByLabelText("Application files"), { target: { files: [file] } });
    await waitFor(() => expect(onBatch).toHaveBeenCalledWith([file]));
    expect(await screen.findByText("Upload processed")).toBeTruthy();
    expect(screen.getByText("notes.exe: unsupported file type")).toBeTruthy();
    expect(screen.getByText(/duplicate file\(s\) skipped/)).toBeTruthy();
  });

  it("passes the reference in single-application mode and surfaces API errors", async () => {
    const onSingle = vi.fn().mockRejectedValue(new Error("Empty submission: no files were provided"));
    render(<ApplicationUpload onBatch={vi.fn()} onSingle={onSingle} />);
    fireEvent.click(screen.getByRole("button", { name: "One application" }));
    fireEvent.change(screen.getByLabelText(/Application reference/), { target: { value: "APP-099" } });
    const file = new File([""], "empty.txt");
    fireEvent.change(screen.getByLabelText("Files for one application"), { target: { files: [file] } });
    await waitFor(() => expect(onSingle).toHaveBeenCalledWith([file], "APP-099"));
    expect((await screen.findByRole("alert")).textContent).toContain("Empty submission");
  });
});

describe("dashboard", () => {
  it("summarises counts, workflow progress, coverage gaps and the disclaimer", () => {
    render(<DashboardSummaryView summary={fx.summary()} />);
    expect(screen.getByText("Climate Resilience Research Call")).toBeTruthy();
    expect(screen.getByText("15 of 15 confirmed")).toBeTruthy();
    expect(screen.getByText("11")).toBeTruthy();
    expect(screen.getByText("findings awaiting a reviewer")).toBeTruthy();
    expect(screen.getByText(/Not searched \(1\): OpenAlex/)).toBeTruthy();
    expect(screen.getByText(/never replace, human review/)).toBeTruthy();
    expect(screen.queryByText("Screening in progress")).toBeNull();
  });

  it("shows processing and partial states and an empty state", () => {
    const { unmount } = render(<DashboardSummaryView summary={fx.summary({ latest_batch: fx.batch({ status: "PARTIAL", finished: 2, total: 5 }) })} />);
    expect(screen.getByText("Screening in progress")).toBeTruthy();
    expect(screen.getByText("Some screening runs are partial")).toBeTruthy();
    unmount();
    render(<DashboardSummaryView summary={fx.summary({ applications_total: 0, latest_batch: null })} />);
    expect(screen.getByText("No applications yet")).toBeTruthy();
  });
});

describe("results table", () => {
  const rows = [
    fx.row(),
    fx.row({ id: "app-3", application_reference: "APP-003", eligibility: "FAIL", open_findings: 5, unreadable_documents: 1 }),
    fx.row({ id: "app-5", application_reference: "APP-005", eligibility: "REVIEW_REQUIRED", screening_status: "PARTIAL" }),
  ];

  it("renders status as text and symbol, not colour alone, with links to the workspace", () => {
    render(<ResultsTable rows={rows} filters={{}} onFiltersChange={vi.fn()} />);
    const failRow = screen.getByTestId("row-APP-003");
    const badge = within(failRow).getAllByLabelText("Status: FAIL")[0];
    expect(badge.textContent).toContain("✕");
    expect(badge.textContent).toContain("FAIL");
    expect(within(failRow).getByText("1 unreadable document(s)")).toBeTruthy();
    expect(within(screen.getByTestId("row-APP-005")).getByLabelText("Status: PARTIAL")).toBeTruthy();
    expect(within(failRow).getByRole("link", { name: "APP-003" }).getAttribute("href")).toBe("/dashboard/applications/view?id=app-3");
  });

  it("sorts eligibility issues first and forwards filter changes", () => {
    const onFiltersChange = vi.fn();
    render(<ResultsTable rows={rows} filters={{}} onFiltersChange={onFiltersChange} />);
    fireEvent.change(screen.getByLabelText("Sort applications"), { target: { value: "eligibility" } });
    const order = screen.getAllByTestId(/^row-/).map((el) => el.getAttribute("data-testid"));
    expect(order).toEqual(["row-APP-003", "row-APP-005", "row-APP-001"]);
    fireEvent.change(screen.getByLabelText("Filter by eligibility"), { target: { value: "FAIL" } });
    expect(onFiltersChange).toHaveBeenCalledWith({ eligibility: "FAIL" });
    fireEvent.click(screen.getByLabelText(/Similarity flagged only/));
    expect(onFiltersChange).toHaveBeenLastCalledWith({ flagged: "true" });
  });

  it("shows an empty state when nothing matches", () => {
    render(<ResultsTable rows={[]} filters={{ q: "zzz" }} onFiltersChange={vi.fn()} />);
    expect(screen.getByText("No applications match these filters.")).toBeTruthy();
  });
});

describe("finding interaction", () => {
  it("groups findings by check and selects one", () => {
    const onSelect = vi.fn();
    const findings = [
      fx.finding(),
      fx.finding({ finding_id: "f-2", type: "duplication", status: "REVIEW_REQUIRED", signal: "POSSIBLE_DUPLICATION", title: "Duplication signal" }),
    ];
    render(<FindingList findings={findings} selectedId="f-2" onSelect={onSelect} />);
    expect(screen.getByRole("region", { name: "Eligibility" })).toBeTruthy();
    const dup = screen.getByTestId("finding-f-2");
    expect(dup.getAttribute("aria-pressed")).toBe("true");
    expect(within(dup).getByLabelText("Signal: Possible duplication")).toBeTruthy();
    fireEvent.click(screen.getByTestId("finding-f-1"));
    expect(onSelect).toHaveBeenCalledWith(findings[0]);
  });
});

describe("evidence drawer", () => {
  const baseProps = { documentNames: { "doc-1": "proposal.txt" }, onClose: vi.fn(), onShowInDocument: vi.fn(), onDecide: vi.fn(noop), onNote: vi.fn(noop) };

  it("separates AI signal, evidence and human decision, and links evidence to the document", () => {
    render(<EvidenceDrawer detail={fx.findingDetail()} canDecide {...baseProps} />);
    expect(screen.getByText("AI signal")).toBeTruthy();
    expect(screen.getByText("Evidence (1)")).toBeTruthy();
    expect(screen.getByText("Human decision")).toBeTruthy();
    expect(screen.getByLabelText("Citation verified against extracted text")).toBeTruthy();
    expect(screen.getByText("proposal.txt · p.1 · Budget")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Show in document/ }));
    expect(baseProps.onShowInDocument).toHaveBeenCalledWith(fx.evidence());
  });

  it("states uncertainty when no application passage supports the finding", () => {
    const detail = fx.findingDetail({ status: "REVIEW_REQUIRED", confidence: null, evidence: [fx.evidence({ source_type: "rfp", document_id: null, citation_valid: null })] });
    render(<EvidenceDrawer detail={detail} canDecide={false} {...baseProps} />);
    expect(screen.getByText(/No passage from this application could be cited/)).toBeTruthy();
    expect(screen.getByText("confidence not computed")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Show in document/ })).toBeNull();
    expect(screen.getByText(/Only a Reviewer or Grant Administrator/)).toBeTruthy();
  });

  it("shows compared records and prior decisions", () => {
    const detail = fx.findingDetail({
      type: "duplication", status: "REVIEW_REQUIRED", signal: "POSSIBLE_DUPLICATION", evidence: [],
      matches: [{ match_id: "m-1", source_type: "historical_application", record_id: "HIST-2024-118", application_id: null, document_id: null,
        title: "Historical drought project", similarity_score: 0.81, lexical_score: 0.4, semantic_score: null, reranker_score: 0.7,
        matched_section: "objectives", matched_passage: "community drought early warning", matching_concepts: ["drought", "early warning"],
        explanation: "Similar objectives; this does not establish duplication.", method: "hybrid", data_origin: "SYNTHETIC" }],
    });
    detail.decisions = [{ id: "d-1", finding_id: "f-1", action: "REQUEST_REVIEW", reviewer_id: "demo-reviewer", reviewer_role: "REVIEWER",
      note: "Check with programme officer", previous_state: "PENDING", new_state: "REVIEW_REQUESTED", created_at: "2026-09-30T10:00:00Z" }];
    render(<EvidenceDrawer detail={detail} canDecide {...baseProps} />);
    expect(screen.getByText("Compared records (1)")).toBeTruthy();
    expect(screen.getByText("Historical drought project")).toBeTruthy();
    expect(screen.getByText("early warning")).toBeTruthy();
    expect(screen.getByText(/Check with programme officer/)).toBeTruthy();
  });
});

describe("reviewer decision", () => {
  it("requires a rationale", async () => {
    const onDecide = vi.fn(noop);
    render(<DecisionPanel canDecide onDecide={onDecide} onNote={vi.fn(noop)} />);
    fireEvent.click(screen.getByRole("button", { name: "Record decision" }));
    expect((await screen.findByRole("alert")).textContent).toContain("A rationale is required");
    expect(onDecide).not.toHaveBeenCalled();
  });

  it("records the chosen action with the note, or a note on its own", async () => {
    const onDecide = vi.fn(noop);
    const onNote = vi.fn(noop);
    render(<DecisionPanel canDecide onDecide={onDecide} onNote={onNote} />);
    fireEvent.click(screen.getByLabelText("Escalate"));
    fireEvent.change(screen.getByLabelText(/Rationale/), { target: { value: " Budget total contradicts annex " } });
    fireEvent.click(screen.getByRole("button", { name: "Record decision" }));
    await waitFor(() => expect(onDecide).toHaveBeenCalledWith("ESCALATE", "Budget total contradicts annex"));
    expect((await screen.findByRole("status")).textContent).toContain("Decision recorded: Escalate");
    fireEvent.change(screen.getByLabelText(/Rationale/), { target: { value: "Follow up next week" } });
    fireEvent.click(screen.getByRole("button", { name: "Add note only" }));
    await waitFor(() => expect(onNote).toHaveBeenCalledWith("Follow up next week"));
  });
});

describe("document viewer", () => {
  const content: DocumentContent = {
    document_id: "doc-1", filename: "proposal.txt", owner_type: "application", owner_id: "app-1", extraction_status: "success",
    pages: [{ page_number: 1, lines: ["Budget", "Total requested amount:", "RWF 65,000,000"], text: "Budget Total requested amount: RWF 65,000,000" }],
  };

  it("highlights cited evidence even when it spans several lines", () => {
    render(<DocumentViewer content={content} highlight={{ documentId: "doc-1", page: 1, text: "Total requested amount: RWF 65,000,000" }} />);
    const marks = screen.getAllByTestId("evidence-highlight").map((m) => m.textContent);
    expect(marks).toEqual(["Total requested amount:", "RWF 65,000,000"]);
  });

  it("does not highlight evidence from another document and reports unreadable files", () => {
    const { unmount } = render(<DocumentViewer content={content} highlight={{ documentId: "doc-2", page: 1, text: "Budget" }} />);
    expect(screen.queryByTestId("evidence-highlight")).toBeNull();
    unmount();
    render(<DocumentViewer content={{ ...content, extraction_status: "failed", pages: [] }} highlight={null} />);
    expect(screen.getByText("No readable text")).toBeTruthy();
  });
});

describe("status badges", () => {
  it("falls back to readable text for unknown statuses", () => {
    render(<StatusBadge status="SOMETHING_NEW" />);
    expect(screen.getByLabelText("Status: SOMETHING NEW")).toBeTruthy();
  });
});
