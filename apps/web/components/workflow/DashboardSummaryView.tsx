"use client";

import Link from "next/link";
import { formatAmount } from "../../lib/labels";

function compactAmount(value: number | null | undefined, currency: string | null) {
  if (value == null) return "Not set";
  const unit = currency ?? "RWF";
  if (value >= 1000000) return `${unit} ${(value / 1000000).toLocaleString(undefined, { maximumFractionDigits: 1 })}M`;
  if (value >= 1000) return `${unit} ${(value / 1000).toLocaleString(undefined, { maximumFractionDigits: 0 })}K`;
  return `${unit} ${value.toLocaleString()}`;
}

function dateLabel(value: string | null | undefined) {
  if (!value) return "—";
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric" }).format(date);
}

import type { DashboardSummary } from "../../lib/types";
import { CallStatusBadge, Notice, StatusBadge } from "./ui";
import { StakeholderOverview } from "./StakeholderOverview";

export function DashboardSummaryView({ summary }: { summary: DashboardSummary }) {
  const call = summary.grant_call;
  const batch = summary.latest_batch;
  const unavailable = summary.sources.filter((s) => s.access_status !== "AVAILABLE");
  const reportReady = summary.findings_pending_review === 0 && summary.applications_review_complete === summary.applications_total && summary.applications_total > 0;
  const currentStep = summary.requirements_confirmed < summary.requirements_total || call.status === "REQUIREMENTS_PENDING" ? 0 : summary.applications_total === 0 ? 1 : !batch || batch.finished < batch.total ? 2 : !reportReady ? 3 : 4;
  const steps = [
    {
      label: "Requirements",
      value: `${summary.requirements_confirmed} of ${summary.requirements_total} confirmed`,
      done: currentStep > 0,
      href: `/dashboard/calls?id=${call.id}`,
    },
    { label: "Applications", value: `${summary.applications_total} uploaded`, done: currentStep > 1, href: "/dashboard/applications" },
    {
      label: "Screening",
      value: batch ? `${batch.finished} of ${batch.total} runs finished` : "Not started",
      done: currentStep > 2,
      href: "/dashboard/screening",
    },
    {
      label: "Review",
      value: currentStep === 3 ? "Current review stage" : "Human review",
      done: currentStep > 3,
      href: "/dashboard/review",
    },
    { label: "Report", value: reportReady ? "Ready to open" : "Available after review", done: reportReady, href: "/dashboard/report" },
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
          <dd title={call.funding_max ? `${formatAmount(call.funding_min, call.currency)} – ${formatAmount(call.funding_max, call.currency)}` : "Not set"}>{call.funding_max ? `${compactAmount(call.funding_min, call.currency)} – ${compactAmount(call.funding_max, call.currency).replace(`${call.currency} `, "")}` : "Not set"}</dd>
          <dt>Window</dt>
          <dd>{dateLabel(call.open_date)} – {dateLabel(call.close_date)}</dd>
        </dl>
      </section>

      <ol className="workflow-steps" aria-label="Workflow progress">
        {steps.map((step, index) => (
          <li key={step.label} className={`${step.done ? "done " : ""}${index === currentStep ? "current" : ""}`}>
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

      <section className="attention-grid" aria-label="Administrator attention">
        <div className="attention-card attention-review">
          <span className="attention-icon" aria-hidden="true">!</span>
          <div>
            <b>Review queue</b>
            <strong>{summary.findings_pending_review}</strong>
            <span>findings need human review</span>
          </div>
          <Link href="/dashboard/review">Open review →</Link>
        </div>
        <div className="attention-card attention-screening">
          <span className="attention-icon" aria-hidden="true">◫</span>
          <div>
            <b>Screening coverage</b>
            <strong>{batch ? `${batch.finished}/${batch.total}` : "—"}</strong>
            <span>applications with completed runs</span>\n            {batch && batch.total > 0 && <span className="attention-progress"><span style={{ width: `${Math.min(100, Math.round((batch.finished / batch.total) * 100))}%` }} /></span>}
          </div>
          <Link href="/dashboard/screening">Inspect runs →</Link>
        </div>
        <div className="attention-card attention-evidence">
          <span className="attention-icon" aria-hidden="true">◉</span>
          <div>
            <b>Evidence signals</b>
            <strong>{summary.duplication_flags + summary.text_similarity_flags}</strong>
            <span>{summary.duplication_flags} possible overlaps · {summary.text_similarity_flags} shared passages</span>
          </div>
          <Link href="/dashboard/review">Inspect evidence →</Link>
        </div>
      </section>

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

      <StakeholderOverview />

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
