"use client";

import { useMemo, useState } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

type ScreeningResult = {
  proposal_id: string;
  status: string;
  run_state: string;
  extraction?: {
    filename?: string;
    text?: string;
    page_count?: number;
    extraction_status?: string;
    file_sha256?: string;
    pages?: { page_number: number; text: string }[];
  };
  completeness?: { passed: number; total: number };
  eligibility_checks?: {
    criterion: string;
    label: string;
    status: string;
    passed: boolean | null;
    evidence: string;
    observed?: unknown;
  }[];
  similarity_candidates?: {
    proposal_id: string;
    similarity: number;
    lexical_similarity: number;
    semantic_similarity: number | null;
    rank: number;
    method: string;
  }[];
  retrieved_evidence?: {
    chunk_id: string;
    page_number: number;
    text: string;
    score: number;
    lexical_score: number;
    semantic_score: number | null;
    rank: number;
    method: string;
  }[];
  text_overlap?: {
    source_id: string;
    ratio: number;
    shared_tokens: number;
    method: string;
  }[];
  evidence?: {
    source_id: string;
    field: string;
    value: string;
    rationale: string;
  }[];
  evidence_chain?: {
    finding_id: string;
    criterion_id: string;
    status: string;
    relationship: string;
    confidence: number;
    page_number: number;
    evidence_span: string;
    citation_locator: string;
  }[];
  evidence_coverage?: {
    internal_document: string;
    citation_validated_findings: number;
    retrieved_chunks: number;
    findings: number;
  };
  model_versions?: {
    retrieval?: string;
    embedding_model?: string;
    embedding_runtime?: string;
    rules?: string;
  };
  human_review_required?: boolean;
};

const proposals = [
  { id: "NRIF-2026-014", title: "AI-based crop disease detection", applicant: "Rwanda AgriTech Research Group", institution: "National Agricultural Research Centre", submitted: "28 Sep 2026", status: "REVIEW", deadline: "12 Oct 2026", reviewer: "Unassigned" },
  { id: "NRIF-2026-015", title: "Climate-smart irrigation analytics", applicant: "AgriSystems Lab", institution: "Rwanda Institute of Applied Sciences", submitted: "27 Sep 2026", status: "READY", deadline: "12 Oct 2026", reviewer: "M. Uwase" },
  { id: "NRIF-2026-016", title: "Digital health early warning system", applicant: "Health Data Collaborative", institution: "University Research Office", submitted: "26 Sep 2026", status: "FLAGGED", deadline: "12 Oct 2026", reviewer: "J. Ndayisenga" },
];

export default function Home() {
  const [tab, setTab] = useState("screening");
  const [selected, setSelected] = useState(proposals[0]);
  const [org, setOrg] = useState("NCST / NRIF");
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [comparison, setComparison] = useState<string | null>(null);
  const [decisionOpen, setDecisionOpen] = useState(false);
  const [audit, setAudit] = useState<string[]>(["28 Sep 2026 · screening run completed · system"]);
  const [assigned, setAssigned] = useState("Unassigned");

  return (
    <main className="shell">
      <aside className="rail">
        <div className="brand"><span>AI</span><b>AI-SCREENING</b></div>
        <div className="rail-label">WORKSPACE</div>
        {[["overview","Overview"],["screening","Grant Screening"],["publications","Publication Reconciliation"],["review","Human Review"],["integrations","Integrations"]].map(([id,label]) =>
          <button key={id} className={tab === id ? "nav active" : "nav"} onClick={() => setTab(id)}>{label}</button>
        )}
        <div className="rail-foot">NCST / NRIF<br/>AI-assisted · human-controlled</div>
      </aside>
      <section className="workspace">
        <header className="masthead">
          <div><div className="eyebrow">RESEARCH INTELLIGENCE / {tab.replace("-", " ")}</div><h1>{tab === "screening" ? "Proposal review workspace" : tab === "overview" ? "Organization workspace" : tab}</h1><p>{tab === "screening" ? "Inspect evidence, resolve uncertainty, and record a human decision." : "Local-first intelligence infrastructure for research organizations."}</p></div>
          <select value={org} onChange={e => setOrg(e.target.value)}><option>NCST / NRIF</option><option>University Research Office</option><option>Research Institute</option></select>
        </header>

        {tab === "screening" && <Screening selected={selected} setSelected={setSelected} result={result} setResult={setResult} comparison={comparison} setComparison={setComparison} decisionOpen={decisionOpen} setDecisionOpen={setDecisionOpen} audit={audit} setAudit={setAudit} assigned={assigned} setAssigned={setAssigned} />}
        {tab === "overview" && <Overview result={result} />}
        {tab === "review" && <Review audit={audit} />}
        {tab === "publications" && <Publications />}
        {tab === "integrations" && <Integrations org={org} />}
      </section>
    </main>
  );
}

