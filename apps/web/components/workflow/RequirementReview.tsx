"use client";

import { useState } from "react";
import { CATEGORY_LABELS, formatAmount } from "../../lib/labels";
import type { CriterionCategory, RfpCriterion } from "../../lib/types";

export interface RequirementActions {
  onVerify: (id: string) => Promise<void>;
  onReject: (id: string, note: string) => Promise<void>;
  onEdit: (id: string, changes: { title: string; requirement_text: string }) => Promise<void>;
  onToggleActive: (id: string, active: boolean) => Promise<void>;
  onAdd: (input: { title: string; requirement_text: string; category: CriterionCategory }) => Promise<void>;
  onConfirm: () => Promise<void>;
}

interface Props extends RequirementActions {
  requirements: RfpCriterion[];
  canEdit: boolean;
  confirmed: boolean;
}

const STATUS_TEXT: Record<RfpCriterion["status"], string> = {
  EXTRACTED: "Extracted · awaiting verification",
  NEEDS_REVIEW: "Low confidence · needs review",
  VERIFIED: "Verified",
  EDITED: "Edited by administrator",
  REJECTED: "Rejected",
};

export function isPending(c: RfpCriterion) {
  return c.active && c.status !== "REJECTED" && !c.is_confirmed;
}

function parameterSummary(c: RfpCriterion): string | null {
  const p = c.parameters as Record<string, unknown>;
  if (typeof p.max_amount === "number") return `Maximum ${formatAmount(p.max_amount, p.currency as string)}`;
  if (typeof p.max_months === "number") return `Maximum ${p.max_months} months`;
  if (typeof p.country === "string") return `Country: ${p.country}`;
  if (typeof p.document_type === "string") return `Document: ${String(p.document_type).replace(/_/g, " ")}${p.conditional ? " (conditional)" : ""}`;
  if (Array.isArray(p.any_of) && p.any_of.length) return `Any of: ${(p.any_of as string[]).join(", ")}`;
  return null;
}

function RequirementItem({ c, canEdit, actions }: { c: RfpCriterion; canEdit: boolean; actions: RequirementActions }) {
  const [mode, setMode] = useState<"view" | "edit" | "reject">("view");
  const [title, setTitle] = useState(c.title);
  const [text, setText] = useState(c.requirement_text);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const summary = parameterSummary(c);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError(null);
    try {
      await action();
      setMode("view");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <li className={`requirement${!c.active ? " inactive" : ""}${isPending(c) ? " pending" : ""}`} data-testid={`requirement-${c.criterion_code}`}>
      <div className="requirement-head">
        <span className="req-code">{c.criterion_code}</span>
        <b>{c.title}</b>
        <span className="req-category">{CATEGORY_LABELS[c.category]}</span>
        <span className={`req-status req-${c.status.toLowerCase()}`}>{!c.active ? "Deactivated" : STATUS_TEXT[c.status]}</span>
      </div>
      {mode === "edit" ? (
        <div className="req-edit">
          <label>Title<input value={title} onChange={(e) => setTitle(e.target.value)} /></label>
          <label>Requirement text<textarea rows={3} value={text} onChange={(e) => setText(e.target.value)} /></label>
          <div className="req-actions">
            <button className="dark-button" disabled={busy || !text.trim() || !title.trim()} onClick={() => run(() => actions.onEdit(c.id, { title, requirement_text: text }))}>Save edit</button>
            <button className="ghost-button" onClick={() => setMode("view")}>Cancel</button>
          </div>
        </div>
      ) : (
        <blockquote className="req-text">
          {c.requirement_text}
          <footer>
            {c.source_type === "administrator" ? "Added by administrator" : c.source_type === "administrator_edit" ? "Edited from the call document" : `Call document${c.source_page ? ` p.${c.source_page}` : ""}${c.source_section ? ` · ${c.source_section}` : ""}`}
            {c.extracted_confidence !== null && ` · extraction confidence ${c.extracted_confidence.toFixed(2)}`}
            {summary && ` · ${summary}`}
            {` · ${c.screening_use === "informational" ? "informational (not screened)" : `used in ${c.screening_use} screening`}`}
          </footer>
        </blockquote>
      )}
      {c.administrator_note && <p className="req-note">Note: {c.administrator_note}</p>}
      {mode === "reject" && (
        <div className="req-edit">
          <label>Reason for rejection *<input value={note} onChange={(e) => setNote(e.target.value)} /></label>
          <div className="req-actions">
            <button className="dark-button" disabled={busy || !note.trim()} onClick={() => run(() => actions.onReject(c.id, note))}>Reject requirement</button>
            <button className="ghost-button" onClick={() => setMode("view")}>Cancel</button>
          </div>
        </div>
      )}
      {canEdit && mode === "view" && (
        <div className="req-actions">
          {c.active && !c.is_confirmed && c.status !== "REJECTED" && (
            <button className="dark-button" disabled={busy} onClick={() => run(() => actions.onVerify(c.id))}>Verify</button>
          )}
          {c.active && <button className="ghost-button" disabled={busy} onClick={() => setMode("edit")}>Edit</button>}
          {c.active && c.status !== "REJECTED" && <button className="ghost-button" disabled={busy} onClick={() => setMode("reject")}>Reject</button>}
          <button className="ghost-button" disabled={busy} onClick={() => run(() => actions.onToggleActive(c.id, !c.active))}>{c.active ? "Deactivate" : "Reactivate"}</button>
        </div>
      )}
      {error && <p className="form-error" role="alert">{error}</p>}
    </li>
  );
}

