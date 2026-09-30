"use client";

import { useContext, useEffect, useState } from "react";
import type { Stakeholder } from "../../lib/types";
import { ApiError } from "../../lib/api";
import { WorkspaceContext } from "./WorkspaceContext";

export function StakeholderOverview() {
  const workspace = useContext(WorkspaceContext);
  const client = workspace?.client;
  const [stakeholders, setStakeholders] = useState<Stakeholder[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!client) return;
    let cancelled = false;
    client.stakeholders().then((data) => {
      if (!cancelled) setStakeholders(data.stakeholders);
    }).catch((e) => {
      if (!cancelled) setError(e instanceof ApiError ? e.message : "Unable to load stakeholder context.");
    });
    return () => { cancelled = true; };
  }, [client]);

  if (!client) return null;
  if (error) return <p className="muted">{error}</p>;
  if (!stakeholders.length) return <p className="muted">Loading stakeholder context…</p>;

  return (
    <section className="stakeholder-overview" aria-labelledby="stakeholder-overview-title">
      <div className="eyebrow">USER &amp; EVIDENCE · PRIMARY USERS</div>
      <div className="stakeholder-overview-head">
        <div>
          <h2 id="stakeholder-overview-title">Built around the grant lifecycle</h2>
          <p>AI-SCREENING supports the institutional screening workflow and gives researchers a pre-submission view of potential research overlap.</p>
        </div>
        <span className="human-review-note">Human review remains required.</span>
      </div>
      <div className="stakeholder-overview-grid">
        {stakeholders.map((stakeholder, index) => (
          <article className="stakeholder-overview-card" key={stakeholder.stakeholder_id}>
            <span className="stakeholder-index">0{index + 1}</span>
            <h3>{stakeholder.name}</h3>
            <p className="stakeholder-role">{stakeholder.role}</p>
            <p>{stakeholder.purpose}</p>
            <dl>
              <dt>Access</dt><dd>{stakeholder.access_scope}</dd>
              <dt>Stage</dt><dd>{stakeholder.lifecycle_stage}</dd>
            </dl>
          </article>
        ))}
      </div>
    </section>
  );
}
