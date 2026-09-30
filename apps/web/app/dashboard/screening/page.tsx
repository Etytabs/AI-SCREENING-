"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ScreeningProgressView } from "../../../components/workflow/ScreeningProgressView";
import { NoCallSelected, Notice, PageHeader, StatusBadge } from "../../../components/workflow/ui";
import { useWorkspace } from "../../../components/workflow/WorkspaceContext";
import { ApiError } from "../../../lib/api";
import { STAGE_LABELS } from "../../../lib/labels";
import type { ApplicationRow, BatchProgress, StageName } from "../../../lib/types";

const STAGE_HELP: Record<StageName, string> = {
  DOCUMENT_EXTRACTION: "Reads the text already extracted at upload; unreadable files are reported, never guessed.",
  REQUIREMENT_MAPPING: "Maps each verified requirement to the most relevant passages in the application.",
  ELIGIBILITY: "Checks verified eligibility requirements. Missing evidence gives REVIEW REQUIRED, never FAIL.",
  COMPLETENESS: "Checks the documents the call requires. FAIL only when every file was readable and the document is absent.",
  DUPLICATION: "Whole-proposal similarity against other applications and authorized historical records.",
  TEXT_SIMILARITY: "Shared verbatim passages, excluding text quoted from the call document.",
  NOVELTY: "Per-dimension comparison producing a signal for reviewers, not a novelty judgement.",
  EVIDENCE: "Validates every citation; a FAIL without application evidence is downgraded to review.",
};

export default function ScreeningPage() {
  const { client, callId, call, role, callsState, refreshCalls } = useWorkspace();
  const [rows, setRows] = useState<ApplicationRow[]>([]);
  const [progress, setProgress] = useState<BatchProgress | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const load = useCallback(async () => {
    if (!callId) return;
    try {
      const [r, summary] = await Promise.all([client.listApplications(callId), client.dashboard(callId)]);
      setRows(r);
      setProgress(summary.latest_batch);
      setError(null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Unable to load screening status.");
    } finally {
      setLoaded(true);
    }
  }, [client, callId]);

  useEffect(() => { setLoaded(false); load(); }, [load]);

  useEffect(() => {
    if (!progress || progress.finished >= progress.total) return;
    const timer = setTimeout(async () => {
      try {
        const next = await client.batchProgress(progress.batch_id);
        setProgress(next);
        if (next.finished >= next.total) { await load(); await refreshCalls(); }
      } catch (e) {
        setError(e instanceof ApiError ? e.message : "Lost contact with the screening API.");
      }
    }, 1500);
    return () => clearTimeout(timer);
  }, [progress, client, load, refreshCalls]);

  async function launch(ids?: string[]) {
    if (!callId) return;
    setError(null);
    try {
      const batch = await client.screenCall(callId, ids);
      setProgress(await client.batchProgress(batch.id));
      setSelected(new Set());
      await refreshCalls();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Screening could not be started.");
    }
  }

  const canLaunch = role !== "REVIEWER" && !!call && ["READY_FOR_SUBMISSIONS", "SCREENING", "REVIEW"].includes(call.status);
  const unscreened = rows.filter((r) => r.screening_status === "NOT_SCREENED").map((r) => r.id);
  const busy = !!progress && progress.finished < progress.total;

  return (
    <>
      <PageHeader eyebrow="GRANT SCREENING / SCREENING" title="Batch screening" intro="Runs asynchronously in the background. Each application passes through the same eight stages." />
      {callsState === "ready" && !callId && <NoCallSelected />}
      {error && <Notice kind="error" title="Screening problem">{error}</Notice>}
      {callId && !loaded && <Notice kind="loading" title="Loading…" />}

      {callId && loaded && (
        <>
          <section className="panel">
            <h2>Launch screening</h2>
            {!canLaunch && role === "REVIEWER" && <Notice kind="info" title="Read-only">Only administrators can launch screening.</Notice>}
            {!canLaunch && role !== "REVIEWER" && call && (
              <Notice kind="review" title="Requirements not confirmed"><Link href={`/dashboard/calls?id=${call.id}`}>Confirm the requirements</Link> before screening.</Notice>
            )}
            {rows.length === 0 ? (
              <Notice kind="empty" title="No applications to screen"><Link href="/dashboard/applications">Upload applications</Link> first.</Notice>
            ) : (
              <>
                <table className="data-table select-table">
                  <thead><tr><th><span className="sr-only">Select</span></th><th>Application</th><th>Screening status</th></tr></thead>
                  <tbody>
                    {rows.map((r) => (
                      <tr key={r.id}>
                        <td><input type="checkbox" aria-label={`Select ${r.application_reference}`} checked={selected.has(r.id)} disabled={!canLaunch || busy}
                          onChange={(e) => setSelected((s) => { const next = new Set(s); if (e.target.checked) next.add(r.id); else next.delete(r.id); return next; })} /></td>
                        <td><b>{r.application_reference}</b> {r.title}</td>
                        <td><StatusBadge status={["QUEUED", "RUNNING"].includes(r.screening_status) ? "PROCESSING" : r.screening_status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="req-actions">
                  <button className="dark-button" disabled={!canLaunch || busy || selected.size === 0} onClick={() => launch([...selected])}>Screen selected ({selected.size})</button>
                  <button className="ghost-button" disabled={!canLaunch || busy || unscreened.length === 0} onClick={() => launch(unscreened)}>Screen not-yet-screened ({unscreened.length})</button>
                  <button className="ghost-button" disabled={!canLaunch || busy} onClick={() => launch()}>Re-screen all ({rows.length})</button>
                </div>
              </>
            )}
          </section>

          <section className="panel">
            <h2>Latest batch</h2>
            {progress ? <ScreeningProgressView progress={progress} rows={rows} /> : <p className="muted">No screening has been run for this call.</p>}
          </section>

          <section className="panel">
            <h2>Pipeline stages</h2>
            <dl className="stage-help">
              {(Object.keys(STAGE_HELP) as StageName[]).map((s) => (<div key={s}><dt>{STAGE_LABELS[s]}</dt><dd>{STAGE_HELP[s]}</dd></div>))}
            </dl>
          </section>
        </>
      )}
    </>
  );
}