function Screening({selected,setSelected,result,setResult,comparison,setComparison,decisionOpen,setDecisionOpen,audit,setAudit,assigned,setAssigned}:any) {
  const [uploading,setUploading] = useState(false);
  const [error,setError] = useState("");
  const [filter,setFilter] = useState("ALL");
  const active = result ? {
    id: result.proposal_id,
    title: result.extraction?.filename || "Uploaded proposal",
    applicant: "Uploaded document",
    institution: "Source metadata from document"
  } : selected;
  const filtered = proposals.filter(p => filter === "ALL" || p.status === filter);

  async function upload(file:File) {
    setUploading(true);
    setError("");
    setResult(null);
    const body = new FormData();
    body.append("file", file);
    body.append("proposal_id", file.name.replace(/\.[^.]+$/, ""));
    try {
      const res = await fetch(`${API_BASE}/api/v1/grants/screen-document`, {method:"POST",body});
      const data=await res.json();
      if(!res.ok) throw new Error(data.detail || "Screening failed");
      setResult(data);
      setAudit((a:string[]) => [new Date().toLocaleString() + " · live screening run completed · system", ...a]);
    } catch(e) {
      setError(e instanceof Error ? e.message : "Unable to connect to screening API.");
    } finally {
      setUploading(false);
    }
  }

  return <>
    <div className="demo-warning"><b>LIVE MVP / DEMO RULES</b><span>Document analysis is live. Eligibility rules and historical comparison records remain synthetic until authorized institutional data is connected.</span></div>
    <div className="case-head">
      <div><div className="case-id">{active.id || "LIVE"} · {result ? "LIVE RUN" : active.submitted}</div><h2>{active.title}</h2><p>{active.applicant} · {active.institution}</p></div>
      <label className="action-button">{uploading ? "Analyzing…" : "Upload proposal"}<input type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={e=>e.target.files?.[0]&&upload(e.target.files[0])}/></label>
    </div>
    {error && <div className="error">{error}</div>}
    <div className="case-grid">
      <DocumentPane live={result} />
      <Intelligence result={result} openComparison={(kind:string)=>setComparison(kind)} setDecisionOpen={setDecisionOpen} />
    </div>
    <Queue selected={selected} setSelected={setSelected} filter={filter} setFilter={setFilter} rows={filtered} assigned={assigned} setAssigned={setAssigned} />
    {comparison && <Comparison result={result} kind={comparison} close={()=>setComparison(null)} />}
    {decisionOpen && <Decision close={()=>setDecisionOpen(false)} audit={audit} setAudit={setAudit} assigned={assigned} />}
  </>;
}

