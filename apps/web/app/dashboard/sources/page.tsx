"use client";

import { useEffect, useState } from "react";
import { Notice, PageHeader, StatusBadge } from "../../../components/workflow/ui";
import { useWorkspace } from "../../../components/workflow/WorkspaceContext";
import { ApiError } from "../../../lib/api";
import { humanize } from "../../../lib/labels";
import type { DataSource } from "../../../lib/types";

export default function SourcesPage() {
  const { client, role } = useWorkspace();
  const [sources, setSources] = useState<DataSource[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    client.sources().then(setSources).catch((e) => setError(e instanceof ApiError ? e.message : "Unable to load sources."));
  }, [client]);

  return (
    <>
      <PageHeader
        eyebrow="GRANT SCREENING / SOURCES"
        title="Data sources"
        intro="Sources the screening pipeline may search. Optional sources that are not configured are reported as not searched; screening never treats them as evidence of absence."
      />
      {role !== "SYSTEM_ADMINISTRATOR" && (
        <Notice kind="info" title="Read-only view">Source configuration is managed by System Administrators through server environment variables; there is no in-app editor and no credentials are handled by this page.</Notice>
      )}
      {error && <Notice kind="error" title="Sources unavailable">{error}</Notice>}
      {!sources && !error && <Notice kind="loading" title="Loading sources…" />}
      {sources && sources.length === 0 && <Notice kind="empty" title="No sources registered" />}
      {sources && sources.length > 0 && (
        <section className="panel">
          <table className="data-table results-table">
            <thead><tr><th>Source</th><th>Provider</th><th>Type</th><th>Access</th><th>Core workflow</th><th>Coverage & method</th></tr></thead>
            <tbody>
              {sources.map((s) => (
                <tr key={s.source_id}>
                  <td data-label="Source"><b>{s.source_name}</b><small className="muted">{s.source_id}</small></td>
                  <td data-label="Provider">{s.provider}</td>
                  <td data-label="Type">{humanize(s.source_type)}</td>
                  <td data-label="Access"><StatusBadge status={s.access_status} /></td>
                  <td data-label="Core workflow">{s.required_for_core_workflow ? "Required" : "Optional"}</td>
                  <td data-label="Coverage" className="small">{[s.coverage, s.methodology].filter(Boolean).join(" · ") || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </>
  );
}
