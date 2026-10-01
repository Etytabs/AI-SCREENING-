import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import DuplicationPage from "../app/dashboard/duplication/page";
import { DuplicationProjectImport } from "../components/workflow/DuplicationProjectImport";
import { EvidenceDrawer } from "../components/workflow/EvidenceDrawer";
import { WorkspaceContext, type WorkspaceValue } from "../components/workflow/WorkspaceContext";
import type { ArchivedProject, SimilarityMatch } from "../lib/types";
import { createClient } from "../lib/api";
import * as fx from "./fixtures";

const project: ArchivedProject = {
  id: "project-1", title: "Drought sensor network", source_type: "funded_project", reference: "FUND-2024-7",
  year: 2024, organization: "Research Council", filename: "funded-project.txt", text_length: 560,
  created_at: "2026-09-30T10:00:00Z", data_origin: "UPLOADED", application_id: null, grant_call_id: null,
};

function context(overrides: Partial<WorkspaceValue> = {}): WorkspaceValue {
  return {
    role: "GRANT_ADMINISTRATOR", setRole: vi.fn(), client: createClient({ role: "GRANT_ADMINISTRATOR", userId: "admin" }),
    calls: [], callsState: "ready", callsError: null, callId: null, setCallId: vi.fn(), call: null, refreshCalls: vi.fn(),
    ...overrides,
  };
}

describe("duplication project import", () => {
  it("imports the document and metadata, clears the form and explains how to update existing results", async () => {
    const onImport = vi.fn().mockResolvedValue(project);
    const onImported = vi.fn();
    render(<DuplicationProjectImport onImport={onImport} onImported={onImported} />);
    const file = new File(["Project objectives: build a drought sensor network."], "funded-project.txt", { type: "text/plain" });
    fireEvent.change(screen.getByLabelText("Previous project document"), { target: { files: [file] } });
    fireEvent.change(screen.getByLabelText("Project title *"), { target: { value: " Drought sensor network " } });
    fireEvent.change(screen.getByLabelText("Project source"), { target: { value: "funded_project" } });
    fireEvent.change(screen.getByLabelText("Project reference"), { target: { value: " FUND-2024-7 " } });
    fireEvent.change(screen.getByLabelText("Year"), { target: { value: "2024" } });
    fireEvent.change(screen.getByLabelText("Organization"), { target: { value: " Research Council " } });
    fireEvent.submit(screen.getByRole("form", { name: "Import comparison project" }));
    await waitFor(() => expect(onImported).toHaveBeenCalledWith(project));
    expect(onImport).toHaveBeenCalledWith({ file, title: project.title, source_type: "funded_project", reference: "FUND-2024-7", year: 2024, organization: "Research Council" });
    expect(screen.getByText("Project added to the comparison library")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Run screening again" }).getAttribute("href")).toBe("/dashboard/screening");
    expect((screen.getByLabelText("Project title *") as HTMLInputElement).value).toBe("");
    expect(screen.queryByText("Selected:")).toBeNull();
  });

  it("rejects unsupported files before importing and shows duplicate errors without claiming success", async () => {
    const onImport = vi.fn().mockRejectedValue(new Error("This content already exists as Drought sensor network."));
    render(<DuplicationProjectImport onImport={onImport} onImported={vi.fn()} />);
    fireEvent.change(screen.getByLabelText("Previous project document"), { target: { files: [new File(["not a document"], "archive.exe")] } });
    expect(screen.getByRole("alert").textContent).toContain("Use a PDF, DOCX or TXT");
    expect(onImport).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText("Project title *"), { target: { value: "Drought sensor network" } });
    fireEvent.change(screen.getByLabelText("Previous project document"), { target: { files: [new File(["Objectives"], "project.txt")] } });
    fireEvent.submit(screen.getByRole("form", { name: "Import comparison project" }));
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("already exists"));
    expect(screen.queryByText("Project added to the comparison library")).toBeNull();
    expect(screen.getByText("project.txt")).toBeTruthy();
  });
});

