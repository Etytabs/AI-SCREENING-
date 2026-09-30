"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";
import { CallForm } from "../../../components/workflow/CallForm";
import { FileDrop } from "../../../components/workflow/FileDrop";
import { RequirementReview } from "../../../components/workflow/RequirementReview";
import { CallStatusBadge, Notice, PageHeader, SyntheticBadge } from "../../../components/workflow/ui";
import { useWorkspace } from "../../../components/workflow/WorkspaceContext";
import { API_BASE, ApiError } from "../../../lib/api";
import { formatAmount, formatDate, ROLE_LABELS } from "../../../lib/labels";
import type { GrantCall, RfpCriterion, RfpUploadResponse } from "../../../lib/types";

const RFP_ACCEPT = ".pdf,.docx,.txt";
const errorText = (e: unknown) => (e instanceof ApiError || e instanceof Error ? e.message : "Request failed");

function CallList() {
  const { calls, callsState, callsError, client, role, refreshCalls, setCallId } = useWorkspace();
  const router = useRouter();
  const canCreate = role !== "REVIEWER";
  return (
    <>
      <PageHeader eyebrow="GRANT SCREENING / GRANT CALLS" title="Grant calls" intro="Create a call, upload its call document (RFP) and verify the requirements before accepting submissions." />
      {callsState === "loading" && <Notice kind="loading" title="Loading grant calls…" />}
      {callsState === "error" && <Notice kind="error" title="Grant calls unavailable">{callsError}</Notice>}
      {callsState === "ready" && calls.length === 0 && <Notice kind="empty" title="No grant calls yet">Create the first call below.</Notice>}
      {calls.length > 0 && (
        <table className="data-table">
          <thead><tr><th>Call</th><th>Organization</th><th>Status</th><th>Funding ceiling</th><th>Created</th><th /></tr></thead>
          <tbody>
            {calls.map((call) => (
              <tr key={call.id}>
                <td><b>{call.name}</b> <SyntheticBadge origin={call.data_origin} /><small>{call.reference}</small></td>
                <td>{call.organization}</td>
                <td><CallStatusBadge status={call.status} /></td>
                <td>{formatAmount(call.funding_max, call.currency)}</td>
                <td>{formatDate(call.created_at)}</td>
                <td><Link href={`/dashboard/calls?id=${call.id}`} onClick={() => setCallId(call.id)}>Open setup →</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <section className="panel">
        <h2>Create a grant call</h2>
        {!canCreate && <Notice kind="info" title="Read-only">Only a Grant Administrator or System Administrator can create calls. Current role: {ROLE_LABELS[role]}.</Notice>}
        <CallForm
          disabled={!canCreate}
          onSubmit={(input) => client.createCall(input)}
          onCreated={async (call: GrantCall) => {
            await refreshCalls();
            setCallId(call.id);
            router.push(`/dashboard/calls?id=${call.id}`);
          }}
        />
      </section>
    </>
  );
}

function CallSetup({ id }: { id: string }) {
  const { client, role, refreshCalls, setCallId } = useWorkspace();
  const [call, setCall] = useState<GrantCall | null>(null);
  const [requirements, setRequirements] = useState<RfpCriterion[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [lastUpload, setLastUpload] = useState<RfpUploadResponse | null>(null);
  const canEdit = role !== "REVIEWER";

  const load = useCallback(async () => {
    try {
      const [c, r] = await Promise.all([client.getCall(id), client.listRequirements(id)]);
      setCall(c);
      setRequirements(r);
      setError(null);
    } catch (e) {
      setError(errorText(e));
    }
  }, [client, id]);

  useEffect(() => {
    setCallId(id);
    load();
  }, [id, load, setCallId]);

  const after = async () => { await load(); await refreshCalls(); };

  if (error && !call) return <Notice kind="error" title="Grant call unavailable">{error}</Notice>;
  if (!call) return <Notice kind="loading" title="Loading grant call…" />;
  const confirmed = !["DRAFT", "REQUIREMENTS_PENDING"].includes(call.status);

  return (
    <>
      <PageHeader
        eyebrow="GRANT CALLS / SETUP"
        title={call.name}
        intro={`${call.organization}${call.reference ? ` · ${call.reference}` : ""}`}
        actions={<><CallStatusBadge status={call.status} /><SyntheticBadge origin={call.data_origin} /></>}
      />
      {error && <Notice kind="error" title="Action failed">{error}</Notice>}
      {call.data_origin === "SYNTHETIC" && (
        <Notice kind="info" title="Synthetic demonstration call">
          Requirements in this call were verified automatically by the demo seed, not by a person. It is not an official NCST/NRIF call.
        </Notice>
      )}

      <section className="panel">
        <h2><span className="step-no">1</span> Call document</h2>
        <p className="muted">Upload the RFP as PDF, DOCX or TXT. Requirements are extracted deterministically and every one cites the exact sentence it came from. Nothing is screened until an administrator verifies it.</p>
        {canEdit ? (
          <FileDrop
            accept={RFP_ACCEPT}
            disabled={uploading || call.status === "CLOSED" || call.status === "ARCHIVED"}
            label={uploading ? "Extracting requirements…" : "Upload call document"}
            hint="PDF, DOCX or TXT. Uploading a new version supersedes unverified requirements from earlier versions."
            onFiles={async ([file]) => {
              setUploading(true);
              setError(null);
              try {
                const response = await client.uploadRfp(id, file);
                setLastUpload(response);
                await after();
              } catch (e) {
                setError(errorText(e));
              } finally {
                setUploading(false);
              }
            }}
          />
        ) : (
          <Notice kind="info" title="Read-only">Only administrators can upload call documents.</Notice>
        )}
        {lastUpload && (
          lastUpload.requirements.length
            ? <Notice kind="success" title={`${lastUpload.requirements.length} requirements extracted from ${lastUpload.rfp_document.filename} (version ${lastUpload.rfp_document.version})`}>Review each one below.</Notice>
            : <Notice kind="review" title="No requirements could be extracted">The document was read ({lastUpload.rfp_document.extraction_status}) but no requirement sentences were recognised. Add requirements manually.</Notice>
        )}
        {call.data_origin === "SYNTHETIC" && (
          <p className="muted">Demo files: <a href={`${API_BASE}/api/v1/demo/rfp`}>synthetic call document</a> · <a href={`${API_BASE}/api/v1/demo/applications.zip`}>synthetic applications ZIP</a></p>
        )}
      </section>

      <section className="panel">
        <h2><span className="step-no">2</span> Verify requirements</h2>
        <RequirementReview
          requirements={requirements}
          canEdit={canEdit}
          confirmed={confirmed}
          onVerify={async (cid) => { await client.verifyRequirement(cid, "VERIFY"); await after(); }}
          onReject={async (cid, note) => { await client.verifyRequirement(cid, "REJECT", note); await after(); }}
          onEdit={async (cid, changes) => { await client.updateRequirement(cid, changes); await after(); }}
          onToggleActive={async (cid, active) => { await client.setRequirementActive(cid, active); await after(); }}
          onAdd={async (input) => { await client.addRequirement(id, input); await after(); }}
          onConfirm={async () => { await client.confirmRequirements(id); await after(); }}
        />
      </section>

      <section className="panel">
        <h2><span className="step-no">3</span> Submissions</h2>
        {confirmed
          ? <p>Requirements are confirmed. <Link href="/dashboard/applications">Upload applications →</Link></p>
          : <p className="muted">Submissions open after every active requirement has been verified, edited or rejected.</p>}
      </section>
    </>
  );
}

function CallsContent() {
  const params = useSearchParams();
  const id = params?.get("id");
  return id ? <CallSetup id={id} /> : <CallList />;
}

export default function CallsPage() {
  return (
    <Suspense fallback={<Notice kind="loading" title="Loading…" />}>
      <CallsContent />
    </Suspense>
  );
}
