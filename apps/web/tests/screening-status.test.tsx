import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ScreeningPage from "../app/dashboard/screening/page";
import { ScreeningStatusDialog } from "../components/workflow/ScreeningStatusDialog";
import { WorkspaceContext, type WorkspaceValue } from "../components/workflow/WorkspaceContext";
import { createClient } from "../lib/api";
import * as fx from "./fixtures";

function context(overrides: Partial<WorkspaceValue> = {}): WorkspaceValue {
  return {
    role: "GRANT_ADMINISTRATOR", setRole: vi.fn(), client: createClient({ role: "GRANT_ADMINISTRATOR", userId: "admin" }),
    calls: [], callsState: "ready", callsError: null, callId: "call-1", setCallId: vi.fn(),
    call: fx.grantCall({ status: "REVIEW" }), refreshCalls: vi.fn(),
    ...overrides,
  };
}

const screened = fx.row({
  id: "app-1", application_reference: "APP-0006", title: "Plant disease detection",
  document_names: ["Ndinayo_Eric_Plagiarism_Detection_Test.pdf", "budget.pdf", "cv.pdf"],
  screening_status: "REVIEW_REQUIRED", eligibility: "REVIEW_REQUIRED", completeness: "FAIL",
  duplication: "POSSIBLE_DUPLICATION", text_similarity: "SHARED_PASSAGES_FOUND", novelty: "HIGH",
  total_findings: 12, reviewed_findings: 3, open_findings: 9, review_progress: "IN_PROGRESS",
  document_count: 4, unreadable_documents: 1,
});

describe("screening page", () => {
  it("lists the uploaded applications and drops the batch progress and stage glossary", async () => {
    const workspace = context();
    workspace.client.listApplications = vi.fn().mockResolvedValue([screened]);
    workspace.client.dashboard = vi.fn().mockResolvedValue(fx.summary());
    render(<WorkspaceContext.Provider value={workspace}><ScreeningPage /></WorkspaceContext.Provider>);

    // The row is labelled by the real uploaded file, not by the generated reference code.
    expect(await screen.findByText("Ndinayo_Eric_Plagiarism_Detection_Test.pdf")).toBeTruthy();
    expect(screen.getByText("APP-0006 · Plant disease detection · 2 more documents")).toBeTruthy();
    expect(screen.getByText("Document uploaded")).toBeTruthy();
    expect(screen.getByText("Launch screening")).toBeTruthy();
    expect(screen.queryByText("Latest batch")).toBeNull();
    expect(screen.queryByText("Pipeline stages")).toBeNull();
    expect(screen.queryByText("Document extraction")).toBeNull();
  });

  it("says what the screening produced instead of a bare REVIEW REQUIRED", async () => {
    const workspace = context();
    workspace.client.listApplications = vi.fn().mockResolvedValue([screened]);
    workspace.client.dashboard = vi.fn().mockResolvedValue(fx.summary());
    render(<WorkspaceContext.Provider value={workspace}><ScreeningPage /></WorkspaceContext.Provider>);

    await screen.findByText("Ndinayo_Eric_Plagiarism_Detection_Test.pdf");
    expect(screen.getByText("SCREENED · NEEDS REVIEW")).toBeTruthy();
    expect(screen.queryByText("REVIEW REQUIRED")).toBeNull();
  });

  it("opens the screening status popup from the status badge and closes it again", async () => {
    const workspace = context();
    workspace.client.listApplications = vi.fn().mockResolvedValue([screened]);
    workspace.client.dashboard = vi.fn().mockResolvedValue(fx.summary());
    render(<WorkspaceContext.Provider value={workspace}><ScreeningPage /></WorkspaceContext.Provider>);

    await screen.findByText("Ndinayo_Eric_Plagiarism_Detection_Test.pdf");
    expect(screen.queryByRole("dialog")).toBeNull();
    fireEvent.click(screen.getByTitle("Screening status for APP-0006"));

    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText("APP-0006 · Plant disease detection")).toBeTruthy();
    fireEvent.click(within(dialog).getByRole("button", { name: "Close screening status" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
  });
});

describe("screening status popup", () => {
  it("shows every check result and how far the reviewer has got", () => {
    render(<ScreeningStatusDialog row={screened} onClose={vi.fn()} />);
    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByRole("heading", { name: "Ndinayo_Eric_Plagiarism_Detection_Test.pdf" })).toBeTruthy();
    for (const file of ["Ndinayo_Eric_Plagiarism_Detection_Test.pdf", "budget.pdf", "cv.pdf"]) {
      expect(within(dialog).getAllByText(file).length).toBeGreaterThan(0);
    }
    expect(within(dialog).getByText("1 could not be read")).toBeTruthy();
    for (const check of ["Eligibility", "Completeness", "Duplication", "Plagiarism", "Novelty"]) {
      expect(within(dialog).getByText(check)).toBeTruthy();
    }
    expect(within(dialog).getByText("3 of 12").parentElement?.textContent).toContain("9 still open");
    expect(within(dialog).getByText("Review in progress")).toBeTruthy();
    expect(within(dialog).getByRole("link", { name: /Open full review/ }).getAttribute("href")).toBe(
      "/dashboard/applications/view?id=app-1",
    );
  });

  it("says an unscreened application has no result rather than showing empty checks", () => {
    const row = fx.row({ screening_status: "NOT_SCREENED", last_screened_at: null, total_findings: 0 });
    render(<ScreeningStatusDialog row={row} onClose={vi.fn()} />);
    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText(/has not been screened yet/)).toBeTruthy();
    expect(within(dialog).queryByText("Eligibility")).toBeNull();
    expect(within(dialog).queryByRole("link", { name: /Open full review/ })).toBeNull();
  });

  it("closes on Escape", () => {
    const onClose = vi.fn();
    render(<ScreeningStatusDialog row={screened} onClose={onClose} />);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });
});
