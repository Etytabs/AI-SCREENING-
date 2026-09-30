"use client";

import { useState } from "react";
import { API_BASE } from "../../lib/api";

const proposals = [
  { id: "NRIF-2026-014", title: "AI-based crop disease detection", applicant: "Rwanda AgriTech Research Group", institution: "National Agricultural Research Centre", submitted: "28 Sep 2026", status: "REVIEW", deadline: "12 Oct 2026", reviewer: "Unassigned", score: 0.94, duplicate: 2 },
  { id: "NRIF-2026-015", title: "Climate-smart irrigation analytics", applicant: "AgriSystems Lab", institution: "Rwanda Institute of Applied Sciences", submitted: "27 Sep 2026", status: "READY", deadline: "12 Oct 2026", reviewer: "M. Uwase", score: 0.61, duplicate: 0 },
  { id: "NRIF-2026-016", title: "Digital health early warning system", applicant: "Health Data Collaborative", institution: "University Research Office", submitted: "26 Sep 2026", status: "FLAGGED", deadline: "12 Oct 2026", reviewer: "J. Ndayisenga", score: 0.43, duplicate: 1 },
];

const criteria = [
  ["C01", "Eligible institution", "PASS", "Institution identified on page 1."],
  ["C02", "Project within funding scope", "PASS", "Agricultural research and AI methodology detected."],
  ["C03", "Methodology described", "PASS", "Methodology section detected on page 4."],
  ["C04", "Required partner letter", "UNKNOWN", "No partner letter detected in supplied document."],
  ["C05", "Ethics / regulatory approval", "UNKNOWN", "No approval reference detected; requires reviewer confirmation."],
  ["C06", "Funding ceiling", "REVIEW", "Budget section detected; amount extraction is not yet configured."],
];

const candidates = [
  { id: "NRIF-2024-118", score: 0.94, title: "AI-based crop disease detection using machine learning for maize farmers", applicant: "Rwanda AgriTech Research Group", institution: "National Agricultural Research Centre", year: "2024", outcome: "Completed / archived" },
  { id: "NRIF-2025-031", score: 0.61, title: "Climate-smart irrigation analytics for smallholder agriculture", applicant: "AgriSystems Lab", institution: "Rwanda Institute of Applied Sciences", year: "2025", outcome: "Funded" },
  { id: "NRIF-2024-074", score: 0.43, title: "Digital health early warning and referral system", applicant: "Health Data Collaborative", institution: "University Research Office", year: "2024", outcome: "Not selected" },
];

const overlaps = [
  { term: "annotated maize leaf images", currentPage: 4, historicalPage: 6, ratio: "6.4%" },
  { term: "machine learning models", currentPage: 4, historicalPage: 6, ratio: "3.1%" },
];

export function LegacyScreening() {
  const [selected, setSelected] = useState(proposals[0]);
  const [result, setResult] = useState<any>(null);
  const [comparison, setComparison] = useState<any>(null);
  const [decisionOpen, setDecisionOpen] = useState(false);
  const [audit, setAudit] = useState<string[]>(["28 Sep 2026 · screening run completed · system"]);
  const [assigned, setAssigned] = useState("Unassigned");
  return <Screening selected={selected} setSelected={setSelected} result={result} setResult={setResult} comparison={comparison} setComparison={setComparison} decisionOpen={decisionOpen} setDecisionOpen={setDecisionOpen} audit={audit} setAudit={setAudit} assigned={assigned} setAssigned={setAssigned} />;
}

