import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { EvidenceDrawer } from "../components/workflow/EvidenceDrawer";
import type { SimilarityMatch } from "../lib/types";
import * as fx from "./fixtures";

const publishedMatch: SimilarityMatch = {
  match_id: "match-p1", source_type: "published_work", record_id: "W2000000001", application_id: null, document_id: null,
  title: "Solar irrigation scheduling for drought-prone hillside farms", similarity_score: 0.42, lexical_score: 0.55,
  semantic_score: null, reranker_score: null, matched_section: null,
  matched_passage: "We design solar-powered drip irrigation schedules for hillside farms facing recurrent drought.",
  matching_concepts: ["drip irrigation", "hillside farms"],
  authors: ["A Researcher", "B Co-author"], published_on: "2019-04-15", publisher: "Agricultural Water Management",
  doi: "10.1016/j.agwat.2019.04.001", source_url: "https://doi.org/10.1016/j.agwat.2019.04.001",
  explanation: "2 verbatim passage(s), longest 21 words, covering 18.0% of this proposal.",
  method: "word_shingle_8+content_phrase_overlap", data_origin: "PROVIDER",
  query_passage: "The project designs solar-powered drip irrigation schedules for hillside farms facing recurrent drought.",
  query_coverage: 0.18, source_coverage: 0.42, year: 2019, outcome: "Published",
};

const searchedDetails = {
  similarity_index: 42.0, verbatim_index: 18.0, paraphrase_index: 42.0, band: "HIGH_SIMILARITY",
  matched_sources: 1, compared_records: 37, published_works_compared: 24,
  published_literature_searched: true, coverage_complete: true,
};

const props = { documentNames: { "doc-1": "proposal.txt" }, canDecide: true, onClose: vi.fn(), onShowInDocument: vi.fn(), onDecide: vi.fn(), onNote: vi.fn() };

describe("plagiarism evidence", () => {
  it("shows the similarity percentage, its split and how many records were compared", () => {
    render(<EvidenceDrawer detail={fx.findingDetail({ type: "plagiarism", matches: [publishedMatch], details: searchedDetails })} {...props} />);
    const panel = screen.getByRole("region", { name: "Similarity index" });
    // the headline is the published-work overlap, taken from the match itself
    expect(within(panel).getByRole("img", { name: "Similarity index 42 percent, High similarity" })).toBeTruthy();
    const split = within(panel).getByRole("list", { name: "Similarity breakdown" });
    expect(within(split).getByText("18%").parentElement?.textContent).toContain("copied word for word");
    expect(within(split).getByText("42%").parentElement?.textContent).toContain("reworded content phrases");
    expect(within(split).getByText("1").parentElement?.textContent).toContain("published source");
    expect(within(panel).getByText("24 published works compared from OpenAlex.")).toBeTruthy();
  });

  it("shows only the index, the matched sources and the decision, so reviewers read three sections", () => {
    render(<EvidenceDrawer detail={fx.findingDetail({ type: "plagiarism", matches: [publishedMatch], details: searchedDetails })} {...props} />);
    expect(screen.queryByText("AI signal")).toBeNull();
    expect(screen.queryByText(/^Evidence \(/)).toBeNull();
    expect(screen.queryByText(/^Method:/)).toBeNull();
    expect(screen.queryByText(/Suggested next step/)).toBeNull();
    expect(screen.getByText("Published-literature similarity")).toBeTruthy();
    expect(screen.getByText("Where the text was found (1)")).toBeTruthy();
    expect(screen.getByText("Human decision")).toBeTruthy();
  });

  it("leaves matches against other submissions to the duplication check", () => {
    const sameCall: SimilarityMatch = {
      ...publishedMatch, match_id: "match-p2", source_type: "same_call_application",
      record_id: "app-7", application_id: "app-7", title: "APP-0010 · proposal.pdf",
      authors: [], published_on: null, publisher: null, doi: null, source_url: null,
    };
    render(<EvidenceDrawer detail={fx.findingDetail({ type: "plagiarism", matches: [sameCall, publishedMatch], details: searchedDetails })} {...props} />);
    const rows = screen.getAllByRole("listitem").filter((li) => li.className.includes("plagiarism-match"));
    expect(rows).toHaveLength(1);
    expect(within(rows[0]).getByText("Published work")).toBeTruthy();
    expect(screen.queryByText("APP-0010 · proposal.pdf")).toBeNull();
    expect(screen.getByText("Where the text was found (1)")).toBeTruthy();
  });

  it("keeps the AI signal and evidence sections for other finding types", () => {
    render(<EvidenceDrawer detail={fx.findingDetail({ type: "duplication", matches: [], details: { match_type: "NOT_ASSESSABLE", compared_records: 0 } })} {...props} />);
    expect(screen.getByText("AI signal")).toBeTruthy();
    expect(screen.getByText(/^Evidence \(/)).toBeTruthy();
  });

  it("reveals the source, its publication date and the copied text only after More details", () => {
    render(<EvidenceDrawer detail={fx.findingDetail({ type: "plagiarism", matches: [publishedMatch], details: searchedDetails })} {...props} />);
    expect(screen.getByText("Where the text was found (1)")).toBeTruthy();
    expect(screen.getByText(publishedMatch.title!)).toBeTruthy();
    expect(screen.queryByText("2019-04-15")).toBeNull();

    fireEvent.click(screen.getByTestId("plagiarism-details-match-p1"));
    expect(screen.getByText("2019-04-15")).toBeTruthy();
    expect(screen.getByText("A Researcher, B Co-author")).toBeTruthy();
    expect(screen.getByText("Agricultural Water Management")).toBeTruthy();
    expect(screen.getByText("10.1016/j.agwat.2019.04.001")).toBeTruthy();
    expect(screen.getByRole("link", { name: /Open the original/ }).getAttribute("href")).toBe(publishedMatch.source_url);
    expect(screen.getByText(publishedMatch.query_passage!)).toBeTruthy();
    expect(screen.getByText(publishedMatch.matched_passage!)).toBeTruthy();

    fireEvent.click(screen.getByTestId("plagiarism-details-match-p1"));
    expect(screen.queryByText("2019-04-15")).toBeNull();
  });

  it("says published literature was not searched instead of implying a clean result", () => {
    const detail = fx.findingDetail({
      type: "plagiarism", matches: [], details: {
        similarity_index: 0.0, verbatim_index: 0.0, paraphrase_index: 0.0, band: "LOW_SIMILARITY",
        matched_sources: 0, compared_records: 4, published_works_compared: 0,
        published_literature_searched: false, coverage_complete: false,
      },
    });
    render(<EvidenceDrawer detail={detail} {...props} />);
    const panel = screen.getByRole("region", { name: "Similarity index" });
    expect(within(panel).getByRole("img", { name: "Similarity index 0 percent, Low similarity" })).toBeTruthy();
    expect(within(panel).getByText(/Published literature was not searched/)).toBeTruthy();
    expect(within(panel).getByText(/OpenAlex is not configured/)).toBeTruthy();
    expect(screen.queryByText(/Where the text was found/)).toBeNull();
  });
});
