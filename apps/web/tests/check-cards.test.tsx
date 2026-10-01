import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CheckResultCards } from "../components/workflow/CheckResultCards";
import { DecisionModal } from "../components/workflow/DecisionModal";
import { EvidenceModal } from "../components/workflow/EvidenceModal";
import { WorkspaceContext, type WorkspaceValue } from "../components/workflow/WorkspaceContext";
import { ApiError, createClient } from "../lib/api";
import type { Finding, SimilarityMatch } from "../lib/types";
import * as fx from "./fixtures";

function eligibility(code: string, status: Finding["status"]): Finding {
  return fx.finding({
    finding_id: `e-${code}`, type: "eligibility", status,
    title: `${code} - Addresses a thematic priority`,
    explanation: "None of the expected terms were found.",
  });
}

function match(over: Partial<SimilarityMatch>): SimilarityMatch {
  return {
    match_id: "m", source_type: "same_call_application", record_id: "r", application_id: null,
    document_id: null, title: "t", similarity_score: 1, lexical_score: null, semantic_score: null,
    reranker_score: null, matched_section: null, matched_passage: null, matching_concepts: [],
    explanation: "", method: "m", data_origin: "UPLOADED", ...over,
  };
}

const findings: Finding[] = [
  eligibility("R01", "REVIEW_REQUIRED"),
  eligibility("R02", "REVIEW_REQUIRED"),
  eligibility("R03", "PASS"),
  eligibility("R04", "REVIEW_REQUIRED"),
  eligibility("R05", "REVIEW_REQUIRED"),
  eligibility("R06", "REVIEW_REQUIRED"),
  fx.finding({
    finding_id: "d-1", type: "duplication", status: "REVIEW_REQUIRED", signal: "POSSIBLE_DUPLICATION",
    title: "Proposal duplication check", explanation: "10 of 18 compared records need duplication review.",
    details: { compared_records: 25 },
    matches: [
      match({ match_id: "dm-1", application_id: "app-13", record_id: "APP-0013", title: "APP-0013" }),
      match({ match_id: "dm-2", application_id: "app-4", record_id: "APP-0004", title: "APP-0004" }),
    ],
  }),
  fx.finding({
    finding_id: "p-1", type: "plagiarism", status: "REVIEW_REQUIRED", signal: "SHARED_PASSAGES_FOUND",
    title: "Plagiarism check", explanation: "Similarity index 100.0% of this proposal's text matches 5 sources.",
    details: {
      similarity_index: 100, band: "HIGH_SIMILARITY", published_works_compared: 24,
      published_literature_searched: true,
    },
    matches: [
      // duplicates of other submissions: a duplication question, not plagiarism
      match({ match_id: "pm-1", application_id: "app-13", record_id: "APP-0013", title: "APP-0013" }),
      match({ match_id: "pm-2", application_id: "app-5", record_id: "APP-0005", title: "APP-0005" }),
      match({ match_id: "pm-3", application_id: "app-6", record_id: "APP-0006", title: "APP-0006" }),
      // the only genuine published-literature match
      match({
        match_id: "pm-4", source_type: "published_work", record_id: "W1", application_id: null,
        title: "Exploring factors associated with research involvement",
        similarity_score: 0.352, query_coverage: 0.301, source_coverage: 0.352,
        published_on: "2021-04-26",
      }),
    ],
  }),
];