function AddRequirement({ onAdd }: { onAdd: RequirementActions["onAdd"] }) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [category, setCategory] = useState<CriterionCategory>("other");
  const [error, setError] = useState<string | null>(null);
  if (!open) return <button className="ghost-button" onClick={() => setOpen(true)}>Add requirement manually</button>;
  return (
    <div className="req-edit add-requirement">
      <label>Title *<input value={title} onChange={(e) => setTitle(e.target.value)} /></label>
      <label>Category<select value={category} onChange={(e) => setCategory(e.target.value as CriterionCategory)}>
        {(Object.keys(CATEGORY_LABELS) as CriterionCategory[]).map((key) => <option key={key} value={key}>{CATEGORY_LABELS[key]}</option>)}
      </select></label>
      <label>Requirement text *<textarea rows={3} value={text} onChange={(e) => setText(e.target.value)} /></label>
      <p className="muted">Manually added requirements are recorded as administrator-authored, not as extracted from the call document.</p>
      {error && <p className="form-error" role="alert">{error}</p>}
      <div className="req-actions">
        <button className="dark-button" disabled={!title.trim() || !text.trim()} onClick={async () => {
          try {
            await onAdd({ title, requirement_text: text, category });
            setOpen(false); setTitle(""); setText("");
          } catch (e) { setError(e instanceof Error ? e.message : "Could not add requirement"); }
        }}>Add requirement</button>
        <button className="ghost-button" onClick={() => setOpen(false)}>Cancel</button>
      </div>
    </div>
  );
}

export function RequirementReview({ requirements, canEdit, confirmed, ...actions }: Props) {
  const [filter, setFilter] = useState<"all" | "pending">("all");
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pending = requirements.filter(isPending);
  const shown = filter === "pending" ? pending : requirements;

  return (
    <section className="requirements" aria-label="Requirement review">
      <div className="requirements-bar">
        <div>
          <b>{requirements.filter((c) => c.active && c.is_confirmed).length} confirmed</b>
          <span> · {pending.length} awaiting verification · {requirements.filter((c) => c.status === "REJECTED").length} rejected</span>
        </div>
        <div className="segmented" role="group" aria-label="Filter requirements">
          <button aria-pressed={filter === "all"} onClick={() => setFilter("all")}>All</button>
          <button aria-pressed={filter === "pending"} onClick={() => setFilter("pending")}>Needs attention ({pending.length})</button>
        </div>
      </div>
      {requirements.length === 0 && <p className="muted">No requirements yet. Upload the call document or add requirements manually.</p>}
      <ol className="requirement-list">
        {shown.map((c) => <RequirementItem key={c.id} c={c} canEdit={canEdit} actions={actions} />)}
      </ol>
      {canEdit && <AddRequirement onAdd={actions.onAdd} />}
      {canEdit && (
        <div className="confirm-bar">
          <span>
            {confirmed
              ? "Requirements are confirmed and the call is open for submissions."
              : pending.length
                ? `${pending.length} requirement(s) must be verified, edited or rejected before submissions open.`
                : "All active requirements are verified."}
          </span>
          {!confirmed && (
            <button className="dark-button" disabled={pending.length > 0 || confirming || !requirements.length} onClick={async () => {
              setConfirming(true); setError(null);
              try { await actions.onConfirm(); } catch (e) { setError(e instanceof Error ? e.message : "Confirmation failed"); } finally { setConfirming(false); }
            }}>Confirm requirements and open submissions</button>
          )}
        </div>
      )}
      {error && <p className="form-error" role="alert">{error}</p>}
    </section>
  );
}
