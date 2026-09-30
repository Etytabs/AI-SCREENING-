"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { DashboardSummaryView } from "../../components/workflow/DashboardSummaryView";
import { NoCallSelected, Notice, PageHeader } from "../../components/workflow/ui";
import { useWorkspace } from "../../components/workflow/WorkspaceContext";
import { ApiError } from "../../lib/api";
import type { DashboardSummary, Role } from "../../lib/types";

const roleContent: Record<Exclude<Role, "NCST_GRANT_PERSONNEL">, { eyebrow: string; title: string; intro: string; actions: { href: string; label: string; description: string }[] }> = {
  GRANT_INSTITUTION: {
    eyebrow: "GRANT INSTITUTION / WORKSPACE",
    title: "Submission workspace",
    intro: "Prepare stronger submissions, check call requirements and follow the evidence available for your institution.",
    actions: [
      { href: "/dashboard/calls", label: "Funding calls", description: "Explore active calls, eligibility requirements and deadlines." },
      { href: "/dashboard/applications", label: "My submissions", description: "Review submitted applications, documents and screening status." },
      { href: "/dashboard/check", label: "Submission check", description: "Check research topics and proposal signals before submission." },
      { href: "/dashboard/publications", label: "Research outputs", description: "Review publication records and reconciliation signals." },
    ],
  },
  RESEARCHER_APPLICANT: {
    eyebrow: "RESEARCHER / APPLICANT / WORKSPACE",
    title: "Research workspace",
    intro: "Find relevant funding, validate a research idea and understand evidence before you submit.",
    actions: [
      { href: "/dashboard/calls", label: "Find funding", description: "Explore available research calls and their requirements." },
      { href: "/dashboard/check", label: "Research check", description: "Check a research topic for related work and similarity signals." },
      { href: "/dashboard/applications", label: "My applications", description: "Track proposal documents, status and available screening feedback." },
      { href: "/dashboard/publications", label: "My publications", description: "Review research outputs and publication reconciliation." },
    ],
  },
};

function RoleWorkspace({ role }: { role: Exclude<Role, "NCST_GRANT_PERSONNEL"> }) {
  const content = roleContent[role];
  return (
    <>
      <PageHeader eyebrow={content.eyebrow} title={content.title} intro={content.intro} />
      <section className="role-focus-grid" aria-label={`${content.title} actions`}>
        {content.actions.map((action) => (
          <Link key={action.href} href={action.href} className="role-focus-card">
            <span className="role-focus-arrow">→</span>
            <b>{action.label}</b>
            <p>{action.description}</p>
          </Link>
        ))}
      </section>
      <Notice kind="info" title="Demo workspace">This view uses the same evidence-centered platform, with navigation and primary tasks adapted to the selected stakeholder.</Notice>
    </>
  );
}

export default function OverviewPage() {
  const { client, callId, callsState, callsError, role } = useWorkspace();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!callId) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const load = async () => {
      try {
        const data = await client.dashboard(callId);
        if (cancelled) return;
        setSummary(data);
        setError(null);
        if (data.latest_batch && data.latest_batch.finished < data.latest_batch.total) timer = setTimeout(load, 2000);
      } catch (e) {
        if (!cancelled) setError(e instanceof ApiError ? e.message : "Unable to load the dashboard.");
      }
    };
    setSummary(null);
    load();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [client, callId]);

  return (
    <>
      <PageHeader
        eyebrow="GRANT SCREENING / OVERVIEW"
        title="Call overview"
        intro="Where the selected call stands: requirements, submissions, screening signals and human review."
        actions={callId ? <Link className="ghost-button" href="/dashboard/report">Open report</Link> : undefined}
      />
      {callsState === "loading" && <Notice kind="loading" title="Loading grant calls…" />}
      {callsState === "error" && <Notice kind="error" title="Grant calls unavailable">{callsError}</Notice>}
      {callsState === "ready" && !callId && <NoCallSelected />}
      {error && <Notice kind="error" title="Dashboard unavailable">{error}</Notice>}
      {callId && !summary && !error && <Notice kind="loading" title="Loading dashboard…" />}
      {summary && <DashboardSummaryView summary={summary} />}
    </>
  );
}