function DocumentPane({live}:{live:ScreeningResult|null}) {
  const pages = live?.extraction?.pages || [];
  const text = live?.extraction?.text || "";
  const firstPage = pages[0]?.text || text;
  return <section className="document">
    <div className="doc-toolbar"><b>{live?.extraction?.filename || "Proposal.pdf"}</b><span>{live ? `Pages ${live.extraction?.page_count || pages.length || 1}` : "Demo document"}</span></div>
    <div className="doc-body">
      <article className="paper">
        <div className="paper-meta">{live ? "LIVE EXTRACTION · PAGE 1" : "NRIF GRANT PROPOSAL · PAGE 4"}</div>
        <h3>{live ? (live.extraction?.filename || "Uploaded proposal") : "AI-based crop disease detection using machine learning"}</h3>
        {live ? (
          <p className="extracted-text">{firstPage || "No extracted text returned."}</p>
        ) : <>
          <p><b>Applicant:</b> Rwanda AgriTech Research Group</p><p><b>Institution:</b> National Agricultural Research Centre</p>
          <h4>Demo preview</h4><p>Upload a PDF or DOCX to replace this synthetic preview with the document extracted by the live Python API.</p>
        </>}
        <div className="page-number">{live ? "1" : "4"}</div>
      </article>
    </div>
    <div className="extraction-note"><b>EXTRACTION</b><span>{live ? `${live.extraction?.extraction_status || "success"} · ${live.extraction?.page_count || pages.length || 1} pages · SHA-256 ${live.extraction?.file_sha256?.slice(0,16) || "—"}…` : "Upload a PDF or DOCX to run live extraction."}</span></div>
  </section>
}

