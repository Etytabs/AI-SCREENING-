"use client";

import { useState } from "react";
import { ACTION_LABELS } from "../../lib/labels";
import type { ReviewerAction } from "../../lib/types";

interface Props {
  canDecide: boolean;
  onDecide: (action: ReviewerAction, note: string) => Promise<void>;
  onNote: (note: string) => Promise<void>;
}

const ACTIONS: ReviewerAction[] = ["CONFIRM", "DISMISS"];

export function DecisionPanel({ canDecide, onDecide, onNote }: Props) {
  const [action, setAction] = useState<ReviewerAction>("CONFIRM");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);

  if (!canDecide) {
    return <p className="muted">Only a Reviewer or Grant Administrator can record decisions on findings.</p>;
  }

  async function submit(kind: "decision" | "note") {
    if (!note.trim()) {
      setError(kind === "decision" ? "A rationale is required for every decision." : "The note is empty.");
      return;
    }
    setBusy(true);
    setError(null);
    setSaved(null);
    try {
      if (kind === "decision") await onDecide(action, note.trim());
      else await onNote(note.trim());
      setSaved(kind === "decision" ? `Decision recorded: ${ACTION_LABELS[action]}` : "Note added");
      setNote("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="decision-panel">
      <fieldset>
        <legend>Reviewer action</legend>
        {ACTIONS.map((a) => (
          <label key={a} className="radio">
            <input type="radio" name="reviewer-action" value={a} checked={action === a} onChange={() => setAction(a)} />
            {ACTION_LABELS[a]}
          </label>
        ))}
      </fieldset>
      <label className="block-label">
        Rationale / note *
        <textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} placeholder="Which evidence did you check, and why this action?" />
      </label>
      <div className="req-actions">
        <button className="dark-button" disabled={busy} onClick={() => submit("decision")}>Record decision</button>
        <button className="ghost-button" disabled={busy} onClick={() => submit("note")}>Add note only</button>
      </div>
      <p className="muted small">Your decision is recorded next to the AI signal; it does not overwrite it. Decisions on findings are not funding decisions.</p>
      {error && <p className="form-error" role="alert">{error}</p>}
      {saved && <p className="form-ok" role="status">{saved}</p>}
    </div>
  );
}
