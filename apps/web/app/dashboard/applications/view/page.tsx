"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { DocumentViewer, type Highlight } from "../../../../components/workflow/DocumentViewer";
import { EvidenceDrawer } from "../../../../components/workflow/EvidenceDrawer";
import { FindingList } from "../../../../components/workflow/FindingList";
import { Notice, SignalBadge, StatusBadge, SyntheticBadge } from "../../../../components/workflow/ui";
import { useWorkspace } from "../../../../components/workflow/WorkspaceContext";
import { ApiError } from "../../../../lib/api";
import { formatAmount, formatDate } from "../../../../lib/labels";
import type { ApplicationDetail, DocumentContent, Finding, FindingDetail, FindingEvidence } from "../../../../lib/types";

const message = (e: unknown) => (e instanceof ApiError || e instanceof Error ? e.message : "Request failed");

function Workspace({ id, initialFinding }: { id: string; initialFinding: string | null }) {
  const { client, role } = useWorkspace();
  const [detail, setDetail] = useState<ApplicationDetail | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [selected, setSelected] = useState<FindingDetail | null>(null);
  const [docId, setDocId] = useState<string | null>(null);
  const [content, setContent] = useState<DocumentContent | null>(null);
  const [highlight, setHighlight] = useState<Highlight | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [d, f] = await Promise.all([client.getApplication(id), client.listFindings(id)]);
      setDetail(d);
      setFindings(f);
      setError(null);
      setDocId((current) => current ?? d.documents.find((doc) => doc.document_type === "proposal")?.id ?? d.documents[0]?.id ?? null);
    } catch (e) {
      setError(message(e));
    }
  }, [client, id]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (!detail?.latest_run || !["QUEUED", "RUNNING"].includes(detail.latest_run.status)) return;
    const timer = setTimeout(load, 1500);
    return () => clearTimeout(timer);
  }, [detail, load]);

  useEffect(() => {
    if (!docId) return;
    let cancelled = false;
    client.documentContent(docId).then((c) => { if (!cancelled) setContent(c); }).catch((e) => { if (!cancelled) setActionError(message(e)); });
    return () => { cancelled = true; };
  }, [client, docId]);

  const documentNames = useMemo(() => Object.fromEntries((detail?.documents ?? []).map((d) => [d.id, d.filename])), [detail]);

  const [openedInitial, setOpenedInitial] = useState(false);
  useEffect(() => {
    if (openedInitial || !initialFinding || !detail) return;
    const target = findings.find((f) => f.finding_id === initialFinding);
    if (!target) return;
    setOpenedInitial(true);
    openFinding(target);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialFinding, findings, detail, openedInitial]);

  async function openFinding(f: Finding) {
    try {
      setSelected(await client.getFinding(f.finding_id));
      const first = f.evidence.find((e) => e.source_type === "application_document" && e.document_id && documentNames[e.document_id]);
      if (first) showInDocument(first);
    } catch (e) {
      setActionError(message(e));
    }
  }

  function showInDocument(evidence: FindingEvidence) {
    if (!evidence.document_id) return;
    setDocId(evidence.document_id);
    setHighlight({ documentId: evidence.document_id, page: evidence.page, text: evidence.text });
  }

  async function refreshSelected(findingId: string) {
    const [d, f] = await Promise.all([client.getFinding(findingId), client.listFindings(id)]);
    setSelected(d);
    setFindings(f);
    setDetail(await client.getApplication(id));
  }

  if (error) return <Notice kind="error" title="Application unavailable">{error}</Notice>;
  if (!detail) return <Notice kind="loading" title="Loading application…" />;

  const { application, row, documents, latest_run: run } = detail;
  const running = run && ["QUEUED", "RUNNING"].includes(run.status);
  const notSearched = run?.coverage.sources?.filter((s) => s.state !== "COMPLETE") ?? [];
  const canDecide = role === "REVIEWER" || role === "GRANT_ADMINISTRATOR";

  return (
    <div className="review-page">
      <header className="page-head review-head">
        <div>
          <div className="eyebrow"><Link href="/dashboard/applications">APPLICATIONS</Link> / {application.application_reference} <SyntheticBadge origin={application.data_origin} /></div>
          <h1>{application.title ?? "Untitled application"}</h1>
          <p>{[row.applicant_name, row.institution_name, row.country].filter(Boolean).join(" · ") || "Applicant details not stated in the documents"}</p>
        </div>
        <div className="page-actions">
          {role !== "REVIEWER" && (
            <button className="ghost-button" disabled={!!running} onClick={async () => {
              setActionError(null);
              try { await client.screenApplication(id); setSelected(null); await load(); } catch (e) { setActionError(message(e)); }
            }}>{run ? "Re-run screening" : "Run screening"}</button>
          )}
        </div>
      </header>
      {actionError && <Notice kind="error" title="Action failed">{actionError}</Notice>}

      <section className="review-summary" aria-label="Screening summary">
        <div><span>Requested</span><b>{formatAmount(row.requested_amount, row.currency)}</b></div>
        <div><span>Eligibility</span><StatusBadge status={row.eligibility} /></div>
        <div><span>Completeness</span><StatusBadge status={row.completeness} /></div>
        <div><span>Duplication</span><SignalBadge signal={row.duplication} /></div>
        <div><span>Text similarity</span><SignalBadge signal={row.text_similarity} /></div>
        <div><span>Novelty</span><SignalBadge signal={row.novelty} /></div>
        <div><span>Screening run</span>{run ? <StatusBadge status={run.status} /> : <StatusBadge status="NOT_SCREENED" />}</div>
      </section>
      {running && <Notice kind="processing" title="Screening in progress">Stages update automatically.</Notice>}
      {run?.status === "PARTIAL" && <Notice kind="partial" title="Partial screening">One or more stages failed; the affected checks are marked REVIEW REQUIRED and must be assessed manually.</Notice>}
      {run?.status === "BLOCKED" && <Notice kind="error" title="Screening blocked">No document in this application could be read.</Notice>}
      {notSearched.length > 0 && (
        <p className="muted small">Not searched in this run: {notSearched.map((s) => s.source_id).join(", ")}. An unsearched source is not evidence of absence.</p>
      )}

      <div className="review-grid">
        <section className="review-doc" aria-label="Application documents">
          <div className="doc-tabs" role="tablist">
            {documents.map((doc) => (
              <button key={doc.id} role="tab" aria-selected={doc.id === docId} className={doc.id === docId ? "active" : ""} onClick={() => setDocId(doc.id)}>
                {doc.filename}
                <small>{doc.document_type.replace(/_/g, " ")}{doc.extraction_status !== "success" ? " · unreadable" : ""}</small>
              </button>
            ))}
          </div>
          <div className="doc-scroll">
            {content && content.document_id === docId ? <DocumentViewer content={content} highlight={highlight} /> : <Notice kind="loading" title="Loading document…" />}
          </div>
        </section>

        <section className="review-ai" aria-label="AI findings">
          <div className="review-ai-head">
            <div className="eyebrow">AI SCREENING FINDINGS</div>
            <p className="muted small">{run ? `Run ${run.status.toLowerCase()} · ${formatDate(run.completed_at ?? run.started_at)} · ${run.pipeline_version}` : "Not screened yet"}</p>
          </div>
          {!run && <Notice kind="empty" title="Not screened">Run screening to generate findings.</Notice>}
          <FindingList findings={findings} selectedId={selected?.finding.finding_id ?? null} onSelect={openFinding} />
        </section>
      </div>

      {selected && (
        <EvidenceDrawer
          detail={selected}
          documentNames={documentNames}
          canDecide={canDecide}
          onClose={() => { setSelected(null); setHighlight(null); }}
          onShowInDocument={(evidence) => {
            showInDocument(evidence);
            if (window.matchMedia?.("(max-width: 760px)").matches) setSelected(null);
          }}
          onDecide={async (action, note) => { await client.decide(selected.finding.finding_id, action, note); await refreshSelected(selected.finding.finding_id); }}
          onNote={async (note) => { await client.addNote(selected.finding.finding_id, note); await refreshSelected(selected.finding.finding_id); }}
        />
      )}
    </div>
  );
}

function Content() {
  const params = useSearchParams();
  const id = params?.get("id");
  return id ? <Workspace id={id} initialFinding={params?.get("finding") ?? null} /> : <Notice kind="empty" title="No application selected"><Link href="/dashboard/applications">Choose an application</Link>.</Notice>;
}

export default function ApplicationViewPage() {
  return (
    <Suspense fallback={<Notice kind="loading" title="Loading…" />}>
      <Content />
    </Suspense>
  );
}
