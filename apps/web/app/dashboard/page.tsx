"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { DashboardSummaryView } from "../../components/workflow/DashboardSummaryView";
import { NoCallSelected, Notice, PageHeader } from "../../components/workflow/ui";
import { useWorkspace } from "../../components/workflow/WorkspaceContext";
import { ApiError } from "../../lib/api";
import type { DashboardSummary } from "../../lib/types";

export default function OverviewPage() {
  const { client, callId, callsState, callsError } = useWorkspace();
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