describe("duplication comparison library", () => {
  it("loads without a selected call, filters records, and prevents reviewers importing projects", async () => {
    const workspace = context({ role: "REVIEWER" });
    workspace.client.listDuplicationProjects = vi.fn().mockResolvedValue([project]);
    render(<WorkspaceContext.Provider value={workspace}><DuplicationPage /></WorkspaceContext.Provider>);
    expect(await screen.findByText("Drought sensor network")).toBeTruthy();
    expect(screen.getByText("Read-only library")).toBeTruthy();
    expect(screen.queryByRole("form", { name: "Import comparison project" })).toBeNull();
    fireEvent.change(screen.getByLabelText("Filter project source"), { target: { value: "historical_application" } });
    expect(screen.getByText("No projects match these filters.")).toBeTruthy();
  });

  it("surfaces a failed library load and retries it", async () => {
    const workspace = context();
    workspace.client.listDuplicationProjects = vi.fn().mockRejectedValueOnce(new Error("The API is unreachable")).mockResolvedValueOnce([]);
    render(<WorkspaceContext.Provider value={workspace}><DuplicationPage /></WorkspaceContext.Provider>);
    expect((await screen.findByRole("alert")).textContent).toContain("The API is unreachable");
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByText("No historical projects imported")).toBeTruthy();
  });
});

describe("duplication evidence", () => {
  const match: SimilarityMatch = {
    match_id: "match-1", source_type: "funded_project", record_id: "FUND-2024-7", application_id: null, document_id: "historical-doc",
    title: "Drought sensor network", similarity_score: 0.86, lexical_score: 0.79, semantic_score: null, reranker_score: null,
    matched_section: "objectives", matched_passage: "Install soil sensors across the funded trial sites.", matching_concepts: ["soil sensors"],
    explanation: "Both projects describe the same field trial and intervention.", method: "project_overlap", data_origin: "UPLOADED",
    match_type: "SUBSTANTIAL_SIMILARITY", query_passage: "We will install soil sensors across the trial sites.", query_page: 2,
    query_document_id: "doc-1", matched_page: 4, query_coverage: 0.82, source_coverage: 0.79, year: 2024, outcome: "funded",
  };
  const props = { documentNames: { "doc-1": "proposal.txt" }, canDecide: true, onClose: vi.fn(), onShowInDocument: vi.fn(), onDecide: vi.fn(), onNote: vi.fn() };

  it("shows classification, source, both passages, scores and incomplete comparison coverage", () => {
    const detail = fx.findingDetail({ type: "duplication", matches: [match], details: { match_type: "SUBSTANTIAL_SIMILARITY", compared_records: 14, skipped_records: 2, coverage_complete: false, limitations: ["The funded project register was unavailable."], flagged: 6 } });
    render(<EvidenceDrawer detail={detail} {...props} />);
    const coverage = screen.getByRole("region", { name: "Duplication coverage" });
    expect(within(coverage).getByText("Substantial similarity")).toBeTruthy();
    expect(within(coverage).getByText("14 records searched.")).toBeTruthy();
    expect(screen.getByText("Showing the 1 strongest matches of 6 flagged records.")).toBeTruthy();
    expect(screen.getByText(/Comparison coverage is incomplete/)).toBeTruthy();
    expect(screen.getByText("The funded project register was unavailable.")).toBeTruthy();
    expect(screen.getByText(/not a probability of duplication/)).toBeTruthy();
    expect(screen.getByText("Funded project")).toBeTruthy();
    expect(screen.getByText(match.query_passage!)).toBeTruthy();
    expect(screen.getByText(match.matched_passage!)).toBeTruthy();
    expect(screen.getByText("proposal.txt · p.2")).toBeTruthy();
    expect(screen.getByText("objectives · p.4")).toBeTruthy();
    expect(screen.queryByText(/^confidence /)).toBeNull();
    expect(screen.getByText("Human decision")).toBeTruthy();
  });

  it("shows zero comparisons and not assessable rather than hiding empty coverage", () => {
    render(<EvidenceDrawer detail={fx.findingDetail({ type: "duplication", matches: [], details: { match_type: "NOT_ASSESSABLE", compared_records: 0, coverage_complete: false } })} {...props} />);
    expect(screen.getByText("0 records searched.")).toBeTruthy();
    expect(screen.getByText("Not assessable")).toBeTruthy();
    expect(screen.queryByText("Compared records (0)")).toBeNull();
  });
});
