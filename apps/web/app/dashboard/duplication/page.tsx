"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { DuplicationProjectImport } from "../../../components/workflow/DuplicationProjectImport";
import { Notice, PageHeader, SyntheticBadge } from "../../../components/workflow/ui";
import { useWorkspace } from "../../../components/workflow/WorkspaceContext";
import { DEMO_ROLE_CONFIG } from "../../../lib/demo-roles";
import { formatDate } from "../../../lib/labels";
import type { ArchivedProject, PurposeOverlapResult } from "../../../lib/types";

export default function DuplicationPage() {
  const { client, role } = useWorkspace();
  const [projects, setProjects] = useState<ArchivedProject[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const [query, setQuery] = useState("");
  const [source, setSource] = useState("");
  const [leftText, setLeftText] = useState("");
  const [rightText, setRightText] = useState("");
  const [purposeResult, setPurposeResult] = useState<PurposeOverlapResult | null>(null);
  const [purposeError, setPurposeError] = useState<string | null>(null);
  const [purposeLoading, setPurposeLoading] = useState(false);

  const comparePurposes = async () => {
    setPurposeLoading(true);
    setPurposeError(null);
    setPurposeResult(null);
    try {
      setPurposeResult(await client.comparePurposeOverlap({
        left_text: leftText,
        right_text: rightText,
        left_label: "Project A",
        right_label: "Project B",
      }));
    } catch (cause) {
      setPurposeError(cause instanceof Error ? cause.message : "Purpose comparison failed.");
    } finally {
      setPurposeLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    setProjects(null);
    setError(null);
    client.listDuplicationProjects().then((records) => {
      if (!cancelled) setProjects(records);
    }).catch((cause) => {
      if (!cancelled) setError(cause instanceof Error ? cause.message : "Unable to load comparison projects.");
    });
    return () => { cancelled = true; };
  }, [client, retry]);

  const visible = (projects ?? []).filter((project) =>
    (!source || project.source_type === source) &&
    [project.title, project.reference, project.organization, project.year].filter(Boolean).join(" ").toLowerCase().includes(query.trim().toLowerCase()),
  );

  return (
    <>
      <PageHeader
        eyebrow="GRANT SCREENING / DUPLICATION" title="Duplication check"
        intro="Compare proposals with applications already in the workspace and a library of previously submitted or funded projects. Add historical documents here, then run screening to review potential matches."
        actions={<Link className="ghost-button" href="/dashboard/screening">Screen applications</Link>}
      />
      <Notice kind="info" title="Comparison coverage">
        The library is shared across grant calls. Results cover readable projects available to the checker at the time of screening. A result with no significant similarity does not establish that a proposal is original. Reviewers confirm any duplication finding from the matched passages.
      </Notice>
      <section className="panel" aria-labelledby="purpose-overlap-heading">
        <div className="panel-head"><h2 id="purpose-overlap-heading">Purpose-overlap comparison</h2></div>
        <p className="muted small">Compare structured project narrative dimensions separately from textual duplication or plagiarism.</p>
        <div className="filters">
          <textarea aria-label="Project A narrative" placeholder="Paste Project A purpose, objectives, beneficiaries, intervention, methodology, outputs, outcomes and scope" value={leftText} onChange={(event) => setLeftText(event.target.value)} />
          <textarea aria-label="Project B narrative" placeholder="Paste Project B purpose, objectives, beneficiaries, intervention, methodology, outputs, outcomes and scope" value={rightText} onChange={(event) => setRightText(event.target.value)} />
        </div>
        <button className="primary-button" type="button" disabled={purposeLoading || leftText.trim().length < 40 || rightText.trim().length < 40} onClick={() => void comparePurposes()}>
          {purposeLoading ? "Comparing…" : "Compare purpose"}
        </button>
        {purposeError && <Notice kind="error" title="Purpose comparison unavailable">{purposeError}</Notice>}
        {purposeResult && (
          <div className="purpose-result">
            <Notice kind="review" title={purposeResult.disposition.replace(/_/g, " ")}>
              {purposeResult.summary}
              <div className="muted small">{purposeResult.disclaimer}</div>
            </Notice>
            <table className="data-table results-table">
              <thead><tr><th>Dimension</th><th>Status</th><th>Similarity</th></tr></thead>
              <tbody>{purposeResult.dimensions.map((item) => (
                <tr key={item.dimension}>
                  <td data-label="Dimension">{item.dimension.replace(/_/g, " ")}</td>
                  <td data-label="Status">{item.status.replace(/_/g, " ")}</td>
                  <td data-label="Similarity">{item.similarity.toFixed(2)}</td>
                </tr>
              ))}</tbody>
            </table>
            {purposeResult.limitations.map((item) => <p className="muted small" key={item}>{item}</p>)}
          </div>
        )}
      </section>
      <section className="panel" aria-labelledby="comparison-library-heading">
        <div className="panel-head"><h2 id="comparison-library-heading">Comparison library{projects && ` (${projects.length})`}</h2></div>
        <p className="muted small">Imported historical records appear below. Other submitted applications in the workspace are compared automatically during screening.</p>
        {error && <Notice kind="error" title="Comparison library unavailable">{error} <button type="button" className="text-button" onClick={() => setRetry((value) => value + 1)}>Retry</button></Notice>}
        {!projects && !error && <Notice kind="loading" title="Loading comparison projects…" />}
        {projects && projects.length === 0 && <Notice kind="empty" title="No historical projects imported">Add previously submitted proposals and funded projects to expand comparison coverage.</Notice>}
        {projects && projects.length > 0 && (
          <>
            <div className="filters">
              <input type="search" aria-label="Search comparison projects" placeholder="Search title, reference or organization" value={query} onChange={(event) => setQuery(event.target.value)} />
              <select aria-label="Filter project source" value={source} onChange={(event) => setSource(event.target.value)}>
                <option value="">All project sources</option><option value="historical_application">Previously submitted</option><option value="funded_project">Funded projects</option>
              </select>
            </div>
            <div className="results">
              <table className="data-table results-table">
                <thead><tr><th>Project</th><th>Source</th><th>Organization</th><th>Document</th><th>Added</th></tr></thead>
                <tbody>{visible.map((project) => (
                  <tr key={project.id}>
                    <td data-label="Project"><b>{project.title}</b><small>{[project.reference, project.year].filter(Boolean).join(" · ") || "No reference or year"}</small><SyntheticBadge origin={project.data_origin} /></td>
                    <td data-label="Source">{project.source_type === "funded_project" ? "Funded project" : "Previously submitted proposal"}</td>
                    <td data-label="Organization">{project.organization || "Not provided"}</td>
                    <td data-label="Document">{project.filename || "Imported project text"}<small>{project.text_length.toLocaleString()} characters indexed</small></td>
                    <td data-label="Added">{formatDate(project.created_at)}</td>
                  </tr>
                ))}</tbody>
              </table>
              {!visible.length && <p className="empty-row">No projects match these filters.</p>}
            </div>
          </>
        )}
      </section>
      <section className="panel" aria-labelledby="import-project-heading">
        <h2 id="import-project-heading">Add a historical project</h2>
        {!DEMO_ROLE_CONFIG[role].capabilities.canImportComparisonProjects
          ? <Notice kind="info" title="Read-only library">This demo role cannot import comparison projects.</Notice>
          : <DuplicationProjectImport key={role} onImport={client.importDuplicationProject} onImported={(project) => setProjects((current) => current ? [project, ...current] : current)} />}
      </section>
    </>
  );
}
