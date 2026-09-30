"use client";

import { ACTION_LABELS, FINDING_TYPE_LABELS, formatDate, REVIEW_STATE_LABELS } from "../../lib/labels";
import type { FindingDetail, FindingEvidence, ReviewerAction } from "../../lib/types";
import { DecisionPanel } from "./DecisionPanel";
import { SignalBadge, StatusBadge, SyntheticBadge } from "./ui";

const SOURCE_LABELS: Record<string, string> = {
  application_document: "Application document",
  rfp: "Call document (requirement)",
  administrator_requirement: "Administrator-authored requirement",
  submission_inventory: "Submission inventory",
  same_call_application: "Another application in this call",
  historical_application: "Historical application",
  funded_project: "Funded project",
};

const RELATIONSHIP_LABELS: Record<string, string> = {
  SUPPORTS: "supports",
  CONTRADICTS: "contradicts",
  PARTIALLY_SUPPORTS: "partially supports",
  UNCERTAIN: "uncertain relevance",
};

interface Props {
  detail: FindingDetail;
  documentNames: Record<string, string>;
  canDecide: boolean;
  onClose: () => void;
  onShowInDocument: (evidence: FindingEvidence) => void;
  onDecide: (action: ReviewerAction, note: string) => Promise<void>;
  onNote: (note: string) => Promise<void>;
}

function EvidenceItem({ item, documentNames, onShow }: { item: FindingEvidence; documentNames: Record<string, string>; onShow: (e: FindingEvidence) => void }) {
  const inApplication = item.source_type === "application_document" && item.document_id && documentNames[item.document_id];
  const where = [
    inApplication ? documentNames[item.document_id as string] : null,
    item.page ? `p.${item.page}` : null,
    item.section,
  ].filter(Boolean).join(" · ");
  return (
    <li className={`evidence-item ev-${item.relationship.toLowerCase()}`}>
      <div className="evidence-meta">
        <b>{SOURCE_LABELS[item.source_type] ?? item.source_type}</b>
        <span>{RELATIONSHIP_LABELS[item.relationship] ?? item.relationship}</span>
        {item.citation_valid === true && <span className="cite-ok" aria-label="Citation verified against extracted text">✓ citation verified</span>}
        {item.citation_valid === false && <span className="cite-bad">✕ citation not verified</span>}
        {item.citation_valid === null && item.source_type !== "rfp" && <span className="cite-none">no page citation</span>}
      </div>
      {where && <small>{where}</small>}
      <blockquote>{item.text}</blockquote>
      {inApplication && <button className="text-button" onClick={() => onShow(item)}>Show in document →</button>}
    </li>
  );
}

