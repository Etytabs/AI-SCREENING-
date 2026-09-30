"use client";

import Link from "next/link";
import { CALL_STATUS_LABELS, SIGNAL_LABELS } from "../../lib/labels";
import type { DataOrigin, GrantCallStatus } from "../../lib/types";

type Tone = "pass" | "fail" | "review" | "processing" | "neutral" | "partial";

const STATUS_STYLE: Record<string, { tone: Tone; symbol: string; label: string }> = {
  PASS: { tone: "pass", symbol: "✓", label: "PASS" },
  FAIL: { tone: "fail", symbol: "✕", label: "FAIL" },
  REVIEW_REQUIRED: { tone: "review", symbol: "!", label: "REVIEW REQUIRED" },
  NOT_SCREENED: { tone: "neutral", symbol: "–", label: "NOT SCREENED" },
  QUEUED: { tone: "processing", symbol: "…", label: "QUEUED" },
  RUNNING: { tone: "processing", symbol: "…", label: "PROCESSING" },
  PROCESSING: { tone: "processing", symbol: "…", label: "PROCESSING" },
  PENDING: { tone: "neutral", symbol: "○", label: "PENDING" },
  COMPLETE: { tone: "pass", symbol: "✓", label: "COMPLETE" },
  SCREENED: { tone: "pass", symbol: "✓", label: "SCREENED" },
  SKIPPED: { tone: "neutral", symbol: "–", label: "SKIPPED" },
  PARTIAL: { tone: "partial", symbol: "◐", label: "PARTIAL" },
  BLOCKED: { tone: "fail", symbol: "■", label: "BLOCKED" },
  FAILED: { tone: "fail", symbol: "✕", label: "FAILED" },
  AVAILABLE: { tone: "pass", symbol: "✓", label: "AVAILABLE" },
  NOT_CONFIGURED: { tone: "neutral", symbol: "–", label: "NOT CONFIGURED" },
  DEGRADED: { tone: "partial", symbol: "◐", label: "DEGRADED" },
  UNAVAILABLE: { tone: "fail", symbol: "■", label: "UNAVAILABLE" },
  AUTH_REQUIRED: { tone: "review", symbol: "!", label: "AUTH REQUIRED" },
  RATE_LIMITED: { tone: "partial", symbol: "◐", label: "RATE LIMITED" },
  EXPIRED: { tone: "review", symbol: "!", label: "EXPIRED" },
};

export function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLE[status] ?? { tone: "neutral" as Tone, symbol: "·", label: status.replace(/_/g, " ") };
  return (
    <span className={`badge badge-${style.tone}`} aria-label={`Status: ${style.label}`} data-status={status}>
      <span aria-hidden="true">{style.symbol}</span> {style.label}
    </span>
  );
}

const SIGNAL_TONES: Record<string, Tone> = {
  POSSIBLE_DUPLICATION: "review",
  SHARED_PASSAGES_FOUND: "review",
  NOT_ASSESSABLE: "review",
  REVIEW_REQUIRED: "review",
  LOW: "review",
  NO_SIGNIFICANT_SIMILARITY: "neutral",
  NO_SHARED_PASSAGES: "neutral",
  HIGH: "neutral",
  MEDIUM: "neutral",
  NOT_SCREENED: "neutral",
};

export function SignalBadge({ signal }: { signal: string | null }) {
  if (!signal) return <span className="badge badge-neutral">—</span>;
  const tone = SIGNAL_TONES[signal] ?? "neutral";
  const symbol = tone === "review" ? "!" : "○";
  const label = SIGNAL_LABELS[signal] ?? signal.replace(/_/g, " ").toLowerCase();
  return (
    <span className={`badge badge-${tone} badge-signal`} aria-label={`Signal: ${label}`} data-signal={signal}>
      <span aria-hidden="true">{symbol}</span> {label}
    </span>
  );
}

export function CallStatusBadge({ status }: { status: GrantCallStatus }) {
  return <span className="call-status" data-status={status}>{CALL_STATUS_LABELS[status]}</span>;
}

export function SyntheticBadge({ origin }: { origin: DataOrigin }) {
  if (origin !== "SYNTHETIC") return null;
  return <span className="synthetic-badge" title="Synthetic demonstration data; not an official record">SYNTHETIC</span>;
}

export type NoticeKind = "loading" | "processing" | "empty" | "error" | "partial" | "review" | "info" | "success";

export function Notice({ kind, title, children }: { kind: NoticeKind; title: string; children?: React.ReactNode }) {
  const role = kind === "error" ? "alert" : "status";
  return (
    <div className={`notice notice-${kind}`} role={role}>
      <b>{title}</b>
      {children && <div>{children}</div>}
    </div>
  );
}

export function NoCallSelected() {
  return (
    <Notice kind="empty" title="No grant call selected">
      Select a call in the sidebar or <Link href="/dashboard/calls">create a grant call</Link>.
    </Notice>
  );
}

export function PageHeader({ eyebrow, title, intro, actions }: { eyebrow: string; title: string; intro?: string; actions?: React.ReactNode }) {
  return (
    <header className="page-head">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        {intro && <p>{intro}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </header>
  );
}