function Intelligence({result,openComparison,setDecisionOpen}:{result:ScreeningResult|null;openComparison:(kind:string)=>void;setDecisionOpen:(v:boolean)=>void}) {
  const completeness = result?.completeness;
  const checks = result?.eligibility_checks || [];
  const candidates = result?.similarity_candidates || [];
  const overlaps = result?.text_overlap || [];
  const evidence = result?.retrieved_evidence || [];
  const coverage = result?.evidence_coverage;

  const similarityMethod = candidates[0]?.method || "not run";
  const status = result ? (result.run_state === "COMPLETE" ? "COMPLETE" : result.run_state) : "DEMO";
  const confidenceIndex = result && candidates.length
    ? Math.round(Math.max(...candidates.map(c => c.similarity)) * 100)
    : null;

  return <section className="intelligence">
    <div className="intel-title"><div><div className="eyebrow">AI SCREENING ANALYSIS</div><h2>Findings & evidence</h2><p>{result ? `Live screening · run ${status.toLowerCase()}` : "Upload a proposal to generate live findings"}</p></div><div className="state-count">{confidenceIndex !== null ? <><b>{confidenceIndex}%</b><span>top similarity</span></> : <><b>—</b><span>confidence index</span></>}</div></div>

    <div className="readout"><b>READOUT</b><p>{result ? `${completeness?.passed || 0} of ${completeness?.total || 0} configured checks passed; ${checks.filter(c => c.status === "REVIEW" || c.status === "UNKNOWN").length} require reviewer attention.` : "Core sections, eligibility, similarity and evidence will appear here after a live screening run."}</p></div>

    <Finding title="Completeness" status={result ? (completeness?.passed === completeness?.total ? "PASS" : "REVIEW") : "DEMO"} detail={result ? `${completeness?.passed || 0} / ${completeness?.total || 0} checks passed` : "No live run yet"}>
      <p><b>Evidence:</b> {result ? "Completeness was evaluated from the extracted document and configured rules." : "Upload a document to run the backend extraction and screening pipeline."}</p>
    </Finding>

    <Finding title="Eligibility criteria" status={checks.some(c=>c.status==="FAIL") ? "FLAG" : checks.some(c=>c.status==="REVIEW"||c.status==="UNKNOWN") ? "REVIEW" : result ? "PASS" : "DEMO"} detail={result ? `${checks.length} machine-readable criteria` : "Demo rules"}>
      <div className="criteria">{(result ? checks : []).map(c=><div key={c.criterion}><span><i>{c.criterion}</i><b>{c.label}</b><small>{c.evidence}</small></span><em className={c.status.toLowerCase()}>{c.status}</em></div>)}</div>
      {!result && <p><b>Evidence:</b> Synthetic rules remain visible only as a demonstration until official criteria are connected.</p>}
    </Finding>

    <Finding title="Duplicate / semantic similarity" status={candidates.length ? "FLAG" : result ? "PASS" : "DEMO"} detail={result ? `${candidates.length} ranked candidates` : "Historical candidates appear after upload"}>
      <div className="candidate-list">{candidates.map(c=><button key={c.proposal_id} onClick={()=>openComparison("similarity")} className="candidate"><span><b>{String(c.rank).padStart(2,"0")} · {c.proposal_id}</b><small>Lexical {c.lexical_similarity.toFixed(2)} · Semantic {c.semantic_similarity === null ? "disabled" : c.semantic_similarity.toFixed(2)}</small><small>{c.method}</small></span><strong>{c.similarity.toFixed(2)}</strong></button>)}</div>
      {result && candidates.length === 0 && <p>No non-zero historical similarity candidates were returned.</p>}
      {!result && <p>Upload a proposal to retrieve and rank historical candidates.</p>}
      {result && candidates.length > 0 && <><div className="method-note">Method: {similarityMethod}. Similarity is comparison evidence, not a duplicate verdict.</div><button className="text-button" onClick={()=>openComparison("similarity")}>Compare selected candidate →</button></>}
    </Finding>

    <Finding title="Retrieved evidence" status={evidence.length ? "PASS" : result ? "REVIEW" : "DEMO"} detail={result ? `${evidence.length} evidence chunks` : "Evidence retrieval appears after upload"}>
      <div className="evidence-list">{evidence.map(e=><button key={e.chunk_id} onClick={()=>openComparison("evidence")}><span><b>Page {e.page_number} · {e.chunk_id}</b><small>{e.text}</small></span><strong>{e.score.toFixed(2)}</strong></button>)}</div>
      {result && evidence.length === 0 && <p>No evidence chunks were returned.</p>}
    </Finding>

    <Finding title="Text overlap" status={overlaps.length ? "REVIEW" : result ? "PASS" : "DEMO"} detail={result ? `${overlaps.length} records with shared tokens` : "Overlap evidence appears after upload"}>
      <div className="overlap-list">{overlaps.map(o=><button key={o.source_id} onClick={()=>openComparison("overlap")}><span><b>{o.source_id}</b><small>{o.shared_tokens} shared tokens · {o.method}</small></span><strong>{(o.ratio*100).toFixed(1)}%</strong></button>)}</div>
      {result && overlaps.length === 0 && <p>No measurable token overlap was returned.</p>}
    </Finding>

    <div className="provenance"><div className="eyebrow">PROVENANCE / MODEL CONTRACT</div><dl>
      <dt>Document</dt><dd>{result?.extraction?.filename || "Proposal.pdf"} · {result?.extraction?.file_sha256 ? `SHA-256 ${result.extraction.file_sha256.slice(0,16)}…` : "synthetic demo"}</dd>
      <dt>Extraction</dt><dd>PyMuPDF / python-docx · {result?.extraction?.extraction_status || "demo"}</dd>
      <dt>Similarity</dt><dd>{result?.model_versions?.retrieval || "hybrid-retrieval-v0.2"} · {result?.model_versions?.embedding_runtime || "not run"}</dd>
      <dt>Rules</dt><dd>{result?.model_versions?.rules || "nrif-demo-v0.2"} · {result ? "active for this run" : "DEMO ONLY"}</dd>
      <dt>Coverage</dt><dd>{coverage ? `${coverage.retrieved_chunks} chunks · ${coverage.citation_validated_findings} validated citations` : "awaiting live run"}</dd>
    </dl></div>
    <div className="review-bar"><span>Decision belongs to authorized reviewer.</span><button className="dark-button" onClick={()=>setDecisionOpen(true)}>Record decision</button></div>
  </section>
}

function Finding({title,status,detail,children}:any) {
  return <div className="finding"><div className="finding-head"><div><b>{title}</b><small>{detail}</small></div><span className={`status ${status.toLowerCase()}`}>{status}</span></div><div className="finding-body">{children}</div></div>
}