function Screening({selected,setSelected,result,setResult,comparison,setComparison,decisionOpen,setDecisionOpen,audit,setAudit,assigned,setAssigned}:any) {
  const [uploading,setUploading] = useState(false);
  const [error,setError] = useState("");
  const [filter,setFilter] = useState("ALL");
  const [fileName,setFileName] = useState("");
  const active = result || selected;
  const filtered = proposals.filter(p => filter === "ALL" || p.status === filter);
  async function upload(file:File) {
    if (!/\.(pdf|docx)$/i.test(file.name)) { setError("Only PDF and DOCX proposals are supported."); return; }
    setUploading(true); setError(""); setResult(null); setFileName(file.name);
    const body = new FormData(); body.append("file", file); body.append("proposal_id", file.name.replace(/\.[^.]+$/, ""));
    try { const res = await fetch(`${API_BASE}/api/v1/grants/screen-document`, {method:"POST",body}); const data=await res.json(); if(!res.ok) throw new Error(data.detail || "Screening failed"); setResult(data); setAudit((a:string[]) => [new Date().toLocaleString() + " · screening run completed · system", ...a]); }
    catch(e){setError(e instanceof Error ? e.message : "Unable to connect to screening API.");}
    finally{setUploading(false);}
  }
  return <>
    <div className="demo-warning"><b>DEMONSTRATION MODE</b><span>NRIF rules and historical records shown here are synthetic. They are not official eligibility criteria and must not be used for production decisions.</span></div>
    <div className="case-head">
      <div><div className="case-id">{active.id || active.proposal_id} · {active.submitted || "LIVE RUN"}</div><h2>{active.title || fileName}</h2><p>{active.applicant || "Uploaded document"} · {active.institution || "Source metadata pending"}</p></div>
    </div>
    {error && <div className="error">{error}</div>}
    <div className="case-grid">
      <DocumentPane live={result} fileName={fileName} uploading={uploading} onFile={upload} />
      <Intelligence result={result} openComparison={(kind:string)=>setComparison(kind)} setDecisionOpen={setDecisionOpen} />
    </div>
    <Queue selected={selected} setSelected={setSelected} filter={filter} setFilter={setFilter} rows={filtered} assigned={assigned} setAssigned={setAssigned} />
    {comparison && <Comparison kind={comparison} close={()=>setComparison(null)} />}
    {decisionOpen && <Decision close={()=>setDecisionOpen(false)} audit={audit} setAudit={setAudit} assigned={assigned} />}
  </>;
}

const ACCEPTED_TYPES = ".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document";

function FileInput({onFile,disabled}:{onFile:(file:File)=>void;disabled?:boolean}) {
  return <input type="file" accept={ACCEPTED_TYPES} disabled={disabled} onChange={e=>{const file=e.target.files?.[0]; if(file) onFile(file); e.target.value="";}}/>;
}

function DocumentPane({live,fileName,uploading,onFile}:any) {
  const [dragging,setDragging] = useState(false);
  const [showSample,setShowSample] = useState(false);
  const extraction = live?.extraction;
  const failed = !!live && extraction?.extraction_status !== "success";
  const showLive = !!live && !failed && !uploading;
  const showDemo = !live && !uploading && showSample;
  const docType = extraction?.content_type?.includes("pdf") ? "PDF" : "DOCX";
  function handleDrop(event: React.DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files[0];
    if (file && !uploading) onFile(file);
  }
  return <section className="document">
    <div className="doc-toolbar">
      <b>{uploading || live ? fileName : showDemo ? "Sample proposal (demo)" : "No document uploaded"}</b>
      {showLive && <span>{extraction.page_count} page{extraction.page_count === 1 ? "" : "s"} · {docType}</span>}
      {!live && !uploading && <button onClick={()=>setShowSample(!showSample)}>{showSample ? "Back to upload" : "View sample"}</button>}
      {(showLive || failed) && !uploading && <label className="doc-upload">Upload another<FileInput onFile={onFile}/></label>}
    </div>
    <div className="doc-body">
      {showLive ? extraction.pages.map((page:any) => <article className="paper" key={page.page_number}>
        <div className="paper-meta">{fileName} · PAGE {page.page_number}</div>
        <p className="paper-text">{page.text || "No text layer detected on this page. It may be scanned and require OCR."}</p>
        <div className="page-number">{page.page_number}</div>
      </article>) : !showDemo ? <label className={`dropzone${dragging ? " dragging" : ""}${uploading ? " busy" : ""}`} onDragOver={e=>{e.preventDefault();setDragging(true)}} onDragLeave={()=>setDragging(false)} onDrop={handleDrop}>
        <FileInput onFile={onFile} disabled={uploading}/>
        <div className="dropzone-icon">↑</div>
        <b>{uploading ? `Analyzing ${fileName}…` : failed ? "The document could not be read" : "Upload a grant proposal"}</b>
        <span>{uploading ? "Extracting text and running completeness, eligibility and similarity checks." : failed ? (extraction?.error || "Text extraction failed.") + " Try another file." : "Drag and drop a file here, or click to browse."}</span>
        {!uploading && <em>{failed ? "Choose another file" : "Choose file"}</em>}
        <small>PDF or DOCX · text is extracted page by page for evidence and provenance</small>
      </label> : <article className="paper">
        <div className="paper-meta">NRIF GRANT PROPOSAL · PAGE 4</div>
        <h3>AI-based crop disease detection using machine learning</h3>
        <p><b>Applicant:</b> Rwanda AgriTech Research Group</p><p><b>Institution:</b> National Agricultural Research Centre</p>
        <h4>1. Objectives</h4><p>The project proposes a machine-learning system to identify common crop diseases from field images and provide early alerts to extension workers and farmers.</p>
        <h4>2. Methodology</h4><p>The proposed approach combines <mark>machine learning models trained on annotated maize leaf images</mark> with a mobile-assisted field data collection workflow.</p>
        <h4>3. Expected Outcomes</h4><p>A validated prototype, an annotated image dataset, field deployment guidance, and training materials for agricultural extension teams.</p>
        <h4>4. Workplan</h4><p>Data collection and annotation will precede model development, field validation, and deployment preparation.</p>
        <h4>5. Budget</h4><p>Personnel, data collection, compute, field validation, training, and project administration are included in the proposed budget.</p>
        <div className="page-number">4</div>
      </article>}
    </div>
    <div className="extraction-note"><b>EXTRACTION QUALITY</b><span>{showLive ? "Live extraction completed. Page-level quality will be reported when provenance is page-aware." : failed ? "Extraction failed. No findings were produced from this document." : showDemo ? "Text layer appears readable in this demo. Scanned pages and complex tables require quality checks." : "Upload a document to extract its text and assess extraction quality."}</span></div>
  </section>
}

