"use client";

import Link from "next/link";
import { useState } from "react";
import { CheckResultCards } from "../../../components/workflow/CheckResultCards";
import { DecisionModal } from "../../../components/workflow/DecisionModal";
import { EvidenceModal } from "../../../components/workflow/EvidenceModal";
import { FileDrop } from "../../../components/workflow/FileDrop";
import { NoCallSelected, Notice, PageHeader } from "../../../components/workflow/ui";
import { useWorkspace } from "../../../components/workflow/WorkspaceContext";
import { ApiError } from "../../../lib/api";
import type { ApplicationDetail, Finding } from "../../../lib/types";

type Phase = "idle" | "uploading" | "screening" | "done" | "error";

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export default function ResearchCheckPage() {
  const { client, call, callId, callsState, role, refreshCalls } = useWorkspace();
  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState<string | null>(null);
  const [uploadErrors, setUploadErrors] = useState<string[]>([]);
  const [detail, setDetail] = useState<ApplicationDetail | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [evidenceFor, setEvidenceFor] = useState<Finding[] | null>(null);
  const [deciding, setDeciding] = useState(false);

  const open = !!call && ["READY_FOR_SUBMISSIONS", "SCREENING", "REVIEW"].includes(call.status);
  const busy = phase === "uploading" || phase === "screening";
  const showResults = phase === "done" && !!detail;

  function reset() {
    setPhase("idle");
    setDetail(null);
    setFindings([]);
    setError(null);
    setUploadErrors([]);
    setEvidenceFor(null);
    setDeciding(false);
  }

  async function check(files: File[]) {
    if (!call) return;
    setPhase("uploading");
    setError(null);
    setUploadErrors([]);
    setDetail(null);
    setFindings([]);
    try {
      const upload = await client.createApplication(call.id, files);
      setUploadErrors([...upload.errors, ...upload.duplicates.map((d) => `${d}: duplicate file skipped`)]);
      const applicationId = upload.applications_created[0] ?? upload.applications_updated[0];
      if (!applicationId) throw new Error("No application was created from these files.");
      setPhase("screening");
      await client.screenApplication(applicationId);
      let current = await client.getApplication(applicationId);
      while (!current.latest_run || ["QUEUED", "RUNNING"].includes(current.latest_run.status)) {
        await sleep(1500);
        current = await client.getApplication(applicationId);
      }
      setDetail(current);
      setFindings(await client.listFindings(applicationId));
      setPhase("done");
      refreshCalls();
    } catch (e) {
      // The selected call can disappear under us (for example after an API restart).
      // Reload the list so the picker recovers instead of failing on every attempt.
      if (e instanceof ApiError && e.status === 404) {
        await refreshCalls();
        setError("That grant call no longer exists. The call list has been reloaded - pick a call and try again.");
      } else {
        setError(e instanceof ApiError || e instanceof Error ? e.message : "The check failed.");
      }
      setPhase("error");
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="GRANT SCREENING / RESEARCH CHECK"
        title="Check a research document"
        intro="Upload a proposal or research document. It is added to the selected call and checked for eligibility, duplication and plagiarism (text similarity)."
      />
      {callsState === "ready" && !callId && <NoCallSelected />}
      {call && role === "REVIEWER" && <Notice kind="info" title="Read-only">Switch to Grant Administrator in the sidebar to upload documents.</Notice>}
      {call && role !== "REVIEWER" && !open && (
        <Notice kind="review" title="Call not open">Confirm this call&apos;s requirements first. <Link href={`/dashboard/calls?id=${call.id}`}>Go to requirement review</Link></Notice>
      )}

      {call && role !== "REVIEWER" && open && !showResults && (
        <section className="panel">
          <p className="muted small">Checking against: <b>{call.name}</b></p>
          <FileDrop
            accept=".pdf,.docx,.txt,.zip"
            multiple
            disabled={busy}
            inputLabel="Research document"
            label={phase === "uploading" ? "Uploading and extracting text…" : phase === "screening" ? "Checking…" : "Upload research to check"}
            hint="PDF, DOCX, TXT or ZIP. Add the budget, CV and other annexes too if you have them; all files are treated as one submission."
            onFiles={check}
          />
        </section>
      )}

      {phase === "screening" && <Notice kind="processing" title="Screening in progress">Running eligibility, duplication and text-similarity checks…</Notice>}
      {error && <Notice kind="error" title="Check failed">{error}</Notice>}
      {uploadErrors.length > 0 && (
        <Notice kind="review" title="Some files had problems"><ul>{uploadErrors.map((e) => <li key={e}>{e}</li>)}</ul></Notice>
      )}

      {showResults && detail && (
        <section className="panel">
          <div className="panel-head">
            <h2>Results - {detail.application.application_reference}</h2>
            <div className="page-actions">
              <button className="ghost-button" onClick={reset}>Check another document</button>
              <button className="dark-button" aria-haspopup="dialog" onClick={() => setDeciding(true)}>Human decision</button>
            </div>
          </div>
          {detail.latest_run?.status === "BLOCKED" && <Notice kind="error" title="Screening blocked">None of the uploaded files could be read.</Notice>}
          {detail.latest_run?.status === "PARTIAL" && <Notice kind="partial" title="Partial screening">Some checks could not complete and are marked REVIEW REQUIRED.</Notice>}
          <CheckResultCards findings={findings} onOpenEvidence={setEvidenceFor} />
          <p className="disclaimer">These are screening signals for human review. They do not decide eligibility, duplication, plagiarism or funding.</p>
        </section>
      )}

      {evidenceFor && <EvidenceModal findings={evidenceFor} siblingFindings={findings} onClose={() => setEvidenceFor(null)} />}

      {deciding && detail && (
        <DecisionModal
          findings={findings}
          onClose={() => setDeciding(false)}
          onRecorded={async () => setFindings(await client.listFindings(detail.application.id))}
        />
      )}

    </>
  );
}
