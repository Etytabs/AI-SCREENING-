"use client";

import Link from "next/link";
import { useState } from "react";
import { FileDrop } from "../../../components/workflow/FileDrop";
import { NoCallSelected, Notice, PageHeader } from "../../../components/workflow/ui";
import { useWorkspace } from "../../../components/workflow/WorkspaceContext";
import { ApiError } from "../../../lib/api";
import type { ApplicationDetail, BatchProgress } from "../../../lib/types";

type Phase = "idle" | "uploading" | "screening" | "done" | "error";

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export default function ResearchCheckPage() {
  const { client, call, callId, callsState, role, refreshCalls } = useWorkspace();
  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState<string | null>(null);
  const [uploadErrors, setUploadErrors] = useState<string[]>([]);
  const [batch, setBatch] = useState<BatchProgress | null>(null);
  const [detail, setDetail] = useState<ApplicationDetail | null>(null);

  const open = !!call && ["READY_FOR_SUBMISSIONS", "SCREENING", "REVIEW"].includes(call.status);
  const busy = phase === "uploading" || phase === "screening";

  async function check(files: File[]) {
    if (!call || !files.length) return;

    setPhase("uploading");
    setError(null);
    setUploadErrors([]);
    setBatch(null);
    setDetail(null);

    try {
      // Research Check is an intake point for the NCST team: several submitted
      // proposals can arrive together and must remain separate applications.
      const upload = await client.batchUpload(call.id, files);
      setUploadErrors([
        ...upload.errors,
        ...upload.duplicates.map((d) => `${d}: duplicate file skipped`),
        ...upload.requires_manual_association.map(
          (p) => `${p.filename}: needs an application reference before screening`,
        ),
      ]);

      const applicationIds = [...new Set([
        ...upload.applications_created,
        ...upload.applications_updated,
      ])];

      if (!applicationIds.length) {
        throw new Error(
          "No research submission could be associated with an application. Use a ZIP with one folder per submission, or prefix files with the application reference (REF__proposal.pdf).",
        );
      }

      setPhase("screening");
      const screening = await client.screenCall(call.id, applicationIds);

      let current = await client.batchProgress(screening.id);
      while (["QUEUED", "RUNNING"].includes(current.status)) {
        await sleep(1500);
        current = await client.batchProgress(screening.id);
      }
      setBatch(current);

      // Keep the detailed result view for a single submission. For multiple
      // submissions, the Applications workspace is the correct review surface.
      if (applicationIds.length === 1) {
        const application = await client.getApplication(applicationIds[0]);
        setDetail(application);
      }

      setPhase("done");
      await refreshCalls();
    } catch (e) {
      setError(e instanceof ApiError || e instanceof Error ? e.message : "The check failed.");
      setPhase("error");
    }
  }

  const created = batch?.total ?? 0;
  const finished = batch?.finished ?? 0;

  return (
    <>
      <PageHeader
        eyebrow="GRANT SCREENING / RESEARCH CHECK"
        title="Upload submitted research"
        intro="Upload multiple research proposals received for the selected funding call. Each associated submission becomes its own application and can then be screened against the call requirements."
      />

      {callsState === "ready" && !callId && <NoCallSelected />}

      {call && role === "REVIEWER" && (
        <Notice kind="info" title="Read-only">
          Switch to Grant Administrator in the sidebar to upload submitted research.
        </Notice>
      )}

      {call && role !== "REVIEWER" && !open && (
        <Notice kind="review" title="Call not open">
          Confirm this call&apos;s requirements first.{" "}
          <Link href={`/dashboard/calls?id=${call.id}`}>Go to requirement review</Link>
        </Notice>
      )}

      {call && role !== "REVIEWER" && open && (
        <section className="panel">
          <p className="muted small">
            Funding call: <b>{call.name}</b>
          </p>
          <FileDrop
            accept=".pdf,.docx,.txt,.md,.markdown,.zip"
            multiple
            disabled={busy}
            inputLabel="Submitted research"
            label={
              phase === "uploading"
                ? "Uploading submitted research…"
                : phase === "screening"
                  ? "Screening submissions…"
                  : "Upload submitted research"
            }
            hint="Select any supported research document directly. Each loose file is treated as one submission and receives an application reference automatically. Use a ZIP with one folder per submission when a submission contains multiple files; REF__filename.pdf is also supported."
            onFiles={check}
          />
        </section>
      )}

      {phase === "screening" && (
        <Notice kind="processing" title="Screening in progress">
          Screening the submitted research against eligibility, duplication and text-similarity checks…
        </Notice>
      )}

      {error && <Notice kind="error" title="Check failed">{error}</Notice>}

      {uploadErrors.length > 0 && (
        <Notice kind="review" title="Some files need attention">
          <ul>{uploadErrors.map((item) => <li key={item}>{item}</li>)}</ul>
        </Notice>
      )}

      {phase === "done" && batch && (
        <section className="panel">
          <div className="panel-head">
            <div>
              <p className="muted small">Research intake complete</p>
              <h2>{created} submission{created === 1 ? "" : "s"} sent to screening</h2>
            </div>
            <Link className="ghost-button" href="/dashboard/applications">
              Open Applications
            </Link>
          </div>

          <div className="check-section">
            <p>
              <b>{finished}</b> of <b>{batch.total}</b> screening run{batch.total === 1 ? "" : "s"} finished.
            </p>
            {uploadErrors.length > 0 && (
              <p className="muted small">
                Some files were not screened because they need manual association.
              </p>
            )}
          </div>
        </section>
      )}

      {phase === "done" && detail && (
        <section className="panel">
          <div className="panel-head">
            <div>
              <p className="muted small">Submission result</p>
              <h2>{detail.application.application_reference}</h2>
            </div>
            <Link
              className="ghost-button"
              href={`/dashboard/applications/view?id=${detail.application.id}`}
            >
              Open full review workspace
            </Link>
          </div>
          <p className="muted">
            The detailed findings are available in the application review workspace, with evidence and human-review actions.
          </p>
        </section>
      )}
    </>
  );
}