describe("research check result cards", () => {
  it("shows the three checks side by side with values read from the findings", () => {
    render(<CheckResultCards findings={findings} onOpenEvidence={vi.fn()} />);

    const elig = within(screen.getByRole("region", { name: "Eligibility" }));
    expect(elig.getByText("1 / 6")).toBeTruthy();
    expect(elig.getByText("PARTIAL")).toBeTruthy();

    // APP-0013 is matched by both checks; it counts once, and APP-0005/0006 are
    // duplicates the text-similarity check found, so they belong here too.
    const dup = within(screen.getByRole("region", { name: "Duplication" }));
    expect(dup.getByText("4")).toBeTruthy();
    expect(dup.getByText("4 matching submissions of 25 records compared")).toBeTruthy();

    // the headline is the published-work overlap, not the 100% that included duplicates
    const plag = within(screen.getByRole("region", { name: "Plagiarism" }));
    expect(plag.getByText("35.2")).toBeTruthy();
    expect(plag.getByText("%")).toBeTruthy();
    expect(plag.getByText("1 published source of 24 compared")).toBeTruthy();
  });

  it("derives the eligibility ratio from the findings rather than a fixed value", () => {
    render(<CheckResultCards findings={findings.filter((f) => f.type !== "eligibility").concat([
      eligibility("R01", "PASS"), eligibility("R02", "PASS"), eligibility("R03", "FAIL"),
    ])} onOpenEvidence={vi.fn()} />);
    const elig = within(screen.getByRole("region", { name: "Eligibility" }));
    expect(elig.getByText("2 / 3")).toBeTruthy();
  });

  it("colours the plagiarism card by the band the check reported", () => {
    const { container, unmount } = render(<CheckResultCards findings={findings} onOpenEvidence={vi.fn()} />);
    expect(container.querySelector(".check-card.tone-fail")).toBeTruthy();
    unmount();

    const low = findings.map((f) => f.type === "plagiarism"
      ? { ...f, details: { ...f.details, band: "LOW_SIMILARITY" } } : f);
    const second = render(<CheckResultCards findings={low} onOpenEvidence={vi.fn()} />);
    const plag = within(screen.getByRole("region", { name: "Plagiarism" }));
    expect(plag.getByText("35.2")).toBeTruthy();
    expect(second.container.querySelector(".check-card.tone-fail")).toBeNull();
  });

  it("says a check has no result instead of inventing a number", () => {
    render(<CheckResultCards findings={[]} onOpenEvidence={vi.fn()} />);
    for (const name of ["Eligibility", "Duplication", "Plagiarism"]) {
      const card = within(screen.getByRole("region", { name }));
      expect(card.getByText("—")).toBeTruthy();
      expect(card.getByText("No result for this check.")).toBeTruthy();
    }
  });

  it("asks for a popup instead of navigating away from the page", () => {
    const onOpenEvidence = vi.fn();
    render(<CheckResultCards findings={findings} onOpenEvidence={onOpenEvidence} />);

    const plag = within(screen.getByRole("region", { name: "Plagiarism" }));
    const view = plag.getByRole("button", { name: /View evidence/ });
    expect(view.getAttribute("aria-haspopup")).toBe("dialog");
    fireEvent.click(view);
    expect(onOpenEvidence).toHaveBeenCalledWith(findings.filter((f) => f.type === "plagiarism"));

    // eligibility hands the popup every requirement, so none is unreachable
    const elig = within(screen.getByRole("region", { name: "Eligibility" }));
    fireEvent.click(elig.getByRole("button", { name: /View evidence/ }));
    expect(onOpenEvidence).toHaveBeenLastCalledWith(findings.filter((f) => f.type === "eligibility"));

    expect(screen.queryAllByRole("link")).toHaveLength(0);
  });

  it("shows only the score and a short summary, with the detail left to the popup", () => {
    render(<CheckResultCards findings={findings} onOpenEvidence={vi.fn()} />);
    const elig = within(screen.getByRole("region", { name: "Eligibility" }));
    expect(elig.getByText("1 of 6 requirements met, 5 to review")).toBeTruthy();
    // the per-requirement rows and their descriptions are no longer on the card
    expect(elig.queryByText(/R01 - Addresses a thematic priority/)).toBeNull();
    expect(elig.queryByText(/None of the expected terms were found/)).toBeNull();

    const dup = within(screen.getByRole("region", { name: "Duplication" }));
    expect(dup.queryByText(/compared records need duplication review/)).toBeNull();
    expect(dup.queryByText(/Compared with:/)).toBeNull();
  });

  it("keeps duplicated submissions out of the plagiarism figure", () => {
    const noPublished = findings.map((f) => f.type === "plagiarism"
      ? { ...f, matches: f.matches.filter((m) => m.source_type !== "published_work") } : f);
    render(<CheckResultCards findings={noPublished} onOpenEvidence={vi.fn()} />);

    const plag = within(screen.getByRole("region", { name: "Plagiarism" }));
    expect(plag.getByText("0.0")).toBeTruthy();
    expect(plag.getByText("No published work matched of 24 compared")).toBeTruthy();

    // the same submissions are still counted as duplication
    const dup = within(screen.getByRole("region", { name: "Duplication" }));
    expect(dup.getByText("4")).toBeTruthy();
  });
});

