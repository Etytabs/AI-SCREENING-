"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";

import { formatDate, SCREENING_STATE_LABELS } from "../../lib/labels";
import type { ApplicationRow } from "../../lib/types";
import { SignalBadge, StatusBadge } from "./ui";

const PROGRESS_LABELS: Record<ApplicationRow["review_progress"], string> = {
  NOT_SCREENED: "Not screened yet",
  PENDING: "No finding reviewed yet",
  IN_PROGRESS: "Review in progress",
  COMPLETE: "Every finding has a reviewer decision",
};

export function ScreeningStatusDialog({ row, onClose }: { row: ApplicationRow; onClose: () => void }) {
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    closeRef.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  const screened = row.screening_status !== "NOT_SCREENED";
  const checks: [string, React.ReactNode][] = [
    ["Eligibility", <StatusBadge key="e" status={row.eligibility} />],
    ["Completeness", <StatusBadge key="c" status={row.completeness} />],
    ["Duplication", <SignalBadge key="d" signal={row.duplication} />],
    ["Plagiarism", <SignalBadge key="p" signal={row.text_similarity} />],
    ["Novelty", <SignalBadge key="n" signal={row.novelty} />],
  ];

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={`Screening status for ${row.application_reference}`}
        onClick={(event) => event.stopPropagation()}
      >
        <header>
          <div>
            <div className="eyebrow">SCREENING STATUS</div>
            <h2>{row.document_names?.[0] ?? row.application_reference}</h2>
            <p className="muted small">{[row.application_reference, row.title].filter(Boolean).join(" · ")}</p>
          </div>
          <button ref={closeRef} className="close" onClick={onClose} aria-label="Close screening status">Close ×</button>
        </header>

        <div className="modal-body">
          <dl className="modal-meta">
            <dt>Screening</dt>
            <dd>
              <StatusBadge
                status={["QUEUED", "RUNNING"].includes(row.screening_status) ? "PROCESSING" : row.screening_status}
                label={SCREENING_STATE_LABELS[row.screening_status]}
              />
            </dd>
            <dt>Last screened</dt>
            <dd>{row.last_screened_at ? formatDate(row.last_screened_at) : "—"}</dd>
            <dt>Documents</dt>
            <dd>
              <ul className="file-list">
                {(row.document_names ?? []).map((name) => <li key={name}>{name}</li>)}
              </ul>
              {row.unreadable_documents > 0 && (
                <span className="warn-text">{row.unreadable_documents} could not be read</span>
              )}
            </dd>
          </dl>

          {!screened ? (
            <p className="muted">This application has not been screened yet, so there is no result to review.</p>
          ) : (
            <>
              <div className="eyebrow">CHECKS</div>
              <dl className="modal-checks">
                {checks.map(([label, badge]) => (
                  <div key={label}>
                    <dt>{label}</dt>
                    <dd>{badge}</dd>
                  </div>
                ))}
              </dl>

              <div className="eyebrow">REVIEWER PROGRESS</div>
              <p>
                <b>{row.reviewed_findings} of {row.total_findings}</b> finding{row.total_findings === 1 ? "" : "s"} reviewed
                {row.open_findings > 0 && ` · ${row.open_findings} still open`}
              </p>
              <p className="muted small">{PROGRESS_LABELS[row.review_progress]}</p>
              <Link className="dark-button" href={`/dashboard/applications/view?id=${row.id}`}>Open full review →</Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
