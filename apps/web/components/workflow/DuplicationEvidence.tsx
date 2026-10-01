"use client";

import type { DuplicationMatchType, Finding, SimilarityMatch } from "../../lib/types";
import { SyntheticBadge } from "./ui";

const MATCH_LABELS: Record<DuplicationMatchType, string> = {
  EXACT_DUPLICATE: "Exact content match",
  SUBSTANTIAL_SIMILARITY: "Substantial similarity",
  POSSIBLE_SIMILARITY: "Possible similarity",
  NO_SIGNIFICANT_SIMILARITY: "No significant similarity",
  NOT_ASSESSABLE: "Not assessable",
};

const SOURCE_LABELS: Record<string, string> = {
  same_call_application: "Another application in this call",
  historical_application: "Previously submitted proposal",
  funded_project: "Funded project",
};

function Classification({ value }: { value: unknown }) {
  if (typeof value !== "string" || !(value in MATCH_LABELS)) return null;
  const tone = value === "NO_SIGNIFICANT_SIMILARITY" ? "neutral" : "review";
  return <span className={`badge badge-${tone}`}>{MATCH_LABELS[value as DuplicationMatchType]}</span>;
}

function Match({ match, documentNames }: { match: SimilarityMatch; documentNames: Record<string, string> }) {
  const queryLocation = [match.query_document_id ? documentNames[match.query_document_id] : null, match.query_page ? `p.${match.query_page}` : null].filter(Boolean).join(" · ");
  const sourceLocation = [match.matched_section?.replace(/_/g, " "), match.matched_page ? `p.${match.matched_page}` : null].filter(Boolean).join(" · ");
  return (
    <li>
      <div className="evidence-meta">
        <b>{match.title ?? match.record_id}</b>
        <SyntheticBadge origin={match.data_origin} />
        <span>{SOURCE_LABELS[match.source_type] ?? match.source_type.replace(/_/g, " ")}</span>
      </div>
      <small>{[match.record_id, match.year, match.outcome].filter(Boolean).join(" · ")}</small>
      <p><Classification value={match.match_type} /></p>
      <small>
        Similarity score {match.similarity_score.toFixed(2)} / 1
        {match.lexical_score !== null && ` · lexical ${match.lexical_score.toFixed(2)}`}
        {match.semantic_score !== null && ` · semantic ${match.semantic_score.toFixed(2)}`}
        {match.reranker_score !== null && ` · reranker ${match.reranker_score.toFixed(2)}`}
      </small>
      {(match.query_coverage != null || match.source_coverage != null) && (
        <small>
          {match.query_coverage != null && `Proposal coverage: ${Math.round(match.query_coverage * 100)}%`}
          {match.query_coverage != null && match.source_coverage != null && " · "}
          {match.source_coverage != null && `Compared project coverage: ${Math.round(match.source_coverage * 100)}%`}
        </small>
      )}
      <p className="small">{match.explanation}</p>
      {match.matching_concepts.length > 0 && <p className="concepts">{match.matching_concepts.map((concept) => <span key={concept}>{concept}</span>)}</p>}
      <div className="duplication-passages">
        <div>
          <b className="small">Submitted proposal passage</b>
          {queryLocation && <small>{queryLocation}</small>}
          {match.query_passage ? <blockquote>{match.query_passage}</blockquote> : <p className="muted small">No matching proposal passage was recorded for this result.</p>}
        </div>
        <div>
          <b className="small">Compared project passage</b>
          {sourceLocation && <small>{sourceLocation}</small>}
          {match.matched_passage ? <blockquote>{match.matched_passage}</blockquote> : <p className="muted small">No matching project passage was recorded for this result.</p>}
        </div>
      </div>
    </li>
  );
}

export function DuplicationEvidence({
  finding,
  documentNames,
  additionalMatches = [],
}: {
  finding: Finding;
  documentNames: Record<string, string>;
  /** Duplication matches the text-similarity check also found, shown here rather than
   *  under plagiarism. Nothing is rescored; they are the same stored matches. */
  additionalMatches?: SimilarityMatch[];
}) {
  const matches = [...finding.matches, ...additionalMatches];
  const details = finding.details;
  const recordsSearched = typeof details.compared_records === "number" ? details.compared_records : null;
  const skippedRecords = typeof details.skipped_records === "number" ? details.skipped_records : 0;
  const flagged = typeof details.flagged === "number" ? details.flagged : null;
  const limitations = Array.isArray(details.limitations) ? details.limitations.filter((item): item is string => typeof item === "string") : [];
  return (
    <>
      <section className="drawer-section" aria-label="Duplication coverage">
        <h3>Duplication comparison</h3>
        <Classification value={details.match_type} />
        <p>{recordsSearched === null ? "The number of records searched was not recorded for this run." : `${recordsSearched} ${recordsSearched === 1 ? "record" : "records"} searched.`}</p>
        {flagged !== null && flagged > matches.length && <p className="small">Showing the {matches.length} strongest matches of {flagged} flagged records.</p>}
        {skippedRecords > 0 && <p className="small">{skippedRecords} {skippedRecords === 1 ? "record was" : "records were"} skipped because usable project content was unavailable.</p>}
        {details.coverage_complete === false && <p className="uncertainty">Comparison coverage is incomplete. Unreadable or unavailable sources cannot be ruled out as duplicates.</p>}
        {limitations.length > 0 && <ul className="history">{limitations.map((limitation, index) => <li key={index}>{limitation}</li>)}</ul>}
        <p className="muted small">Similarity scores rank content overlap on a scale from 0 to 1. They are not a probability of duplication. A reviewer must confirm whether the projects duplicate each other.</p>
      </section>
      {matches.length > 0 && (
        <section className="drawer-section">
          <h3>Compared records ({matches.length})</h3>
          <ul className="match-list">{matches.map((match) => <Match key={match.match_id} match={match} documentNames={documentNames} />)}</ul>
        </section>
      )}
    </>
  );
}
