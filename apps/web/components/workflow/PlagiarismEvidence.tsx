"use client";

import { useState } from "react";

import { isPublishedMatch } from "../../lib/matches";
import type { Finding, SimilarityMatch } from "../../lib/types";
import { SyntheticBadge } from "./ui";

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
  published_work: "Published literature",
};

function num(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function pct(value: number | null | undefined): string {
  return value == null || !Number.isFinite(value) ? "Not available" : `${Math.round(value * 1000) / 10}%`;
}

/** Percentage dial: the headline number a reviewer reads first. */
function SimilarityDial({ index }: { index: number }) {
  return (
    <div className="similarity-dial" role="img" aria-label={`Highest published-source similarity score ${index} percent`}>
      <strong>{index}%</strong>
      <span>Highest published-source similarity score</span>
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
  return (
    <li className="plagiarism-match">
      <div className="evidence-meta">
        <b>{match.title ?? match.record_id}</b>
        <SyntheticBadge origin={match.data_origin} />
        <span>{SOURCE_LABELS[match.source_type] ?? match.source_type.replace(/_/g, " ")}</span>
        {SOURCE_FLAGS[match.source_type] && <span className="dup-flag">[{SOURCE_FLAGS[match.source_type]}]</span>}
      </div>
      <small>
        Similarity score {pct(match.similarity_score)} · {pct(match.query_coverage)} verbatim passage coverage · {pct(match.source_coverage)} content phrase overlap
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
  const works = typeof details.published_works_compared === "number" ? details.published_works_compared : null;
  const searchedLiterature = details.published_literature_searched === true;

  // Published literature only. Overlap with other submissions in this call is a
  // duplication question and is reported by the duplication check instead.
  const matches = finding.matches.filter(isPublishedMatch);
  const top = matches.reduce<SimilarityMatch | null>(
    (best, match) => (best === null || match.similarity_score > best.similarity_score ? match : best),
    null,
  );
  const index = top ? top.similarity_score * 100 : null;

  return (
    <>
      <section className="drawer-section" aria-label="Similarity index">
        <h3>Published-literature similarity</h3>
        {index !== null && <SimilarityDial index={Math.round(index * 10) / 10} />}
        {top && <ul className="similarity-split" aria-label="Similarity breakdown">
          <li><b>{pct(top.query_coverage)}</b><span>verbatim passage coverage</span></li>
          <li><b>{pct(top.source_coverage)}</b><span>content phrase overlap</span></li>
          <li><b>{matches.length}</b><span>published source{matches.length === 1 ? "" : "s"}</span></li>
        </ul>}
        <p className="small">
          {searchedLiterature
            ? works !== null ? `${works} published work${works === 1 ? "" : "s"} compared from OpenAlex.` : "Published literature was searched; the number of works compared is unavailable."
            : "Published literature was not searched; no conclusion about published sources can be drawn."}
        </p>
        {searchedLiterature && !top && <p className="small">No matching published sources were recorded in this run.</p>}
        <p className="small">Similarity is a signal for human assessment, not proof of plagiarism.</p>
        {!searchedLiterature && (
          <p className="uncertainty">
            Check source availability and screening coverage before drawing conclusions.
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
