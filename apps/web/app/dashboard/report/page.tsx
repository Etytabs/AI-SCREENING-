"use client";

import { useEffect, useState } from "react";
import { NoCallSelected, Notice, PageHeader, SignalBadge, StatusBadge } from "../../../components/workflow/ui";
import { useWorkspace } from "../../../components/workflow/WorkspaceContext";
import { ApiError } from "../../../lib/api";
import { ACTION_LABELS, CATEGORY_LABELS, FINDING_TYPE_LABELS, formatAmount, formatDate, REVIEW_STATE_LABELS } from "../../../lib/labels";
import type { ScreeningReport } from "../../../lib/types";

export default function ReportPage() {
  const { client, callId, callsState } = useWorkspace();
  const [report, setReport] = useState<ScreeningReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!callId) return;
    setReport(null);
    client.report(callId).then(setReport).catch((e) => setError(e instanceof ApiError ? e.message : "Unable to build the report."));
  }, [client, callId]);

  return (
    <>
      <PageHeader
        eyebrow="GRANT SCREENING / REPORT"
        title="Screening report"
        intro="A record of the verified requirements, AI screening signals and reviewer decisions for the selected call."
        actions={report ? <button className="ghost-button no-print" onClick={() => window.print()}>Print / save as PDF</button> : undefined}
      />
      {callsState === "ready" && !callId && <NoCallSelected />}
      {error && <Notice kind="error" title="Report unavailable">{error}</Notice>}
      {callId && !report && !error && <Notice kind="loading" title="Building report…" />}

      {report && (
        <article className="report">
          {report.synthetic_notice && <Notice kind="review" title="Synthetic demonstration data">{report.synthetic_notice}</Notice>}
          <section className="panel">
            <h2>{report.grant_call.name}</h2>
            <dl className="summary-table">
              <dt>Organization</dt><dd>{report.grant_call.organization}</dd>
              <dt>Reference</dt><dd>{report.grant_call.reference ?? "—"}</dd>
              <dt>Generated</dt><dd>{formatDate(report.generated_at)}</dd>
              <dt>Applications</dt><dd>{report.summary.applications_total}</dd>
              <dt>Findings</dt><dd>{report.summary.findings_total} total · {report.summary.findings_reviewed} with a reviewer decision · {report.summary.findings_pending_review} awaiting review</dd>
            </dl>
          </section>

          <section className="panel">
            <h2>Verified requirements ({report.requirements.length})</h2>
            <table className="data-table">
              <thead><tr><th>Code</th><th>Category</th><th>Requirement</th><th>Source</th></tr></thead>
              <tbody>
                {report.requirements.map((r) => (
                  <tr key={r.id}>
                    <td>{r.criterion_code}</td>
                    <td>{CATEGORY_LABELS[r.category]}</td>
                    <td>{r.requirement_text}</td>
                    <td className="small">{r.citation_locator ?? (r.source_type === "administrator" ? "Added by administrator" : "—")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          {report.applications.map(({ row, findings }) => (
            <section className="panel report-application" key={row.id}>
              <h2>{row.application_reference} · {row.title ?? "Untitled"}</h2>
              <p className="muted small">
                {[row.applicant_name, row.institution_name, row.country].filter(Boolean).join(" · ") || "Applicant not stated"} · Requested {formatAmount(row.requested_amount, row.currency)} · Screening {row.screening_status.replace(/_/g, " ").toLowerCase()}
              </p>
              {findings.length === 0 ? (
                <p className="muted">Not screened.</p>
              ) : (
                <table className="data-table">
                  <thead><tr><th>Check</th><th>Finding</th><th>AI result</th><th>Evidence</th><th>Reviewer</th></tr></thead>
                  <tbody>
                    {findings.map((f) => {
                      const last = f.decisions[f.decisions.length - 1];
                      return (
                        <tr key={f.finding_id}>
                          <td>{FINDING_TYPE_LABELS[f.type]}</td>
                          <td><b>{f.title}</b><small className="muted">{f.explanation}</small></td>
                          <td>{f.type === "eligibility" || f.type === "completeness" ? <StatusBadge status={f.status} /> : <SignalBadge signal={f.signal} />}</td>
                          <td className="nowrap">{f.evidence_count} items · {f.valid_citations} verified citations</td>
                          <td>
                            {REVIEW_STATE_LABELS[f.review_state]}
                            {last && <small className="muted">{ACTION_LABELS[last.action]} by {last.reviewer_id}: “{last.note}”</small>}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </section>
          ))}

          <p className="disclaimer">{report.disclaimer}</p>
        </article>
      )}
    </>
  );
}
