"use client";

import { useEffect, useMemo, useRef } from "react";

import { REVIEW_STATE_LABELS } from "../../lib/labels";
import type { Finding, ReviewerAction } from "../../lib/types";
import { DecisionPanel } from "./DecisionPanel";
import { useWorkspace } from "./WorkspaceContext";

/**
 * Records a reviewer decision without leaving the results page.
 *
 * A decision belongs to one finding, so this decides the first one still awaiting a
 * reviewer; once it is recorded the refreshed findings move it on to the next.
 * Recording goes through the same client.decide call as the review workspace.
 */
export function DecisionModal({
  findings,
  onClose,
  onRecorded,
}: {
  findings: Finding[];
  onClose: () => void;
  onRecorded: () => void | Promise<void>;
}) {
  const { client, role } = useWorkspace();
  const closeRef = useRef<HTMLButtonElement>(null);

  const selected = useMemo(
    () => findings.find((f) => f.review_state === "PENDING") ?? findings[0],
    [findings],
  );

  useEffect(() => {
    closeRef.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function record(action: ReviewerAction, note: string) {
    if (!selected) return;
    await client.decide(selected.finding_id, action, note);
    await onRecorded();
  }

  async function addNote(note: string) {
    if (!selected) return;
    await client.addNote(selected.finding_id, note);
    await onRecorded();
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal modal-wide"
        role="dialog"
        aria-modal="true"
        aria-label="Human decision"
        onClick={(event) => event.stopPropagation()}
      >
        <header>
          <div>
            <div className="eyebrow">HUMAN DECISION</div>
            <h2>Record a decision</h2>
          </div>
          <button ref={closeRef} className="close" onClick={onClose} aria-label="Close human decision">Close ×</button>
        </header>

        <div className="modal-body">
          {!selected ? (
            <p className="muted">There is no finding to decide on for this document.</p>
          ) : (
            <section className="drawer-section">
              <h3>Decision on {selected.title}</h3>
              <p className="small">{selected.explanation}</p>
              <p><b>{REVIEW_STATE_LABELS[selected.review_state]}</b></p>
              <DecisionPanel
                key={selected.finding_id}
                canDecide={role === "REVIEWER" || role === "GRANT_ADMINISTRATOR"}
                onDecide={record}
                onNote={addNote}
              />
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