function Intelligence({result,openComparison,setDecisionOpen}:any) {
  return <section className="intelligence">
    <div className="intel-title"><div><div className="eyebrow">AI SCREENING ANALYSIS</div><h2>Findings & evidence</h2><p>{result ? "Live screening result · human review required" : "Demo evidence · human review required"}</p></div><div className="state-count"><b>4</b><span>passed</span><b>2</b><span>review</span></div></div>
    <div className="readout"><b>READOUT</b><p>Core sections are present. Similarity and unresolved eligibility signals require comparison or reviewer confirmation.</p></div>

    <Finding title="Completeness" status="PASS" detail={result ? `${result.completeness?.passed || 0} / ${result.completeness?.total || 0} configured rules passed` : "4 / 4 configured demo checks detected"}><p><b>Evidence:</b> Title, abstract/summary, methodology and budget indicators detected.</p><button className="text-button">Open evidence · pages 1–4</button></Finding>

    <Finding title="Eligibility criteria" status="REVIEW" detail="6 machine-readable criteria"><div className="criteria">{criteria.map(c=><div key={c[0]}><span><i>{c[0]}</i><b>{c[1]}</b><small>{c[3]}</small></span><em className={c[2].toLowerCase()}>{c[2]}</em></div>)}</div></Finding>

    <Finding title="Duplicate / semantic similarity" status="FLAG" detail="3 ranked candidates · threshold 0.70"><div className="candidate-list">{candidates.map((c,i)=><button key={c.id} onClick={()=>openComparison("similarity")} className="candidate"><span><b>{String(i+1).padStart(2,"0")} · {c.id}</b><small>{c.title}</small><small>{c.applicant} · {c.year} · {c.outcome}</small></span><strong>{c.score.toFixed(2)}</strong></button>)}</div><div className="method-note">Method: token Jaccard baseline · candidate pool: 247 historical proposals. Lexical matching may miss paraphrased similarity.</div><button className="text-button" onClick={()=>openComparison("similarity")}>Compare selected candidate →</button></Finding>

    <Finding title="Text overlap" status="REVIEW" detail="2 evidence spans · 9.5% combined"><div className="overlap-list">{overlaps.map(o=><button key={o.term} onClick={()=>openComparison("overlap")}><span>“{o.term}”</span><small>Current p.{o.currentPage} ↔ historical p.{o.historicalPage}</small><strong>{o.ratio}</strong></button>)}</div><button className="text-button" onClick={()=>openComparison("overlap")}>Open passage comparison →</button></Finding>

    <div className="provenance"><div className="eyebrow">PROVENANCE / MODEL CONTRACT</div><dl><dt>Document</dt><dd>Proposal.pdf · SHA-256 verified</dd><dt>Extraction</dt><dd>PyMuPDF · extraction-v0.1</dd><dt>Similarity</dt><dd>token_jaccard_baseline-v0.1</dd><dt>Rules</dt><dd>nrif-demo-v0.1 · <b>NOT OFFICIAL</b></dd></dl></div>
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

function Comparison({kind,close}:any) {
  const isOverlap=kind==="overlap";
  return <div className="overlay"><section className="comparison"><header><div><div className="eyebrow">{isOverlap?"TEXT OVERLAP":"SEMANTIC SIMILARITY"} / EVIDENCE COMPARISON</div><h2>{isOverlap ? "Compare matching passages" : "Compare historical candidate"}</h2><p>NRIF-2026-014 ↔ NRIF-2024-118 · evidence view · no automatic verdict</p></div><button className="close" onClick={close}>Close ×</button></header>
    <div className="record-strip"><div><b>Current proposal</b><span>Rwanda AgriTech Research Group · 2026</span></div><div><b>Historical record</b><span>Rwanda AgriTech Research Group · 2024 · Completed / archived</span></div><strong>{isOverlap?"2 spans":"0.94 similarity"}</strong></div>
    <div className="diff"><article><div className="diff-head">CURRENT · PAGE 4</div><h3>2. Methodology</h3><p>The proposed approach combines <mark>machine learning models trained on annotated maize leaf images</mark> with a mobile-assisted field data collection workflow.</p><p>The project will validate the model using field data collected by extension teams.</p></article><article><div className="diff-head">HISTORICAL · PAGE 6</div><h3>3. Methodology</h3><p>The proposed approach uses <mark>machine learning models trained on annotated maize leaf images</mark> before deployment through agricultural extension teams.</p><p>The earlier project validated a model using field-collected maize disease data.</p></article></div>
    <footer><span>Evidence source: extracted text · page references · {isOverlap?"set-token-overlap":"token_jaccard_baseline-v0.1"}</span><button className="dark-button" onClick={close}>Return to finding</button></footer>
  </section></div>
}

function Decision({close,audit,setAudit,assigned}:any) {
  const [outcome,setOutcome]=useState("Proceed to peer review"); const [reason,setReason]=useState("");
  function save(){if(!reason.trim())return;setAudit((a:string[])=>[`${new Date().toLocaleString()} · ${outcome} · ${assigned==="Unassigned"?"authorized reviewer":assigned}`,...a]);close();}
  return <div className="overlay"><section className="decision"><header><div><div className="eyebrow">HUMAN DECISION / AUDIT EVENT</div><h2>Record screening decision</h2><p>The system cannot record a consequential decision without reviewer rationale.</p></div><button className="close" onClick={close}>Close ×</button></header><div className="decision-grid"><div><label>Outcome</label>{["Proceed to peer review","Return for clarification","Escalate","Do not proceed"].map(x=><button key={x} className={outcome===x?"choice selected":"choice"} onClick={()=>setOutcome(x)}>{x}</button>)}</div><div><label>Reviewer</label><div className="reviewer">{assigned==="Unassigned"?"Current authorized reviewer":assigned}</div><label>Rationale <b>*</b></label><textarea value={reason} onChange={e=>setReason(e.target.value)} placeholder="Explain the evidence reviewed and why this outcome was selected."/><label>Flags reviewed</label><div className="reviewed">✓ Completeness &nbsp; ✓ Eligibility &nbsp; ✓ Similarity &nbsp; ✓ Text overlap</div></div></div><footer><span>{reason.trim()?"Ready to create audit event":"Rationale is required"}</span><button className="dark-button" disabled={!reason.trim()} onClick={save}>Record decision</button></footer></section></div>
}

export function LegacyPublications(){return <><div className="section-intro"><div className="eyebrow">PUBLICATION RECONCILIATION</div><h2>Local-first synchronization</h2><p>Reconcile available local records first; international sources remain optional connectors.</p></div><section className="publication-list">{[["PUB-1042","AI in African agriculture","98.7%"],["PUB-1077","Machine learning for rural health","93.4%"],["PUB-1091","Climate adaptation analytics","71.2%"]].map(x=><div key={x[0]}><span><b>{x[0]}</b><small>{x[1]}</small></span><strong>{x[2]}</strong><button>Compare</button></div>)}</section></>}
