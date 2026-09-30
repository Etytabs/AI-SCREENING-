import { LegacyPublications } from "../../../components/legacy/LegacyWorkspace";
import { PageHeader } from "../../../components/workflow/ui";

export default function PublicationsPage() {
  return (
    <>
      <PageHeader
        eyebrow="GRANT SCREENING / PUBLICATIONS"
        title="Publication reconciliation"
        intro="Search scholarly sources through the publications API and compare records across sources before reconciliation."
      />
      <LegacyPublications />
    </>
  );
}
