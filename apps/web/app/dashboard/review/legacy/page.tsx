import Link from "next/link";
import { LegacyScreening } from "../../../../components/legacy/LegacyWorkspace";
import { PageHeader } from "../../../../components/workflow/ui";

export default function LegacyReviewPage() {
  return (
    <>
      <PageHeader
        eyebrow="GRANT SCREENING / REVIEW / LEGACY"
        title="Single-proposal screening workspace"
        intro="The original workspace for screening one proposal outside a grant call. Findings here are not stored in a call."
        actions={<Link className="ghost-button" href="/dashboard/review">← Back to review</Link>}
      />
      <LegacyScreening />
    </>
  );
}
