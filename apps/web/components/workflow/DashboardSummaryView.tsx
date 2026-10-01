"use client";

import Link from "next/link";
import { formatAmount, formatDate } from "../../lib/labels";

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
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
      }).format(date);
}

import type { DashboardSummary, RecordedDecision } from "../../lib/types";
import { CallStatusBadge, Notice } from "./ui";

const DECISION_LABELS: Record<string, string> = { CONFIRMED: "Confirmed", DISMISSED: "Dismissed" };

/** Where a reviewer's recorded decision is kept and shown for the whole call. */
function DecisionLog({ decisions }: { decisions: RecordedDecision[] }) {
  return (
    <section className="drawer-section decision-log" aria-label="Human decisions">
      <h3>Human decisions ({decisions.length})</h3>
      {decisions.length === 0 ? (
        <p className="muted">
          No reviewer decision has been recorded yet. Confirming or dismissing a finding records it here.
        </p>
      ) : (
        <ul className="decision-log-list">
          {decisions.map((d) => (
            <li key={d.decision_id}>
              <div className="evidence-meta">
                <b>{d.document_name ?? d.application_reference}</b>
                <span className={`decision-state ds-${d.review_state.toLowerCase()}`}>
                  {DECISION_LABELS[d.review_state] ?? d.review_state}
                </span>
              </div>
              <small>{[d.application_reference, d.finding_title, formatDate(d.created_at), d.reviewer_id].filter(Boolean).join(" · ")}</small>
              <p className="small">{d.note}</p>
              <Link className="text-button" href={`/dashboard/applications/view?id=${d.application_id}&finding=${d.finding_id}`}>
                Open the finding
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function DashboardSummaryView({ summary }: { summary: DashboardSummary }) {
  const call = summary.grant_call;
  const batch = summary.latest_batch;
  // Four numbers an administrator acts on; the per-check breakdown lives on Applications,
  // which is also where a finding is opened and reviewed.
  const headline = [
    { value: summary.applications_total, label: "applications", href: "/dashboard/applications" },
    { value: summary.eligibility_counts.PASS ?? 0, label: "eligible", href: "/dashboard/applications" },
    { value: summary.completeness_counts.FAIL ?? 0, label: "incomplete", href: "/dashboard/applications" },
    { value: summary.findings_pending_review, label: "awaiting review", href: "/dashboard/applications" },
  ];
  const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;
  const reviewed = summary.applications_total > 0
    && summary.applications_review_complete === summary.applications_total;

  const currentStep =
    summary.requirements_confirmed < summary.requirements_total
      ? 0
      : summary.applications_total === 0
        ? 1
        : !batch || batch.finished < batch.total
          ? 2
          : summary.findings_pending_review > 0
            ? 3
            : reviewed
              ? 4
              : 3;

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
      value: batch ? `${batch.finished} of ${plural(batch.total, "run")} finished` : "Not started",
      done: !!batch && batch.finished === batch.total,
      href: "/dashboard/screening",
    },
    {
      label: "Review",
      value: `${plural(summary.findings_pending_review, "finding")} awaiting a reviewer`,
      done: summary.findings_total > 0 && summary.findings_pending_review === 0,
      href: "/dashboard/applications",
    },
    {
      label: "Report",
      value: summary.findings_total
        ? `${plural(summary.findings_total, "finding")} across ${plural(summary.applications_total, "application")}`
        : "Nothing screened yet",
      done: reviewed,
      href: "/dashboard/report",
    },
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

      {summary.applications_total === 0 ? (
        <Notice kind="empty" title="No applications yet">
          <Link href="/dashboard/applications">Upload applications</Link> once the requirements are confirmed.
        </Notice>
      ) : (
        <ul className="headline-stats" aria-label="Screening summary">
          {headline.map((stat) => (
            <li key={stat.label}>
              <Link href={stat.href}>
                <b>{stat.value}</b>
                <span>{stat.label}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}

      <DecisionLog decisions={summary.decisions ?? []} />

      <p className="disclaimer">{summary.disclaimer}</p>
    </div>
  );
}
