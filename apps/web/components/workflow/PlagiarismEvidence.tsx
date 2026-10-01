"use client";

import { useState } from "react";

import { isPublishedMatch } from "../../lib/matches";
import type { Finding, SimilarityMatch } from "../../lib/types";
import { SyntheticBadge } from "./ui";

const BAND_LABELS: Record<string, string> = {
  LOW_SIMILARITY: "Low similarity",
  MODERATE_SIMILARITY: "Moderate similarity",
  HIGH_SIMILARITY: "High similarity",
};

const SOURCE_LABELS: Record<string, string> = {
  published_work: "Published work",
  same_call_application: "Another application in this call",
  historical_application: "Previously submitted proposal",
  funded_project: "Funded project",
};

// Which concern a match belongs to: text shared with a peer application is a duplication
// question, text shared with something already published is a plagiarism question.
const SOURCE_FLAGS: Record<string, string> = {
  same_call_application: "Duplication",
  published_work: "Plagiarism",
};

function num(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function pct(value: number | null | undefined): string {
  return `${Math.round(num(value) * 1000) / 10}%`;
}

/** Percentage dial: the headline number a reviewer reads first. */
function SimilarityDial({ index, band }: { index: number; band: string }) {
  const tone = band === "HIGH_SIMILARITY" ? "high" : band === "MODERATE_SIMILARITY" ? "moderate" : "low";
  return (
    <div className={`similarity-dial dial-${tone}`} role="img" aria-label={`Similarity index ${index} percent, ${BAND_LABELS[band] ?? band}`}>
      <strong>{index}%</strong>
      <span>{BAND_LABELS[band] ?? "Similarity index"}</span>
      <div className="similarity-bar"><i style={{ width: `${Math.min(100, Math.max(index, 1))}%` }} /></div>
    </div>
  );
}

function SourceMeta({ match }: { match: SimilarityMatch }) {
  const authors = match.authors ?? [];
  const byline = authors.length > 3 ? `${authors.slice(0, 3).join(", ")} and ${authors.length - 3} more` : authors.join(", ");
  return (
    <dl className="plagiarism-meta">
      {byline && (<><dt>Authors</dt><dd>{byline}</dd></>)}
      {match.published_on && (<><dt>Published</dt><dd>{match.published_on}</dd></>)}
      {!match.published_on && match.year != null && (<><dt>Published</dt><dd>{match.year}</dd></>)}
      {match.publisher && (<><dt>Published in</dt><dd>{match.publisher}</dd></>)}
      {match.doi && (<><dt>DOI</dt><dd>{match.doi}</dd></>)}
      <dt>Record</dt><dd>{match.record_id}</dd>
      {match.source_url && (
        <>
          <dt>Source</dt>
          <dd><a href={match.source_url} target="_blank" rel="noreferrer noopener">Open the original ↗</a></dd>
        </>
      )}
    </dl>
  );
}

function MatchRow({ match }: { match: SimilarityMatch }) {
  const [open, setOpen] = useState(false);
  const verbatim = num(match.query_coverage);
  const reworded = num(match.source_coverage);
  return (
    <li className="plagiarism-match">
      <div className="evidence-meta">
        <b>{match.title ?? match.record_id}</b>
        <SyntheticBadge origin={match.data_origin} />
        <span>{SOURCE_LABELS[match.source_type] ?? match.source_type.replace(/_/g, " ")}</span>
        {SOURCE_FLAGS[match.source_type] && <span className="dup-flag">[{SOURCE_FLAGS[match.source_type]}]</span>}
      </div>
      <small>
        {pct(match.similarity_score)} of this proposal · {pct(verbatim)} word-for-word · {pct(reworded)} reworded
        {match.published_on ? ` · published ${match.published_on}` : match.year != null ? ` · ${match.year}` : ""}
      </small>
      <div className="similarity-bar small-bar"><i style={{ width: `${Math.min(100, Math.max(num(match.similarity_score) * 100, 1))}%` }} /></div>
      <button className="text-button" aria-expanded={open} onClick={() => setOpen(!open)} data-testid={`plagiarism-details-${match.match_id}`}>
        {open ? "Hide details" : "More details"}
      </button>
      {open && (
        <div className="plagiarism-detail">
          <SourceMeta match={match} />
          <p className="small">{match.explanation}</p>
          {(match.matching_concepts?.length ?? 0) > 0 && (
            <p className="concepts">{match.matching_concepts.map((concept) => <span key={concept}>{concept}</span>)}</p>
          )}
          <div className="duplication-passages">
            <div>
              <b className="small">Text in this proposal</b>
              {match.query_passage ? <blockquote>{match.query_passage}</blockquote> : <p className="muted small">No proposal passage was recorded for this match.</p>}
            </div>
            <div>
              <b className="small">Matching text in the source</b>
              {match.matched_passage ? <blockquote>{match.matched_passage}</blockquote> : <p className="muted small">No source passage was recorded for this match.</p>}
            </div>
          </div>
        </div>
      )}
    </li>
  );
}

export function PlagiarismEvidence({ finding }: { finding: Finding }) {
  const details = finding.details;
  const band = typeof details.band === "string" ? details.band : "LOW_SIMILARITY";
  const works = num(details.published_works_compared);
  const searchedLiterature = details.published_literature_searched === true;

  // Published literature only. Overlap with other submissions in this call is a
  // duplication question and is reported by the duplication check instead.
  const matches = finding.matches.filter(isPublishedMatch);
  const top = matches.reduce<SimilarityMatch | null>(
    (best, match) => (best === null || match.similarity_score > best.similarity_score ? match : best),
    null,
  );
  const index = top ? top.similarity_score * 100 : 0;

  return (
    <>
      <section className="drawer-section" aria-label="Similarity index">
        <h3>Published-literature similarity</h3>
        <SimilarityDial index={Math.round(index * 10) / 10} band={top ? band : "LOW_SIMILARITY"} />
        <ul className="similarity-split" aria-label="Similarity breakdown">
          <li><b>{pct(top?.query_coverage)}</b><span>copied word for word</span></li>
          <li><b>{pct(top?.source_coverage)}</b><span>reworded content phrases</span></li>
          <li><b>{matches.length}</b><span>published source{matches.length === 1 ? "" : "s"}</span></li>
        </ul>
        <p className="small">
          {searchedLiterature
            ? `${works} published work${works === 1 ? "" : "s"} compared from OpenAlex.`
            : "Published literature was not searched, so copying from published papers cannot be ruled out."}
        </p>
        {!searchedLiterature && (
          <p className="uncertainty">
            OpenAlex is not configured. Set AI_SCREENING_OPENALEX_API_KEY or AI_SCREENING_OPENALEX_MAILTO in .env and run screening again to compare against published literature.
          </p>
        )}
      </section>
      {matches.length > 0 && (
        <section className="drawer-section" aria-label="Matching sources">
          <h3>Where the text was found ({matches.length})</h3>
          <ul className="match-list">{matches.map((match) => <MatchRow key={match.match_id} match={match} />)}</ul>
        </section>
      )}
    </>
  );
}
