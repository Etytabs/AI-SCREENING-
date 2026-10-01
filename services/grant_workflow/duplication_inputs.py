"""Select proposal content for duplication without changing eligibility inputs."""
from services.grant_workflow.models import ApplicationDocument
from services.ingestion.document import ExtractedDocument


def narrative_documents(
    documents: list[tuple[ApplicationDocument, ExtractedDocument | None]],
) -> list[tuple[ApplicationDocument, ExtractedDocument | None]]:
    # A revised file replaces its earlier version for this check. In particular, an
    # unreadable replacement must not silently fall back to an old readable proposal.
    latest: dict[str, tuple[ApplicationDocument, ExtractedDocument | None]] = {}
    for meta, document in documents:
        previous = latest.get(meta.filename.casefold())
        if previous is None or (meta.version, meta.uploaded_at) > (previous[0].version, previous[0].uploaded_at):
            latest[meta.filename.casefold()] = (meta, document)
    candidates = list(latest.values())
    proposals = [(meta, doc) for meta, doc in candidates if meta.document_type == "proposal"]
    # CVs, declarations, budgets and letters are shared routinely and cannot stand
    # in for a missing research narrative.
    return proposals or [(meta, doc) for meta, doc in candidates if meta.document_type == "other"]
