"use client";

import { FINDING_TYPE_LABELS, REVIEW_STATE_LABELS } from "../../lib/labels";
import type { Finding, FindingType } from "../../lib/types";
import { SignalBadge, StatusBadge } from "./ui";

const ORDER: FindingType[] = ["eligibility", "completeness", "duplication", "plagiarism", "novelty"];

export function FindingList({ findings, selectedId, onSelect }: { findings: Finding[]; selectedId: string | null; onSelect: (f: Finding) => void }) {
  if (!findings.length) return <p className="muted">No findings for this run.</p>;
  return (
    <div className="finding-groups">
      {ORDER.filter((type) => findings.some((f) => f.type === type)).map((type) => {
        const group = findings.filter((f) => f.type === type);
        return (
          <section key={type} className="finding-group" aria-label={FINDING_TYPE_LABELS[type]}>
            <h3>{FINDING_TYPE_LABELS[type]} <small>{group.length}</small></h3>
            <ul>
              {group.map((f) => (
                <li key={f.finding_id}>
                  <button
                    className={`finding-row${selectedId === f.finding_id ? " selected" : ""}`}
                    onClick={() => onSelect(f)}
                    aria-pressed={selectedId === f.finding_id}
                    data-testid={`finding-${f.finding_id}`}
                  >
                    <span className="finding-row-title">{f.title}</span>
                    <span className="finding-row-status">
                      {f.signal && f.type !== "eligibility" && f.type !== "completeness" ? <SignalBadge signal={f.signal} /> : <StatusBadge status={f.status} />}
                    </span>
                    <small>{f.explanation}</small>
                    <small className={`review-state rs-${f.review_state.toLowerCase()}`}>{REVIEW_STATE_LABELS[f.review_state]}</small>
                  </button>
                </li>
              ))}
            </ul>
          </section>
        );
      })}
    </div>
  );
}
