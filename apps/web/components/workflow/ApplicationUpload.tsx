"use client";

import { useState } from "react";
import type { UploadResponse } from "../../lib/types";
import { FileDrop } from "./FileDrop";
import { Notice } from "./ui";

const ACCEPT = ".pdf,.docx,.txt,.zip";

interface Props {
  disabled?: boolean;
  onBatch: (files: File[]) => Promise<UploadResponse>;
  onSingle: (files: File[], reference?: string) => Promise<UploadResponse>;
  onDone?: (result: UploadResponse) => void;
}

export function UploadSummary({ result }: { result: UploadResponse }) {
  const kind = result.errors.length || result.requires_manual_association.length ? "review" : "success";
  return (
    <Notice kind={kind} title="Upload processed">
      <ul className="upload-summary">
        <li><b>{result.files_received}</b> file(s) received</li>
        <li><b>{result.applications_created.length}</b> application(s) created</li>
        {result.applications_updated.length > 0 && <li><b>{result.applications_updated.length}</b> existing application(s) updated</li>}
        <li><b>{result.documents_associated}</b> document(s) associated</li>
        {result.requires_manual_association.length > 0 && <li><b>{result.requires_manual_association.length}</b> file(s) need manual association</li>}
        {result.duplicates.length > 0 && <li><b>{result.duplicates.length}</b> duplicate file(s) skipped</li>}
      </ul>
      {result.duplicates.length > 0 && <details><summary>Duplicates</summary><ul>{result.duplicates.map((d) => <li key={d}>{d}</li>)}</ul></details>}
      {result.errors.length > 0 && <details open><summary>Problems ({result.errors.length})</summary><ul>{result.errors.map((e) => <li key={e}>{e}</li>)}</ul></details>}
    </Notice>
  );
}

export function ApplicationUpload({ disabled, onBatch, onSingle, onDone }: Props) {
  const [mode, setMode] = useState<"batch" | "single">("batch");
  const [reference, setReference] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handle(files: File[]) {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const response = mode === "batch" ? await onBatch(files) : await onSingle(files, reference.trim() || undefined);
      setResult(response);
      setReference("");
      onDone?.(response);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="application-upload">
      <div className="segmented" role="group" aria-label="Upload mode">
        <button aria-pressed={mode === "batch"} onClick={() => setMode("batch")}>Several applications / ZIP</button>
        <button aria-pressed={mode === "single"} onClick={() => setMode("single")}>One application</button>
      </div>
      {mode === "single" && (
        <label className="inline-field">Application reference (optional)<input value={reference} onChange={(e) => setReference(e.target.value)} placeholder="Generated if left empty" /></label>
      )}
      <FileDrop
        accept={ACCEPT}
        multiple
        disabled={disabled || busy}
        inputLabel={mode === "batch" ? "Application files" : "Files for one application"}
        label={busy ? "Uploading and extracting text…" : mode === "batch" ? "Upload applications" : "Upload one application's documents"}
        hint={mode === "batch"
          ? "PDF, DOCX, TXT or ZIP. Files are grouped by folder (REF/file.pdf) or by prefix (REF__file.pdf); anything else is held for manual association."
          : "All files are attached to a single application. Metadata is read only from explicit fields such as “Title:” or “Requested amount:”."}
        onFiles={handle}
      />
      {error && <Notice kind="error" title="Upload failed">{error}</Notice>}
      {result && <UploadSummary result={result} />}
    </div>
  );
}
