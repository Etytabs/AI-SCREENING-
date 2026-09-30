"use client";

import Link from "next/link";
import { formatAmount, SIGNAL_LABELS } from "../../lib/labels";
import type { DashboardSummary } from "../../lib/types";
import { CallStatusBadge, Notice, StatusBadge } from "./ui";

function CountRow({ label, counts, order }: { label: string; counts: Record<string, number>; order: string[] }) {
  return (
    <tr>
      <th scope="row">{label}</th>
      {order.map((key) => (
        <td key={key}>
          <b>{counts[key] ?? 0}</b>
          <span>{key === "REVIEW_REQUIRED" ? "review required" : (SIGNAL_LABELS[key] ?? key).toLowerCase()}</span>
        </td>
      ))}
    </tr>
  );
}

export function DashboardSummaryView({ summary }: { summary: DashboardSummary }) {
  const call = summary.grant_call;
  const batch = summary.latest_batch;
  const unavailable = summary.sources.filter((s) => s.access_status !== "AVAILABLE");
  const steps = [
    {
      label: "Requirements",
      value: `${summary.requirements_confirmed} of ${summary.requirements_total} confirmed`,
      done: call.status !== "DRAFT" && call.status !== "REQUIREMENTS_PENDING",
      href: `/dashboard/calls?id=${call.id}`,
    },
    { label: "Applications", value: `${summary.applications_total} uploaded`, done: summary.applications_total > 0, href: "/dashboard/applications" },
    {
      label: "Screening",
      value: batch ? `${batch.finished} of ${batch.total} runs finished` : "Not started",
      done: !!batch && batch.finished === batch.total,
      href: "/dashboard/screening",
    },
    {
      label: "Review",
      value: `${summary.findings_pending_review} findings awaiting a reviewer`,
      done: summary.findings_total > 0 && summary.findings_pending_review === 0,
      href: "/dashboard/review",
    },
    { label: "Report", value: "Screening report", done: false, href: "/dashboard/report" },
  ];

  return (
    <div className="overview">
      <section className="call-summary" aria-label="Grant call">
        <div>
          <CallStatusBadge status={call.status} />
          <h2>{call.name}</h2>
          <p>{call.organization}{call.reference ? ` · ${call.reference}` : ""}</p>
        </div>
        <dl>
          <dt>Funding</dt>
          <dd>{call.funding_max ? `${formatAmount(call.funding_min, call.currency)} – ${formatAmount(call.funding_max, call.currency)}` : "Not set"}</dd>
          <dt>Window</dt>
          <dd>{call.open_date ?? "—"} to {call.close_date ?? "—"}</dd>
        </dl>
      </section>

      <ol className="workflow-steps" aria-label="Workflow progress">
        {steps.map((step, index) => (
          <li key={step.label} className={step.done ? "done" : ""}>
            <Link href={step.href}>
              <span className="step-index" aria-hidden="true">{step.done ? "✓" : index + 1}</span>
              <b>{step.label}</b>
              <small>{step.value}</small>
            </Link>
          </li>
        ))}
      </ol>

      {batch && batch.finished < batch.total && (
        <Notice kind="processing" title="Screening in progress">
          {batch.finished} of {batch.total} applications finished. <Link href="/dashboard/screening">View stage progress</Link>.
        </Notice>
      )}
      {batch && batch.status === "PARTIAL" && (
        <Notice kind="partial" title="Some screening runs are partial">
          At least one stage could not complete. Affected checks are marked REVIEW REQUIRED.
        </Notice>
      )}

      <section className="summary-table-wrap" aria-label="Screening summary">
        <div className="eyebrow">SCREENING SIGNALS · {summary.applications_total} APPLICATIONS</div>
        {summary.applications_total === 0 ? (
          <Notice kind="empty" title="No applications yet">
            <Link href="/dashboard/applications">Upload applications</Link> once the requirements are confirmed.
          </Notice>
        ) : (
          <table className="summary-table">
            <tbody>
              <CountRow label="Eligibility" counts={summary.eligibility_counts} order={["PASS", "FAIL", "REVIEW_REQUIRED", "NOT_SCREENED"]} />
              <CountRow label="Completeness" counts={summary.completeness_counts} order={["PASS", "FAIL", "REVIEW_REQUIRED", "NOT_SCREENED"]} />
              <CountRow label="Novelty signal" counts={summary.novelty_counts} order={["HIGH", "MEDIUM", "LOW", "REVIEW_REQUIRED"]} />
              <tr>
                <th scope="row">Similarity</th>
                <td><b>{summary.duplication_flags}</b><span>possible duplication</span></td>
                <td><b>{summary.text_similarity_flags}</b><span>shared passages</span></td>
                <td><b>{summary.findings_reviewed}</b><span>findings reviewed</span></td>
                <td><b>{summary.applications_review_complete}</b><span>applications fully reviewed</span></td>
              </tr>
            </tbody>
          </table>
        )}
      </section>

      <section className="coverage" aria-label="Source coverage">
        <div className="eyebrow">SOURCE COVERAGE</div>
        <ul>
          {summary.sources.filter((s) => s.access_status === "AVAILABLE").map((s) => (
            <li key={s.source_id}><StatusBadge status="AVAILABLE" /> {s.source_name}</li>
          ))}
        </ul>
        {unavailable.length > 0 && (
          <p className="muted">
            Not searched ({unavailable.length}): {unavailable.map((s) => s.source_name).join(", ")}. An unsearched source is not
            evidence of absence. <Link href="/dashboard/sources">Source details</Link>
          </p>
        )}
      </section>

      <p className="disclaimer">{summary.disclaimer}</p>
    </div>
  );
}
