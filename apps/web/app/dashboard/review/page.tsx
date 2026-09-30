"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { NoCallSelected, Notice, PageHeader, SignalBadge, StatusBadge } from "../../../components/workflow/ui";
import { useWorkspace } from "../../../components/workflow/WorkspaceContext";
import { ApiError } from "../../../lib/api";
import { FINDING_TYPE_LABELS, formatDate, humanize, REVIEW_STATE_LABELS } from "../../../lib/labels";
import type { AuditLogEntry, ReviewState, ScreeningReport } from "../../../lib/types";

const OPEN_STATES: ReviewState[] = ["PENDING", "REVIEW_REQUESTED", "ESCALATED"];

function detailSummary(details: Record<string, unknown>): string {
  return Object.entries(details)
    .filter(([key, value]) => key !== "grant_call_id" && value !== null && value !== "" && typeof value !== "object")
    .map(([key, value]) => `${humanize(key)}: ${String(value)}`)
    .join(" · ");
}

export default function ReviewPage() {
  const { client, callId, callsState } = useWorkspace();
  const [report, setReport] = useState<ScreeningReport | null>(null);
  const [audit, setAudit] = useState<AuditLogEntry[] | null>(null);
  const [auditError, setAuditError] = useState<{ status: number; message: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [scope, setScope] = useState<"open" | "all">("open");

  const load = useCallback(async () => {
    if (!callId) return;
    setReport(null);
    setAudit(null);
    setAuditError(null);
    try {
      setReport(await client.report(callId));
      setError(null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Unable to load findings.");
    }
    try {
      setAudit(await client.audit(callId));
    } catch (e) {
      setAuditError(e instanceof ApiError ? { status: e.status, message: e.message } : { status: 0, message: "Unable to load the audit trail." });
    }
  }, [client, callId]);

  useEffect(() => { load(); }, [load]);

  const queue = useMemo(() => {
    if (!report) return [];
    return report.applications.flatMap(({ row, findings }) =>
      findings
        .filter((f) => scope === "all" || (f.status !== "PASS" && OPEN_STATES.includes(f.review_state)))
        .map((f) => ({ row, finding: f })),
    );
  }, [report, scope]);

  return (
    <>
      <PageHeader
        eyebrow="GRANT SCREENING / REVIEW"
        title="Human review"
        intro="Every flagged finding needs a reviewer decision with a rationale. The system never confirms a finding on its own."
        actions={<Link className="ghost-button" href="/dashboard/review/legacy">Open legacy screening workspace</Link>}
      />
      {callsState === "ready" && !callId && <NoCallSelected />}
      {error && <Notice kind="error" title="Findings unavailable">{error}</Notice>}
      {callId && !report && !error && <Notice kind="loading" title="Loading review queue…" />}

      {report && (
        <section className="panel">
          <div className="panel-head">
            <h2>Review queue</h2>
            <div className="segmented" role="group" aria-label="Queue scope">
              <button aria-pressed={scope === "open"} className={scope === "open" ? "active" : ""} onClick={() => setScope("open")}>Needs decision</button>
              <button aria-pressed={scope === "all"} className={scope === "all" ? "active" : ""} onClick={() => setScope("all")}>All findings</button>
            </div>
          </div>
          {queue.length === 0 ? (
            <Notice kind={scope === "open" && report.summary.findings_total ? "success" : "empty"} title={scope === "open" && report.summary.findings_total ? "No findings awaiting a decision" : "No findings yet"}>
              {report.summary.findings_total ? "All flagged findings have a reviewer decision." : <><Link href="/dashboard/screening">Run screening</Link> to generate findings.</>}
            </Notice>
          ) : (
            <table className="data-table results-table">
              <thead><tr><th>Application</th><th>Check</th><th>Finding</th><th>AI result</th><th>Review state</th><th /></tr></thead>
              <tbody>
                {queue.map(({ row, finding }) => (
                  <tr key={finding.finding_id}>
                    <td data-label="Application"><b>{row.application_reference}</b></td>
                    <td data-label="Check">{FINDING_TYPE_LABELS[finding.type]}</td>
                    <td data-label="Finding">{finding.title}</td>
                    <td data-label="AI result">{finding.type === "eligibility" || finding.type === "completeness" ? <StatusBadge status={finding.status} /> : <SignalBadge signal={finding.signal} />}</td>
                    <td data-label="Review state">{REVIEW_STATE_LABELS[finding.review_state]}</td>
                    <td><Link href={`/dashboard/applications/view?id=${row.id}&finding=${finding.finding_id}`}>Review →</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {callId && (
        <section className="panel">
          <h2>Audit trail</h2>
          {auditError?.status === 403 && <Notice kind="info" title="Restricted">The audit trail is available to Grant and System Administrators.</Notice>}
          {auditError && auditError.status !== 403 && <Notice kind="error" title="Audit trail unavailable">{auditError.message}</Notice>}
          {!audit && !auditError && <Notice kind="loading" title="Loading audit trail…" />}
          {audit && audit.length === 0 && <Notice kind="empty" title="No audit events yet" />}
          {audit && audit.length > 0 && (
            <table className="data-table audit-table">
              <thead><tr><th>Time</th><th>Event</th><th>Actor</th><th>Details</th></tr></thead>
              <tbody>
                {audit.slice(0, 200).map((entry, i) => (
                  <tr key={`${entry.timestamp}-${i}`}>
                    <td className="nowrap">{formatDate(entry.timestamp)}</td>
                    <td>{humanize(entry.event_type)}</td>
                    <td>{entry.actor}</td>
                    <td className="small">{detailSummary(entry.details) || entry.entity_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {audit && audit.length > 200 && <p className="muted small">Showing the 200 most recent of {audit.length} events.</p>}
        </section>
      )}
    </>
  );
}