describe("evidence popup", () => {
  function context(getFinding: ReturnType<typeof vi.fn>): WorkspaceValue {
    const client = createClient({ role: "GRANT_ADMINISTRATOR", userId: "admin" });
    client.getFinding = getFinding;
    return {
      role: "GRANT_ADMINISTRATOR", setRole: vi.fn(), client,
      calls: [], callsState: "ready", callsError: null, callId: "call-1", setCallId: vi.fn(),
      call: fx.grantCall(), refreshCalls: vi.fn(),
    };
  }

  it("loads the finding and shows its evidence without leaving the page", async () => {
    const detail = fx.findingDetail({
      type: "eligibility", status: "REVIEW_REQUIRED", title: "R04 - Geographic eligibility: Rwanda",
    });
    const getFinding = vi.fn().mockResolvedValue(detail);
    render(
      <WorkspaceContext.Provider value={context(getFinding)}>
        <EvidenceModal findings={[eligibility("R04", "REVIEW_REQUIRED")]} onClose={vi.fn()} />
      </WorkspaceContext.Provider>,
    );
    expect(await screen.findByRole("dialog")).toBeTruthy();
    expect(getFinding).toHaveBeenCalledWith("e-R04");
    const dialog = within(screen.getByRole("dialog"));
    expect(await dialog.findByText("R04 - Geographic eligibility: Rwanda")).toBeTruthy();
    expect(dialog.getByText("AI signal")).toBeTruthy();
    expect(dialog.getByText(detail.finding.evidence[0].text)).toBeTruthy();
    // evidence only: the decision lives in its own popup
    expect(dialog.queryByRole("button", { name: "Record decision" })).toBeNull();
  });

  it("closes on the close button and on Escape", async () => {
    const onClose = vi.fn();
    const getFinding = vi.fn().mockResolvedValue(fx.findingDetail());
    const { unmount } = render(
      <WorkspaceContext.Provider value={context(getFinding)}>
        <EvidenceModal findings={findings} onClose={onClose} />
      </WorkspaceContext.Provider>,
    );
    fireEvent.click(await screen.findByRole("button", { name: "Close evidence" }));
    expect(onClose).toHaveBeenCalled();
    unmount();

    const onClose2 = vi.fn();
    render(
      <WorkspaceContext.Provider value={context(getFinding)}>
        <EvidenceModal findings={findings} onClose={onClose2} />
      </WorkspaceContext.Provider>,
    );
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose2).toHaveBeenCalled();
  });

  it("reports a load failure instead of showing an empty popup", async () => {
    const getFinding = vi.fn().mockRejectedValue(new ApiError(503, "The API is unreachable"));
    render(
      <WorkspaceContext.Provider value={context(getFinding)}>
        <EvidenceModal findings={findings} onClose={vi.fn()} />
      </WorkspaceContext.Provider>,
    );
    expect(await screen.findByText("Could not load evidence")).toBeTruthy();
    expect(screen.getByText("The API is unreachable")).toBeTruthy();
  });
});

