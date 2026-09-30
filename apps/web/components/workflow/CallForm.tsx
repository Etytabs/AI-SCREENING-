"use client";

import { useState } from "react";
import type { GrantCall, GrantCallInput } from "../../lib/types";

interface Props {
  onSubmit: (input: GrantCallInput) => Promise<GrantCall>;
  onCreated?: (call: GrantCall) => void;
  disabled?: boolean;
}

const EMPTY = { name: "", organization: "", reference: "", description: "", open_date: "", close_date: "", funding_min: "", funding_max: "", currency: "RWF", domains: "" };

export function CallForm({ onSubmit, onCreated, disabled }: Props) {
  const [values, setValues] = useState(EMPTY);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const set = (key: keyof typeof EMPTY) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setValues((v) => ({ ...v, [key]: e.target.value }));

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!values.name.trim() || !values.organization.trim()) {
      setError("Call name and organization are required.");
      return;
    }
    const min = values.funding_min ? Number(values.funding_min) : null;
    const max = values.funding_max ? Number(values.funding_max) : null;
    if (min !== null && max !== null && min > max) {
      setError("Minimum funding cannot exceed maximum funding.");
      return;
    }
    if (values.open_date && values.close_date && values.open_date > values.close_date) {
      setError("The opening date must be before the closing date.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const call = await onSubmit({
        name: values.name.trim(),
        organization: values.organization.trim(),
        reference: values.reference.trim() || null,
        description: values.description.trim() || null,
        open_date: values.open_date || null,
        close_date: values.close_date || null,
        funding_min: min,
        funding_max: max,
        currency: values.currency.trim() || null,
        domains: values.domains.split(",").map((d) => d.trim()).filter(Boolean),
      });
      setValues(EMPTY);
      onCreated?.(call);
    } catch (e) {
      setError(e instanceof Error ? e.message : "The call could not be created.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="form-grid" onSubmit={submit} aria-label="Create grant call">
      <label>Call name *<input value={values.name} onChange={set("name")} required disabled={disabled} /></label>
      <label>Organization *<input value={values.organization} onChange={set("organization")} required disabled={disabled} /></label>
      <label>Reference<input value={values.reference} onChange={set("reference")} disabled={disabled} /></label>
      <label>Currency<input value={values.currency} onChange={set("currency")} disabled={disabled} /></label>
      <label>Opens<input type="date" value={values.open_date} onChange={set("open_date")} disabled={disabled} /></label>
      <label>Closes<input type="date" value={values.close_date} onChange={set("close_date")} disabled={disabled} /></label>
      <label>Minimum funding<input type="number" min="0" value={values.funding_min} onChange={set("funding_min")} disabled={disabled} /></label>
      <label>Maximum funding<input type="number" min="0" value={values.funding_max} onChange={set("funding_max")} disabled={disabled} /></label>
      <label className="span-2">Research domains (comma separated)<input value={values.domains} onChange={set("domains")} disabled={disabled} /></label>
      <label className="span-2">Description<textarea value={values.description} onChange={set("description")} rows={3} disabled={disabled} /></label>
      {error && <p className="form-error span-2" role="alert">{error}</p>}
      <div className="span-2 form-actions">
        <button type="submit" className="dark-button" disabled={saving || disabled}>{saving ? "Creating…" : "Create grant call"}</button>
      </div>
    </form>
  );
}
