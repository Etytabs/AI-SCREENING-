"use client";

import { ACTION_LABELS, FINDING_TYPE_LABELS, formatDate, REVIEW_STATE_LABELS } from "../../lib/labels";
import type { FindingDetail, FindingEvidence, ReviewerAction } from "../../lib/types";
import { DecisionPanel } from "./DecisionPanel";
import { DuplicationEvidence } from "./DuplicationEvidence";
import { PlagiarismEvidence } from "./PlagiarismEvidence";
import { SignalBadge, StatusBadge, SyntheticBadge } from "./ui";

const SOURCE_LABELS: Record<string, string> = {
  application_document: "Application document",
  published_work: "Published work",
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
  // Plagiarism reads as three sections only: the index, the matched sources, the decision.
  // Its own panel already carries the percentage, coverage and limitations.
  const isPlagiarism = finding.type === "plagiarism";
  return (
    <aside className="evidence-drawer" aria-label="Evidence drawer" role="complementary">
      <header>
        <div>
          <div className="eyebrow">{FINDING_TYPE_LABELS[finding.type]}</div>
          <h2>{finding.title}</h2>
        </div>
        <button className="close" onClick={onClose} aria-label="Close evidence drawer">Close ×</button>
      </header>

      {!isPlagiarism && (
        <section className="drawer-section">
          <h3>AI signal</h3>
          <div className="drawer-badges">
            <StatusBadge status={finding.status} />
            {showSignal && <SignalBadge signal={finding.signal} />}
            {finding.type !== "duplication" && <span className="muted small">{finding.confidence !== null ? `confidence ${finding.confidence.toFixed(2)}` : "confidence not computed"}</span>}
          </div>
          <p>{finding.explanation}</p>
          <p className="small"><b>Suggested next step:</b> {finding.recommended_action}</p>
          <p className="muted small">Method: {finding.method}</p>
        </section>
      )}

      {!isPlagiarism && (
        <section className="drawer-section">
          <h3>Evidence ({finding.evidence.length})</h3>
          {applicationEvidence.length === 0 && (
            <p className="uncertainty">No passage from this application could be cited for this finding. Treat the result as unverified until a reviewer checks the documents.</p>
          )}
          <ul className="evidence-list">
            {finding.evidence.map((item) => <EvidenceItem key={item.evidence_id} item={item} documentNames={documentNames} onShow={onShowInDocument} />)}
          </ul>
        </section>
      )}

      {finding.type === "duplication" && <DuplicationEvidence finding={finding} documentNames={documentNames} />}

      {finding.type === "plagiarism" && <PlagiarismEvidence finding={finding} />}

      {finding.type !== "duplication" && finding.type !== "plagiarism" && finding.matches.length > 0 && (
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
