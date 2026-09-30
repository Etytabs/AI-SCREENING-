"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { formatAmount } from "../../lib/labels";
import type { ApplicationRow } from "../../lib/types";
import { SignalBadge, StatusBadge, SyntheticBadge } from "./ui";

export interface ResultFilters {
  q?: string;
  eligibility?: string;
  completeness?: string;
  novelty?: string;
  review_progress?: string;
  flagged?: string;
}

type SortKey = "application_reference" | "eligibility" | "completeness" | "open_findings" | "requested_amount";
const RANK: Record<string, number> = { FAIL: 0, REVIEW_REQUIRED: 1, PASS: 2, NOT_SCREENED: 3 };

function compare(a: ApplicationRow, b: ApplicationRow, key: SortKey): number {
  if (key === "eligibility" || key === "completeness") return (RANK[a[key]] ?? 9) - (RANK[b[key]] ?? 9);
  if (key === "open_findings") return b.open_findings - a.open_findings;
  if (key === "requested_amount") return (b.requested_amount ?? -1) - (a.requested_amount ?? -1);
  return a.application_reference.localeCompare(b.application_reference);
}

interface Props {
  rows: ApplicationRow[];
  filters: ResultFilters;
  onFiltersChange: (filters: ResultFilters) => void;
}

const REVIEW_TEXT: Record<ApplicationRow["review_progress"], string> = {
  NOT_SCREENED: "Not screened",
  PENDING: "Not started",
  IN_PROGRESS: "In progress",
  COMPLETE: "Complete",
};

export function ResultsTable({ rows, filters, onFiltersChange }: Props) {
  const [sort, setSort] = useState<SortKey>("application_reference");
  const sorted = useMemo(() => [...rows].sort((a, b) => compare(a, b, sort)), [rows, sort]);
  const set = (key: keyof ResultFilters) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    onFiltersChange({ ...filters, [key]: e.target.value || undefined });

  return (
    <section className="results" aria-label="Application results">
      <div className="filters">
        <input type="search" placeholder="Search reference, title, applicant, institution" value={filters.q ?? ""} onChange={set("q")} aria-label="Search applications" />
        <select value={filters.eligibility ?? ""} onChange={set("eligibility")} aria-label="Filter by eligibility">
          <option value="">Eligibility: all</option><option value="PASS">Pass</option><option value="FAIL">Fail</option><option value="REVIEW_REQUIRED">Review required</option><option value="NOT_SCREENED">Not screened</option>
        </select>
        <select value={filters.completeness ?? ""} onChange={set("completeness")} aria-label="Filter by completeness">
          <option value="">Completeness: all</option><option value="PASS">Pass</option><option value="FAIL">Fail</option><option value="REVIEW_REQUIRED">Review required</option>
        </select>
        <select value={filters.novelty ?? ""} onChange={set("novelty")} aria-label="Filter by novelty signal">
          <option value="">Novelty: all</option><option value="HIGH">High signal</option><option value="MEDIUM">Medium signal</option><option value="LOW">Low signal</option><option value="REVIEW_REQUIRED">Review required</option>
        </select>
        <select value={filters.review_progress ?? ""} onChange={set("review_progress")} aria-label="Filter by review progress">
          <option value="">Review: all</option><option value="PENDING">Not started</option><option value="IN_PROGRESS">In progress</option><option value="COMPLETE">Complete</option>
        </select>
        <label className="check"><input type="checkbox" checked={filters.flagged === "true"} onChange={(e) => onFiltersChange({ ...filters, flagged: e.target.checked ? "true" : undefined })} /> Similarity flagged only</label>
        <select value={sort} onChange={(e) => setSort(e.target.value as SortKey)} aria-label="Sort applications">
          <option value="application_reference">Sort: reference</option>
          <option value="eligibility">Sort: eligibility issues first</option>
          <option value="completeness">Sort: completeness issues first</option>
          <option value="open_findings">Sort: most open findings</option>
          <option value="requested_amount">Sort: requested amount</option>
        </select>
      </div>
      {sorted.length === 0 ? (
        <p className="muted empty-row">No applications match these filters.</p>
      ) : (
        <table className="data-table results-table">
          <thead>
            <tr>
              <th>Application</th><th>Requested</th><th>Eligibility</th><th>Completeness</th><th>Similarity signals</th><th>Novelty</th><th>Review</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((row) => (
              <tr key={row.id} data-testid={`row-${row.application_reference}`}>
                <td data-label="Application">
                  <Link href={`/dashboard/applications/view?id=${row.id}`}><b>{row.application_reference}</b></Link> <SyntheticBadge origin={row.data_origin} />
                  <span className="row-title">{row.title ?? "Untitled (no “Title:” field found)"}</span>
                  <small>{[row.applicant_name, row.institution_name, row.country].filter(Boolean).join(" · ") || "Applicant details not stated"}</small>
                  {row.unreadable_documents > 0 && <small className="warn-text">{row.unreadable_documents} unreadable document(s)</small>}
                  {["QUEUED", "RUNNING"].includes(row.screening_status) && <StatusBadge status="PROCESSING" />}
                  {["PARTIAL", "BLOCKED"].includes(row.screening_status) && <StatusBadge status={row.screening_status} />}
                </td>
                <td data-label="Requested">{formatAmount(row.requested_amount, row.currency)}</td>
                <td data-label="Eligibility"><StatusBadge status={row.eligibility} /></td>
                <td data-label="Completeness"><StatusBadge status={row.completeness} /></td>
                <td data-label="Similarity" className="stacked">
                  <span title="Whole-proposal duplication signal"><SignalBadge signal={row.duplication} /></span>
                  <span title="Shared verbatim passages"><SignalBadge signal={row.text_similarity} /></span>
                </td>
                <td data-label="Novelty"><SignalBadge signal={row.novelty} /></td>
                <td data-label="Review">
                  {REVIEW_TEXT[row.review_progress]}
                  {row.total_findings > 0 && <small>{row.open_findings} of {row.total_findings} findings awaiting a decision</small>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