export function EvidenceDrawer({ detail, documentNames, canDecide, onClose, onShowInDocument, onDecide, onNote }: Props) {
  const { finding, decisions, notes } = detail;
  const applicationEvidence = finding.evidence.filter((e) => e.source_type === "application_document");
  const showSignal = finding.signal && finding.type !== "eligibility" && finding.type !== "completeness";
  return (
    <aside className="evidence-drawer" aria-label="Evidence drawer" role="complementary">
      <header>
        <div>
          <div className="eyebrow">{FINDING_TYPE_LABELS[finding.type]}</div>
          <h2>{finding.title}</h2>
        </div>
        <button className="close" onClick={onClose} aria-label="Close evidence drawer">Close ×</button>
      </header>

      <section className="drawer-section">
        <h3>AI signal</h3>
        <div className="drawer-badges">
          <StatusBadge status={finding.status} />
          {showSignal && <SignalBadge signal={finding.signal} />}
          <span className="muted small">{finding.confidence !== null ? `confidence ${finding.confidence.toFixed(2)}` : "confidence not computed"}</span>
        </div>
        <p>{finding.explanation}</p>
        <p className="small"><b>Suggested next step:</b> {finding.recommended_action}</p>
        <p className="muted small">Method: {finding.method}</p>
      </section>

      <section className="drawer-section">
        <h3>Evidence ({finding.evidence.length})</h3>
        {applicationEvidence.length === 0 && (
          <p className="uncertainty">No passage from this application could be cited for this finding. Treat the result as unverified until a reviewer checks the documents.</p>
        )}
        <ul className="evidence-list">
          {finding.evidence.map((item) => <EvidenceItem key={item.evidence_id} item={item} documentNames={documentNames} onShow={onShowInDocument} />)}
        </ul>
      </section>

      {finding.type === "plagiarism" && (() => {
        const publicSource = finding.details.public_source_similarity as {
          status?: string;
          human_review_required?: boolean;
          findings?: Array<{
            similarity: number;
            match_type: string;
            applicant_passage: string;
            source_passage: string;
            source: {
              title?: string;
              url: string;
              authors?: string[];
              publisher?: string | null;
              published_date?: string | null;
              metadata_confidence?: number;
            };
          }>;
        } | undefined;
        if (!publicSource || !publicSource.findings?.length) return null;
        return (
          <section className="drawer-section">
            <h3>Public-source similarity</h3>
            <p className="uncertainty">Potential text similarity detected. This evidence does not establish plagiarism; an authorized reviewer must compare the passages and verify attribution.</p>
            <ul className="match-list">
              {publicSource.findings.map((item, index) => (
                <li key={item.source.url + index}>
                  <div className="evidence-meta">
                    <b>{item.source.title || "Public source"}</b>
                    <span>{Math.round(item.similarity * 100)}% similarity</span>
                    <span>{item.match_type.replace(/-/g, " ")}</span>
                  </div>
                  {item.source.authors?.length ? <small>Author(s): {item.source.authors.join("; ")}</small> : null}
                  {item.source.publisher ? <small>Publisher / institution: {item.source.publisher}</small> : null}
                  {item.source.published_date ? <small>Published: {item.source.published_date}</small> : null}
                  <small>Attribution metadata confidence: {item.source.metadata_confidence !== undefined ? item.source.metadata_confidence.toFixed(2) : "not available"}</small>
                  <div className="source-comparison">
                    <div><b>Applicant passage</b><blockquote>{item.applicant_passage}</blockquote></div>
                    <div><b>Source passage</b><blockquote>{item.source_passage}</blockquote></div>
                  </div>
                  <a className="text-button" href={item.source.url} target="_blank" rel="noreferrer">Open original source ↗</a>
                </li>
              ))}
            </ul>
          </section>
        );
      })()}
      {finding.type === "duplication" && finding.matches.length > 0 && (
        <section className="drawer-section">
          <h3>Compared records ({finding.matches.length})</h3>
          <p className="uncertainty">Potential duplicate or strong semantic similarity detected. This is comparison evidence, not an automatic duplicate verdict.</p>
          <ul className="match-list">
            {finding.matches.map((m) => (
              <li key={m.match_id}>
                <div className="evidence-meta">
                  <b>{m.title ?? m.record_id}</b>
                  <SyntheticBadge origin={m.data_origin} />
                  <span>{SOURCE_LABELS[m.source_type] ?? m.source_type}</span>
                </div>
                <small>
                  similarity {m.similarity_score.toFixed(2)}
                  {m.lexical_score !== null && ` · lexical ${m.lexical_score.toFixed(2)}`}
                  {m.semantic_score !== null && ` · semantic ${m.semantic_score.toFixed(2)}`}
                  {m.reranker_score !== null && ` · reranker ${m.reranker_score.toFixed(2)}`}
                </small>
                {m.matched_section && <p className="small"><b>Matching section:</b> {m.matched_section.replace(/_/g, " ")}</p>}
                {m.matching_concepts.length > 0 && <p className="concepts"><b>Matching concepts:</b> {m.matching_concepts.map((c) => <span key={c}>{c}</span>)}</p>}
                <p className="small">{m.explanation}</p>
                {m.matched_passage && (
                  <div className="source-comparison">
                    <div>
                      <b>Matched passage</b>
                      <blockquote>{m.matched_passage}</blockquote>
                    </div>
                  </div>
                )}
                <p className="muted small">Record reference: {m.record_id}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="drawer-section">
        <h3>Human decision</h3>
        <p><b>{REVIEW_STATE_LABELS[finding.review_state]}</b></p>
        {decisions.length > 0 && (
          <ol className="history">
            {decisions.map((d) => (
              <li key={d.id}>{formatDate(d.created_at)} · {d.reviewer_id} · {ACTION_LABELS[d.action]} — “{d.note}”</li>
            ))}
          </ol>
        )}
        {notes.length > 0 && (
          <ul className="history">
            {notes.map((n) => <li key={n.id}>{formatDate(n.created_at)} · {n.author_id} · note — “{n.note}”</li>)}
          </ul>
        )}
        <DecisionPanel canDecide={canDecide} onDecide={onDecide} onNote={onNote} />
      </section>
    </aside>
  );
}
