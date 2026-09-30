"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ApplicationUpload } from "../../../components/workflow/ApplicationUpload";
import { ResultsTable, type ResultFilters } from "../../../components/workflow/ResultsTable";
import { NoCallSelected, Notice, PageHeader } from "../../../components/workflow/ui";
import { useWorkspace } from "../../../components/workflow/WorkspaceContext";
import { ApiError } from "../../../lib/api";
import type { ApplicationRow, PendingUpload } from "../../../lib/types";

function PendingAssociations({ pending, rows, onAssociate }: {
  pending: PendingUpload[];
  rows: ApplicationRow[];
  onAssociate: (id: string, target: { application_id?: string; new_reference?: string }) => Promise<void>;
}) {
  const [targets, setTargets] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  if (!pending.length) return null;
  return (
    <section className="panel">
      <h2>Files needing manual association ({pending.length})</h2>
      <p className="muted">These files could not be matched to an application by folder or file-name prefix. Choose where each belongs.</p>
      <table className="data-table">
        <thead><tr><th>File</th><th>Text extraction</th><th>Associate with</th><th /></tr></thead>
        <tbody>
          {pending.map((p) => (
            <tr key={p.id}>
              <td>{p.filename}</td>
              <td>{p.extraction_status}</td>
              <td>
                <select value={targets[p.id] ?? ""} onChange={(e) => setTargets((t) => ({ ...t, [p.id]: e.target.value }))} aria-label={`Associate ${p.filename}`}>
                  <option value="">New application</option>
                  {rows.map((r) => <option key={r.id} value={r.id}>{r.application_reference}</option>)}
                </select>
              </td>
              <td>
                <button className="ghost-button" onClick={async () => {
                  setError(null);
                  try {
                    const target = targets[p.id];
                    await onAssociate(p.id, target ? { application_id: target } : {});
                  } catch (e) { setError(e instanceof Error ? e.message : "Association failed"); }
                }}>Associate</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {error && <p className="form-error" role="alert">{error}</p>}
    </section>
  );
}

export default function ApplicationsPage() {
  const { client, callId, call, role, callsState, refreshCalls } = useWorkspace();
  const [rows, setRows] = useState<ApplicationRow[] | null>(null);
  const [allRows, setAllRows] = useState<ApplicationRow[]>([]);
  const [pending, setPending] = useState<PendingUpload[]>([]);
  const [filters, setFilters] = useState<ResultFilters>({});
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!callId) return;
    try {
      const [filtered, all, pend] = await Promise.all([
        client.listApplications(callId, { ...filters }),
        client.listApplications(callId),
        client.pendingUploads(callId),
      ]);
      setRows(filtered);
      setAllRows(all);
      setPending(pend);
      setError(null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Unable to load applications.");
    }
  }, [client, callId, filters]);

  useEffect(() => {
    setRows(null);
  }, [callId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!rows?.some((r) => ["QUEUED", "RUNNING"].includes(r.screening_status))) return;
    const timer = setTimeout(load, 2000);
    return () => clearTimeout(timer);
  }, [rows, load]);

  const canUpload = role !== "REVIEWER" && !!call && ["READY_FOR_SUBMISSIONS", "SCREENING", "REVIEW"].includes(call.status);
  const unscreened = allRows.filter((r) => r.screening_status === "NOT_SCREENED").length;
  const uploadBody = !call ? null : role === "REVIEWER" ? (
    <Notice kind="info" title="Read-only">Reviewers can inspect results but not upload applications.</Notice>
  ) : !canUpload ? (
    <Notice kind="review" title="Submissions are not open">
      Confirm this call&apos;s requirements first. <Link href={`/dashboard/calls?id=${call.id}`}>Go to requirement review</Link>
    </Notice>
  ) : (
    <ApplicationUpload
      onBatch={(files) => client.batchUpload(call.id, files)}
      onSingle={(files, reference) => client.createApplication(call.id, files, reference)}
      onDone={async () => { await load(); await refreshCalls(); }}
    />
  );

  return (
    <>
      <PageHeader
        eyebrow="GRANT SCREENING / APPLICATIONS"
        title="Applications"
        intro="Upload submissions and compare screening results across the call. Every result links to its evidence."
        actions={allRows.length ? <Link className="ghost-button" href="/dashboard/screening">{unscreened ? `Screen ${unscreened} new application(s)` : "Screening"}</Link> : undefined}
      />
      {callsState === "ready" && !callId && <NoCallSelected />}
      {error && <Notice kind="error" title="Applications unavailable">{error}</Notice>}
      {callId && !rows && !error && <Notice kind="loading" title="Loading applications…" />}
      {rows && allRows.length === 0 && <Notice kind="empty" title="No applications uploaded yet" />}
      <PendingAssociations pending={pending} rows={allRows} onAssociate={async (id, target) => { await client.associateUpload(id, target); await load(); }} />
      {rows && allRows.length > 0 && (
        <section className="panel">
          <h2>Screening results</h2>
          <ResultsTable rows={rows} filters={filters} onFiltersChange={setFilters} />
        </section>
      )}
      {call && rows && (
        <details className="panel upload-more" open={allRows.length === 0}>
          <summary>{allRows.length ? "Upload more applications" : "Upload applications"}</summary>
          {uploadBody}
        </details>
      )}
    </>
  );
}