function Queue({selected,setSelected,filter,setFilter,rows,assigned,setAssigned}:any) {
  return <section className="queue"><div className="queue-top"><div><div className="eyebrow">SCREENING REGISTER</div><b>{rows.length} records shown</b></div><div className="queue-tools"><input placeholder="Search proposals"/><select value={filter} onChange={e=>setFilter(e.target.value)}><option>ALL</option><option>REVIEW</option><option>READY</option><option>FLAGGED</option></select><select value={assigned} onChange={e=>setAssigned(e.target.value)}><option>All reviewers</option><option>Unassigned</option><option>M. Uwase</option><option>J. Ndayisenga</option></select></div></div>
    <div className="queue-grid"><div>ID</div><div>Proposal</div><div>Submitted / deadline</div><div>Reviewer</div><div>State</div>{rows.map((p:any)=><button key={p.id} className={selected.id===p.id?"queue-row selected":"queue-row"} onClick={()=>setSelected(p)}><span>{p.id}</span><span><b>{p.title}</b><small>{p.applicant}</small></span><span>{p.submitted}<small>Deadline · {p.deadline}</small></span><span>{p.reviewer}</span><span className={`status ${p.status.toLowerCase()}`}>{p.status}</span></button>)}</div>
  </section>
}

function Comparison({result,kind,close}:{result:ScreeningResult|null;kind:string;close:()=>void}) {
  const candidate = result?.similarity_candidates?.[0];
  const overlap = result?.text_overlap?.[0];
  const evidence = result?.retrieved_evidence?.[0];
  return <div className="overlay"><section className="comparison"><header><div><div className="eyebrow">{kind==="overlap"?"TEXT OVERLAP":kind==="evidence"?"RETRIEVED EVIDENCE":"SEMANTIC SIMILARITY"} / EVIDENCE</div><h2>{kind==="overlap" ? "Overlap evidence" : kind==="evidence" ? "Retrieved evidence" : "Similarity candidate"}</h2><p>{result ? `${result.proposal_id} · live API result · no automatic verdict` : "No live result selected"}</p></div><button className="close" onClick={close}>Close ×</button></header>
    <div className="record-strip"><div><b>Current document</b><span>{result?.extraction?.filename || "No upload"}</span></div><div><b>Evidence source</b><span>{candidate?.proposal_id || overlap?.source_id || evidence?.chunk_id || "—"}</span></div><strong>{candidate ? candidate.similarity.toFixed(2) : overlap ? `${(overlap.ratio*100).toFixed(1)}%` : evidence ? evidence.score.toFixed(2) : "—"}</strong></div>
    <div className="diff">{kind==="evidence" ? <article><div className="diff-head">EXTRACTED EVIDENCE · PAGE {evidence?.page_number || "—"}</div><p>{evidence?.text || "No evidence chunk available."}</p></article> : <><article><div className="diff-head">CURRENT · EXTRACTED DOCUMENT</div><p>{result?.extraction?.text?.slice(0,2500) || "Upload a document to inspect its extracted text."}</p></article><article><div className="diff-head">{kind==="overlap" ? "OVERLAP METADATA" : "HISTORICAL CANDIDATE"}</div><p>{kind==="overlap" ? `${overlap?.source_id || "—"} · ${overlap?.shared_tokens || 0} shared tokens · ${overlap?.method || "—"}` : `${candidate?.proposal_id || "—"} · lexical ${candidate?.lexical_similarity?.toFixed(2) || "—"} · semantic ${candidate?.semantic_similarity === null ? "disabled" : candidate?.semantic_similarity?.toFixed(2) || "—"}`}</p></article></>}</div>
    <footer><span>Evidence is presented for human review; similarity and overlap are not automatic findings of misconduct or duplication.</span><button className="dark-button" onClick={close}>Return to finding</button></footer>
  </section></div>
}

