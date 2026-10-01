"use client";

import Link from "next/link";
import { useState } from "react";
import type { ArchivedProject, ArchivedProjectInput, DuplicationSourceType } from "../../lib/types";
import { FileDrop } from "./FileDrop";
import { Notice } from "./ui";

interface Props {
  onImport: (input: ArchivedProjectInput) => Promise<ArchivedProject>;
  onImported: (project: ArchivedProject) => void;
}

const EMPTY = { title: "", source_type: "historical_application" as DuplicationSourceType, reference: "", year: "", organization: "" };

export function DuplicationProjectImport({ onImport, onImported }: Props) {
  const [values, setValues] = useState(EMPTY);
  const [file, setFile] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [imported, setImported] = useState<ArchivedProject | null>(null);
  const set = (key: keyof typeof EMPTY) => (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setValues((current) => ({ ...current, [key]: event.target.value }));

  function selectFile(files: File[]) {
    setError(null);
    setImported(null);
    setFile(null);
    if (files.length !== 1) {
      setError("Choose one project document at a time.");
      return;
    }
    const selected = files[0];
    if (!/\.(pdf|docx|txt)$/i.test(selected.name)) {
      setError("Use a PDF, DOCX or TXT project document.");
      return;
    }
    if (!selected.size || selected.size > 20 * 1024 * 1024) {
      setError("Choose a non-empty document no larger than 20 MB.");
      return;
    }
    setFile(selected);
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (saving) return;
    setImported(null);
    if (!file || !values.title.trim()) {
      setError("A project title and document are required.");
      return;
    }
    const year = values.year ? Number(values.year) : undefined;
    if (year !== undefined && (!Number.isInteger(year) || year < 1000 || year > 9999)) {
      setError("Enter a four-digit year between 1000 and 9999.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const project = await onImport({
        file,
        title: values.title.trim(),
        source_type: values.source_type,
        reference: values.reference.trim() || undefined,
        year,
        organization: values.organization.trim() || undefined,
      });
      setImported(project);
      setValues(EMPTY);
      setFile(null);
      onImported(project);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The project could not be imported.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      {imported && (
        <Notice kind="success" title="Project added to the comparison library">
          {imported.title} is ready for future duplication checks. <Link href="/dashboard/screening">Run screening again</Link> to compare existing applications against the updated library.
        </Notice>
      )}
      <form className="form-grid" onSubmit={submit} aria-label="Import comparison project">
        <label>Project title *<input value={values.title} onChange={set("title")} required maxLength={500} disabled={saving} /></label>
        <label>Project source<select value={values.source_type} onChange={set("source_type")} disabled={saving}>
          <option value="historical_application">Previously submitted proposal</option>
          <option value="funded_project">Funded project</option>
        </select></label>
        <label>Project reference<input value={values.reference} onChange={set("reference")} maxLength={200} disabled={saving} /></label>
        <label>Year<input type="number" min="1000" max="9999" step="1" value={values.year} onChange={set("year")} disabled={saving} /></label>
        <label className="span-2">Organization<input value={values.organization} onChange={set("organization")} maxLength={500} disabled={saving} /></label>
        <div className="span-2">
          <FileDrop
            accept=".pdf,.docx,.txt" disabled={saving} label="Add a previous project document"
            hint="PDF, DOCX or TXT up to 20 MB. Include the project objectives, methods and expected outcomes."
            inputLabel="Previous project document" onFiles={selectFile}
          />
          {file && <p className="small">Selected: <b>{file.name}</b></p>}
        </div>
        {error && <p className="form-error span-2" role="alert">{error}</p>}
        <div className="form-actions span-2">
          <button type="submit" className="dark-button" disabled={saving}>{saving ? "Importing project…" : "Add to comparison library"}</button>
        </div>
      </form>
    </>
  );
}
