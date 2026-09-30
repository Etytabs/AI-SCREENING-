import Link from "next/link";
import styles from "./page.module.css";

const icon = { width: 20, height: 20, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
const ShieldIcon = () => <svg {...icon}><path d="M12 3l7 3v5c0 4.5-3 8.3-7 10-4-1.7-7-5.5-7-10V6l7-3z" /><path d="M9 12l2 2 4-4" /></svg>;
const DocumentIcon = () => <svg {...icon}><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5z" /><path d="M14 3v5h5M9 13h6M9 17h6" /></svg>;
const SparkIcon = () => <svg {...icon}><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3z" /><path d="M19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8L19 16z" /></svg>;
const ArrowIcon = () => <svg {...icon} width={18} height={18}><path d="M5 12h14M13 6l6 6-6 6" /></svg>;

const steps = [
  { label: "Proposal", detail: "Upload a PDF or DOCX grant proposal for text extraction.", Icon: DocumentIcon },
  { label: "AI comparison", detail: "Completeness, eligibility, similarity and overlap evidence.", Icon: SparkIcon, active: true },
  { label: "Human review", detail: "An authorized reviewer records the decision and rationale.", Icon: ShieldIcon },
];

export default function Home() {
  return (
    <main className={styles.screen}>
      <header className={styles.header}>
        <div className={styles.brand}>
          <span className={styles.brandMark}><ShieldIcon /></span>
          <div><b>AI-SCREENING</b><small>Research Intelligence</small></div>
        </div>
        <Link href="/dashboard" className={styles.headerLink}>Dashboard <ArrowIcon /></Link>
      </header>

      <section className={styles.hero}>
        <div className={styles.pitch}>
          <div className={styles.kicker}>AI-SCREENING · Research intelligence platform</div>
          <h1>Evidence in focus.<br />People in control.</h1>
          <p>A private workspace for grant screening and publication reconciliation, with source-backed evidence and accountable human review.</p>
          <Link href="/dashboard" className={styles.cta}><span>Open dashboard</span><ArrowIcon /></Link>
        </div>
        <ol className={styles.steps}>
          {steps.map(({ label, detail, Icon, active }, i) => <li key={label} className={active ? styles.stepActive : ""}>
            <span className={styles.stepIcon}><Icon /></span>
            <div><small>Step {i + 1}</small><b>{label}</b><p>{detail}</p></div>
          </li>)}
        </ol>
      </section>

      <div className={styles.footnote}>Synthetic demonstration · live connectors require approved access</div>
    </main>
  );
}