function Decision({close,audit,setAudit,assigned}:any) {
  const [outcome,setOutcome]=useState("Proceed to peer review"); const [reason,setReason]=useState("");
  function save(){if(!reason.trim())return;setAudit((a:string[])=>[`${new Date().toLocaleString()} · ${outcome} · ${assigned==="Unassigned"?"authorized reviewer":assigned}`,...a]);close();}
  return <div className="overlay"><section className="decision"><header><div><div className="eyebrow">HUMAN DECISION / AUDIT EVENT</div><h2>Record screening decision</h2><p>The system cannot record a consequential decision without reviewer rationale.</p></div><button className="close" onClick={close}>Close ×</button></header><div className="decision-grid"><div><label>Outcome</label>{["Proceed to peer review","Return for clarification","Escalate","Do not proceed"].map(x=><button key={x} className={outcome===x?"choice selected":"choice"} onClick={()=>setOutcome(x)}>{x}</button>)}</div><div><label>Reviewer</label><div className="reviewer">{assigned==="Unassigned"?"Current authorized reviewer":assigned}</div><label>Rationale <b>*</b></label><textarea value={reason} onChange={e=>setReason(e.target.value)} placeholder="Explain the evidence reviewed and why this outcome was selected."/><label>Flags reviewed</label><div className="reviewed">✓ Completeness &nbsp; ✓ Eligibility &nbsp; ✓ Similarity &nbsp; ✓ Text overlap</div></div></div><footer><span>{reason.trim()?"Ready to create audit event":"Rationale is required"}</span><button className="dark-button" disabled={!reason.trim()} onClick={save}>Record decision</button></footer></section></div>
}

function Overview({result}:{result:ScreeningResult|null}) {
  return <><div className="overview-lead"><div><div className="eyebrow">ORGANIZATION WORKSPACE</div><h2>Evidence infrastructure for research administration.</h2><p>Connect organizational records to deterministic checks, ML analysis, evidence and accountable human review.</p></div><div className="overview-line"><b>Ingest</b><b>Extract</b><b>Analyze</b><b>Evidence</b><b>Review</b></div></div><div className="register-stats"><div><b>{result ? 1 : 3}</b><span>live screening runs</span></div><div><b>{result?.similarity_candidates?.length || 7}</b><span>similarity candidates</span></div><div><b>{result?.retrieved_evidence?.length || 4}</b><span>evidence chunks</span></div><div><b>{result?.evidence_chain?.length || 0}</b><span>validated evidence links</span></div></div></>
}

function Review({audit}:any){return <><div className="section-intro"><div className="eyebrow">HUMAN REVIEW</div><h2>Decision history</h2><p>Every consequential screening action remains attributable to a reviewer.</p></div><section className="audit"><div className="eyebrow">AUDIT LOG</div>{audit.map((x:string,i:number)=><div key={i}><span>{x}</span><b>{i===0?"SYSTEM":"REVIEWER"}</b></div>)}</section></>}

function Publications(){return <><div className="section-intro"><div className="eyebrow">PUBLICATION RECONCILIATION</div><h2>Local-first synchronization</h2><p>Reconcile available local records first; international sources remain optional connectors.</p></div><section className="publication-list">{[["PUB-1042","AI in African agriculture","98.7%"],["PUB-1077","Machine learning for rural health","93.4%"],["PUB-1091","Climate adaptation analytics","71.2%"]].map(x=><div key={x[0]}><span><b>{x[0]}</b><small>{x[1]}</small></span><strong>{x[2]}</strong><button>Compare</button></div>)}</section></>}

function Integrations({org}:{org:string}){return <><div className="section-intro"><div className="eyebrow">INTEGRATIONS</div><h2>{org}</h2><p>Authorized connectors feed the same evidence and audit pipeline.</p></div><section className="integration-list">{["RIGMS","Historical Applications","Eligibility Rules","Institutional Repository","DOI Metadata"].map(x=><div key={x}><span><b>{x}</b><small>Connector available for authorized configuration</small></span><em>AVAILABLE</em><button>Configure</button></div>)}</section></>}
