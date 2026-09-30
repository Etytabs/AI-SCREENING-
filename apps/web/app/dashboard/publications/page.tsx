import { LegacyPublications } from "../../../components/legacy/LegacyWorkspace";
import { PageHeader, SyntheticBadge } from "../../../components/workflow/ui";

export default function PublicationsPage() {
  return (
    <>
      <PageHeader
        eyebrow="GRANT SCREENING / PUBLICATIONS"
        title="Publication reconciliation"
        intro="Carried over unchanged from the earlier prototype. The records below are static demonstration content; the reconciliation service itself is exposed by the publications API."
      />
      <SyntheticBadge origin="SYNTHETIC" />
      <LegacyPublications />
    </>
  );
}