describe("human decision popup", () => {
  function workspace(): WorkspaceValue {
    const client = createClient({ role: "GRANT_ADMINISTRATOR", userId: "admin" });
    client.decide = vi.fn().mockResolvedValue({});
    return {
      role: "GRANT_ADMINISTRATOR", setRole: vi.fn(), client,
      calls: [], callsState: "ready", callsError: null, callId: "call-1", setCallId: vi.fn(),
      call: fx.grantCall(), refreshCalls: vi.fn(),
    };
  }

  it("lets the reviewer pick the check and records the decision against it", async () => {
    const ws = workspace();
    const onRecorded = vi.fn();
    render(
      <WorkspaceContext.Provider value={ws}>
        <DecisionModal findings={findings} onClose={vi.fn()} onRecorded={onRecorded} />
      </WorkspaceContext.Provider>,
    );
    const dialog = within(screen.getByRole("dialog", { name: "Human decision" }));
    // only the decision itself: no check picker, no evidence, no extra sections
    expect(dialog.queryByText("Which check")).toBeNull();
    expect(dialog.getByText(`Decision on ${findings[0].title}`)).toBeTruthy();
    expect(dialog.getByText("Awaiting reviewer")).toBeTruthy();

    fireEvent.click(dialog.getByLabelText("Confirm finding"));
    fireEvent.change(dialog.getByLabelText(/Rationale/), { target: { value: "Checked the cited page." } });
    fireEvent.click(dialog.getByRole("button", { name: "Record decision" }));

    await waitFor(() =>
      expect(ws.client.decide).toHaveBeenCalledWith(findings[0].finding_id, "CONFIRM", "Checked the cited page."),
    );
    await waitFor(() => expect(onRecorded).toHaveBeenCalled());
  });

  it("moves to the next finding still awaiting a reviewer", () => {
    const decided = findings.map((f, i) => (i === 0 ? { ...f, review_state: "CONFIRMED" as const } : f));
    render(
      <WorkspaceContext.Provider value={workspace()}>
        <DecisionModal findings={decided} onClose={vi.fn()} onRecorded={vi.fn()} />
      </WorkspaceContext.Provider>,
    );
    expect(screen.getByText(`Decision on ${decided[1].title}`)).toBeTruthy();
  });

  it("offers only confirm and dismiss, and closes on Escape", () => {
    const onClose = vi.fn();
    render(
      <WorkspaceContext.Provider value={workspace()}>
        <DecisionModal findings={findings} onClose={onClose} onRecorded={vi.fn()} />
      </WorkspaceContext.Provider>,
    );
    expect(screen.getByLabelText("Confirm finding")).toBeTruthy();
    expect(screen.getByLabelText("Dismiss finding")).toBeTruthy();
    expect(screen.queryByLabelText("Escalate")).toBeNull();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });

  it("says so when there is no finding to decide on", () => {
    render(
      <WorkspaceContext.Provider value={workspace()}>
        <DecisionModal findings={[]} onClose={vi.fn()} onRecorded={vi.fn()} />
      </WorkspaceContext.Provider>,
    );
    expect(screen.getByText("There is no finding to decide on for this document.")).toBeTruthy();
  });
});

describe("evidence popup with several findings", () => {
  it("lets the reviewer switch between the requirements behind the eligibility card", async () => {
    const eligibilityFindings = findings.filter((f) => f.type === "eligibility");
    const getFinding = vi.fn().mockImplementation(async (id: string) =>
      fx.findingDetail({ finding_id: id, type: "eligibility", title: `Detail for ${id}` }),
    );
    const client = createClient({ role: "GRANT_ADMINISTRATOR", userId: "admin" });
    client.getFinding = getFinding;
    render(
      <WorkspaceContext.Provider value={{
        role: "GRANT_ADMINISTRATOR", setRole: vi.fn(), client,
        calls: [], callsState: "ready", callsError: null, callId: "call-1", setCallId: vi.fn(),
        call: fx.grantCall(), refreshCalls: vi.fn(),
      }}>
        <EvidenceModal findings={eligibilityFindings} onClose={vi.fn()} />
      </WorkspaceContext.Provider>,
    );
    expect(await screen.findByRole("tablist", { name: "Findings" })).toBeTruthy();
    expect(getFinding).toHaveBeenCalledWith("e-R01");

    fireEvent.click(screen.getByRole("tab", { name: eligibilityFindings[3].title }));
    await waitFor(() => expect(getFinding).toHaveBeenCalledWith("e-R04"));
  });
});

describe("stale grant call recovery", () => {
  it("replaces a stored call that no longer exists and persists the correction", async () => {
    const { WorkspaceProvider, useWorkspace } = await import("../components/workflow/WorkspaceContext");
    window.localStorage.setItem("ai-screening.call", "call_gone");
    const live = fx.grantCall({ id: "call_live" });
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify([live]), { status: 200, headers: { "content-type": "application/json" } }),
    );

    function Probe() {
      const { callId, callsState } = useWorkspace();
      return <span data-testid="probe">{callsState}:{callId ?? "none"}</span>;
    }
    render(<WorkspaceProvider><Probe /></WorkspaceProvider>);

    await waitFor(() => expect(screen.getByTestId("probe").textContent).toBe("ready:call_live"));
    expect(window.localStorage.getItem("ai-screening.call")).toBe("call_live");
    vi.restoreAllMocks();
    window.localStorage.clear();
  });
});
