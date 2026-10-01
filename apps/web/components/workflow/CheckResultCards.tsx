"use client";

import { duplicationMatches, publishedMatches, publishedSimilarity } from "../../lib/matches";
import type { Finding } from "../../lib/types";
import { SignalBadge, StatusBadge } from "./ui";

/** Presentation only. Every number below is read from the findings the API returned. */

type Tone = "pass" | "review" | "fail" | "neutral" | "accent";

function num(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function eligibilityTone(items: Finding[]): Tone {
  if (items.some((f) => f.status === "FAIL")) return "fail";
  if (items.some((f) => f.status === "REVIEW_REQUIRED")) return "review";
  return items.length ? "pass" : "neutral";
}

function signalTone(finding: Finding | undefined): Tone {
  if (!finding) return "neutral";
  if (finding.status === "PASS") return "pass";
  return finding.status === "FAIL" ? "fail" : "review";
}

function plagiarismTone(finding: Finding | undefined): Tone {
  const band = finding?.details?.band;
  if (band === "HIGH_SIMILARITY") return "fail";
  if (band === "MODERATE_SIMILARITY") return "review";
  if (band === "LOW_SIMILARITY") return "pass";
  return signalTone(finding);
}

function Card({
  title, note, tone, value, unit, meter, badge, summary, onEvidence,
}: {
  title: string;
  note: string;
  tone: Tone;
  value: string | null;
  unit?: string;
  meter: number | null;
  badge: React.ReactNode;
  summary: string;
  onEvidence: (() => void) | null;
}) {
  return (
    <section className={`check-card tone-${tone}`} aria-label={title}>
      <header>
        <h3>{title}</h3>
        <p className="muted small">{note}</p>
      </header>
      <div className="check-metric">
        <strong>
          {value ?? "—"}
          {unit && value !== null && <i>{unit}</i>}
        </strong>
        {badge}
      </div>
      {meter !== null && (
        <div className="check-meter" aria-hidden="true">
          <i style={{ width: `${Math.max(2, Math.min(100, meter))}%` }} />
        </div>
      )}
      <p className="check-summary">{summary}</p>
      {onEvidence && (
        <button type="button" className="text-button check-card-foot" aria-haspopup="dialog" onClick={onEvidence}>
          View evidence →
        </button>
      )}
    </section>
  );
}

export function CheckResultCards({
  findings,
  onOpenEvidence,
}: {
  findings: Finding[];
  onOpenEvidence: (group: Finding[]) => void;
}) {
  const eligibility = findings.filter((f) => f.type === "eligibility");
  const passed = eligibility.filter((f) => f.status === "PASS").length;
  const duplication = findings.filter((f) => f.type === "duplication");
  const plagiarism = findings.filter((f) => f.type === "plagiarism");

  const topDuplication = duplication[0];
  const topPlagiarism = plagiarism[0];
  const eligibilityOpen = eligibility.filter((f) => f.status !== "PASS").length;
  // A duplicate found by the text-similarity check is still a duplicate: count it here.
  const duplicates = duplicationMatches(findings);
  const dupCompared = num(topDuplication?.details?.compared_records);
  // Plagiarism reports published literature only.
  const published = publishedMatches(findings);
  const searchedLiterature = topPlagiarism?.details?.published_literature_searched === true;
  // Nothing matched after a real search is 0%; no search at all has no figure to show.
  const index = publishedSimilarity(findings) ?? (searchedLiterature ? 0 : null);
  const worksCompared = num(topPlagiarism?.details?.published_works_compared);

  return (
    <div className="check-cards">
      <Card
        title="Eligibility"
        note="Checked against the call's verified requirements."
        tone="accent"
        value={eligibility.length ? `${passed} / ${eligibility.length}` : null}
        meter={eligibility.length ? (passed / eligibility.length) * 100 : null}
        badge={<span className={`badge badge-${eligibilityTone(eligibility)}`}>{
          eligibility.length === 0 ? "NOT CHECKED"
            : passed === eligibility.length ? "ALL PASS"
            : passed === 0 ? "NOT MET" : "PARTIAL"
        }</span>}
        summary={
          eligibility.length === 0
            ? "No result for this check."
            : `${passed} of ${eligibility.length} requirements met` +
              (eligibilityOpen ? `, ${eligibilityOpen} to review` : "")
        }
        onEvidence={eligibility.length ? () => onOpenEvidence(eligibility) : null}
      />

      <Card
        title="Duplication"
        note="Compared with other applications in the call and authorized historical records."
        tone={signalTone(topDuplication)}
        value={duplication.length || duplicates.length ? String(duplicates.length) : null}
        meter={null}
        badge={topDuplication ? <SignalBadge signal={topDuplication.signal} /> : <span className="badge badge-neutral">NOT CHECKED</span>}
        summary={
          !topDuplication && !duplicates.length
            ? "No result for this check."
            : dupCompared !== null
              ? `${duplicates.length} matching submission${duplicates.length === 1 ? "" : "s"} of ${dupCompared} records compared`
              : `${duplicates.length} matching submission${duplicates.length === 1 ? "" : "s"}`
        }
        onEvidence={topDuplication ? () => onOpenEvidence(duplication) : null}
      />

      <Card
        title="Plagiarism"
        note="A similarity index against other applications and, when OpenAlex is configured, published literature. Not proof of plagiarism."
        tone={plagiarismTone(topPlagiarism)}
        value={index !== null ? index.toFixed(1) : null}
        unit="%"
        meter={index}
        badge={topPlagiarism ? <SignalBadge signal={topPlagiarism.signal} /> : <span className="badge badge-neutral">NOT CHECKED</span>}
        summary={
          !topPlagiarism
            ? "No result for this check."
            : published.length === 0
              ? searchedLiterature
                ? `No published work matched of ${worksCompared} compared`
                : "Published literature was not searched."
              : `${published.length} published source${published.length === 1 ? "" : "s"} of ${worksCompared} compared`
        }
        onEvidence={topPlagiarism ? () => onOpenEvidence(plagiarism) : null}
      />
    </div>
  );
}
