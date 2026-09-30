"use client";

import Link from "next/link";
import { STAGE_LABELS } from "../../lib/labels";
import type { ApplicationRow, BatchProgress } from "../../lib/types";
import { StatusBadge } from "./ui";

export function ScreeningProgressView({ progress, rows }: { progress: BatchProgress; rows: ApplicationRow[] }) {
  const reference = Object.fromEntries(rows.map((r) => [r.id, r.application_reference]));
  return (
    <div className="progress-view">
      <div className="progress-head">
        <StatusBadge status={progress.status === "RUNNING" ? "PROCESSING" : progress.status} />
        <b>{progress.finished} of {progress.total} application runs finished</b>
      </div>
      <table className="data-table stage-table">
        <thead><tr><th>Stage</th><th>Processed</th><th>Failed</th><th aria-hidden="true" /></tr></thead>
        <tbody>
          {progress.stages.map((s) => (
            <tr key={s.stage}>
              <td>{STAGE_LABELS[s.stage]}</td>
              <td>{s.completed} of {s.total}</td>
              <td>{s.failed ? <span className="warn-text">{s.failed} failed</span> : "—"}</td>
              <td aria-hidden="true"><span className="bar"><span style={{ width: `${s.percent_processed}%` }} /></span></td>
            </tr>
          ))}
        </tbody>
      </table>
      <table className="data-table">
        <thead><tr><th>Application</th><th>Run status</th><th>Current / last stage</th><th /></tr></thead>
        <tbody>
          {progress.runs.map((run) => {
            const current = run.stages.find((s) => s.status === "RUNNING") ?? [...run.stages].reverse().find((s) => s.status !== "PENDING");
            const failed = run.stages.filter((s) => s.status === "FAILED");
            return (
              <tr key={run.id}>
                <td>{reference[run.application_id] ?? run.application_id}</td>
                <td><StatusBadge status={run.status === "RUNNING" ? "PROCESSING" : run.status} /></td>
                <td>
                  {current ? `${STAGE_LABELS[current.stage]}${current.message ? ` · ${current.message}` : ""}` : "Queued"}
                  {failed.length > 0 && <small className="warn-text">Failed: {failed.map((s) => STAGE_LABELS[s.stage]).join(", ")}</small>}
                </td>
                <td><Link href={`/dashboard/applications/view?id=${run.application_id}`}>Open →</Link></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
