"use client";

import { useEffect, useRef, useState } from "react";

import { ApiError } from "../../lib/api";
import { extraDuplicationMatches } from "../../lib/matches";
import { ACTION_LABELS, FINDING_TYPE_LABELS, formatDate, REVIEW_STATE_LABELS } from "../../lib/labels";
import type { Finding, FindingDetail } from "../../lib/types";
import { DuplicationEvidence } from "./DuplicationEvidence";
import { Notice, SignalBadge, StatusBadge } from "./ui";
import { PlagiarismEvidence } from "./PlagiarismEvidence";
import { useWorkspace } from "./WorkspaceContext";

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

/**
 * Read-only evidence popup. Keeps the page behind it exactly as it was.
 *
 * Takes every finding behind the card that was clicked, so the detail the card no
 * longer shows (each requirement, each compared source) is all reachable here.
 */
export function EvidenceModal({
  findings,
  siblingFindings,
  onClose,
}: {
  findings: Finding[];
  /** Every finding for this document, so duplication can show the matches the
   *  text-similarity check contributed. */
  siblingFindings?: Finding[];
  onClose: () => void;
}) {
  const { client } = useWorkspace();
  const [findingId, setFindingId] = useState(findings[0]?.finding_id ?? "");
  const [detail, setDetail] = useState<FindingDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    closeRef.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  useEffect(() => {
    if (!findingId) return;
    let cancelled = false;
    setDetail(null);
    setError(null);
    client
      .getFinding(findingId)
      .then((data) => { if (!cancelled) setDetail(data); })
      .catch((e) => {
        if (!cancelled) setError(e instanceof ApiError ? e.message : "Unable to load this evidence.");
      });
    return () => { cancelled = true; };
  }, [client, findingId]);

  const finding = detail?.finding;
  const isPlagiarism = finding?.type === "plagiarism";
  const isDuplication = finding?.type === "duplication";
  const showSignal = finding?.signal && finding.type !== "eligibility" && finding.type !== "completeness";

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal modal-wide"
        role="dialog"
        aria-modal="true"
        aria-label={finding ? `Evidence for ${finding.title}` : "Evidence"}
        onClick={(event) => event.stopPropagation()}
      >
        <header>
          <div>
            <div className="eyebrow">{finding ? FINDING_TYPE_LABELS[finding.type] : "EVIDENCE"}</div>
            <h2>{finding?.title ?? "Loading…"}</h2>
          </div>
          <button ref={closeRef} className="close" onClick={onClose} aria-label="Close evidence">Close ×</button>
        </header>

        <div className="modal-body">
          {findings.length > 1 && (
            <div className="evidence-switcher" role="tablist" aria-label="Findings">
              {findings.map((f) => (
                <button
                  key={f.finding_id}
                  role="tab"
                  type="button"
                  aria-selected={f.finding_id === findingId}
                  className={f.finding_id === findingId ? "active" : ""}
                  onClick={() => setFindingId(f.finding_id)}
                >
                  {f.title}
                </button>
              ))}
            </div>
          )}
          {error && <Notice kind="error" title="Could not load evidence">{error}</Notice>}
          {!detail && !error && <Notice kind="loading" title="Loading evidence…" />}

          {detail && finding && (
            <>
              {!isPlagiarism && (
                <section className="drawer-section">
                  <h3>AI signal</h3>
                  <div className="drawer-badges">
                    <StatusBadge status={finding.status} />
                    {showSignal && <SignalBadge signal={finding.signal} />}
                    {finding.type !== "duplication" && (
                      <span className="muted small">
                        {finding.confidence !== null ? `confidence ${finding.confidence.toFixed(2)}` : "confidence not computed"}
                      </span>
                    )}
                  </div>
                  <p>{finding.explanation}</p>
                  <p className="small"><b>Suggested next step:</b> {finding.recommended_action}</p>
                </section>
              )}

              {isDuplication && (
                <DuplicationEvidence
                  finding={finding}
                  documentNames={{}}
                  additionalMatches={extraDuplicationMatches(finding, siblingFindings)}
                />
              )}
              {isPlagiarism && <PlagiarismEvidence finding={finding} />}

              {!isPlagiarism && !isDuplication && (
                <section className="drawer-section">
                  <h3>Evidence ({finding.evidence.length})</h3>
                  {finding.evidence.length === 0 ? (
                    <p className="uncertainty">No passage could be cited for this finding.</p>
                  ) : (
                    <ul className="evidence-list">
                      {finding.evidence.map((item) => (
                        <li key={item.evidence_id} className={`evidence-item ev-${item.relationship.toLowerCase()}`}>
                          <div className="evidence-meta">
                            <b>{SOURCE_LABELS[item.source_type] ?? item.source_type}</b>
                            {item.citation_valid === true && <span className="cite-ok">✓ citation verified</span>}
                            {item.citation_valid === false && <span className="cite-bad">✕ citation not verified</span>}
                          </div>
                          {(item.page || item.section) && (
                            <small>{[item.page ? `p.${item.page}` : null, item.section].filter(Boolean).join(" · ")}</small>
                          )}
                          <blockquote>{item.text}</blockquote>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              )}

              <section className="drawer-section">
                <h3>Human decision</h3>
                <p><b>{REVIEW_STATE_LABELS[finding.review_state]}</b></p>
                {detail.decisions.length > 0 && (
                  <ol className="history">
                    {detail.decisions.map((d) => (
                      <li key={d.id}>{formatDate(d.created_at)} · {d.reviewer_id} · {ACTION_LABELS[d.action]} — “{d.note}”</li>
                    ))}
                  </ol>
                )}
                {detail.notes.length > 0 && (
                  <ul className="history">
                    {detail.notes.map((n) => <li key={n.id}>{formatDate(n.created_at)} · {n.author_id} · note — “{n.note}”</li>)}
                  </ul>
                )}
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
