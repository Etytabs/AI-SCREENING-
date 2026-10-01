"""Runs the screening pipeline for one application.

Stages execute in order and persist their progress so the API can report batch status
while jobs run in the background. A failing stage never aborts the run: it produces a
REVIEW_REQUIRED finding and the run finishes as PARTIAL.
"""
import logging
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime
from typing import TYPE_CHECKING

from ml.evidence.state import RunState
from ml.semantic_matching.hybrid import TextEmbedder
from ml.semantic_matching.reranker import CrossEncoderReranker
from services.evidence.coverage import SourceCoverage, source_failure_message
from services.evidence.retrieval import select_evidence
from services.grant_workflow.audit import WorkflowAudit
from services.grant_workflow.documents import parse_metadata
from services.grant_workflow.duplication_inputs import narrative_documents
from services.grant_workflow.literature import PublishedLiteratureSource, build_queries
from services.grant_workflow.models import (
    Applicant,
    Application,
    ApplicationDocument,
    ApplicationStatus,
    CriterionStatus,
    DataOrigin,
    Finding,
    FindingStatus,
    FindingType,
    GrantCall,
    GrantCallStatus,
    Institution,
    RfpCriterion,
    RfpDocument,
    ScreeningRun,
    ScreeningStatus,
    StageName,
    StageStatus,
    utcnow,
)
from services.grant_workflow.providers import GrantDataProvider, ProviderUnavailable
from services.grant_workflow.repository import WorkflowRepository
from services.grant_workflow.screening.completeness import evaluate_completeness
from services.grant_workflow.screening.context import ComparisonRecord, ScreeningContext
from services.grant_workflow.screening.eligibility import evaluate_eligibility
from services.grant_workflow.screening.novelty import evaluate_novelty
from services.grant_workflow.screening.similarity import evaluate_duplication
from services.grant_workflow.screening.text_similarity import evaluate_text_similarity
from services.screening.run_state import derive_run_state

if TYPE_CHECKING:
    from services.grant_workflow.duplication_archive import DuplicationArchive

logger = logging.getLogger(__name__)

PIPELINE_VERSION = "grant-screening-v0.1"
PARAGRAPH_BREAK = "\n\n"
FINISHED_RUN_STATES = {RunState.COMPLETE, RunState.PARTIAL, RunState.BLOCKED, RunState.FAILED}

_STAGE_TYPES = {
    StageName.ELIGIBILITY: FindingType.ELIGIBILITY,
    StageName.COMPLETENESS: FindingType.COMPLETENESS,
    StageName.DUPLICATION: FindingType.DUPLICATION,
    StageName.TEXT_SIMILARITY: FindingType.PLAGIARISM,
    StageName.NOVELTY: FindingType.NOVELTY,
}
_STAGE_FUNCTIONS: dict[StageName, Callable[[ScreeningContext, str], list[Finding]]] = {
    StageName.ELIGIBILITY: evaluate_eligibility,
    StageName.COMPLETENESS: evaluate_completeness,
    StageName.DUPLICATION: evaluate_duplication,
    StageName.TEXT_SIMILARITY: evaluate_text_similarity,
    StageName.NOVELTY: evaluate_novelty,
}


def active_criteria(repo: WorkflowRepository, grant_call_id: str) -> list[RfpCriterion]:
    return sorted(
        (c for c in repo.list(RfpCriterion, grant_call_id=grant_call_id)
         if c.active and c.status != CriterionStatus.REJECTED and c.is_confirmed),
        key=lambda c: c.criterion_code,
    )


class ScreeningOrchestrator:
    def __init__(
        self,
        repo: WorkflowRepository,
        audit: WorkflowAudit,
        providers: list[GrantDataProvider],
        *,
        embedder_factory: Callable[[], TextEmbedder | None] = lambda: None,
        reranker_factory: Callable[[], CrossEncoderReranker | None] = lambda: None,
        duplication_archive: "DuplicationArchive | None" = None,
        duplication_archive_errors: dict[str, str] | None = None,
        literature: PublishedLiteratureSource | None = None,
    ) -> None:
        self.repo = repo
        self.audit = audit
        self.providers = providers
        self.embedder_factory = embedder_factory
        self.reranker_factory = reranker_factory
        self.duplication_archive = duplication_archive
        self.duplication_archive_errors = duplication_archive_errors if duplication_archive_errors is not None else {}
        self.literature = literature if literature is not None else PublishedLiteratureSource()

    # -- persistence helpers -------------------------------------------------
    def _set_stage(self, run: ScreeningRun, stage: StageName, status: StageStatus, message: str | None = None) -> None:
        for state in run.stages:
            if state.stage == stage:
                if status == StageStatus.RUNNING:
                    state.started_at = utcnow()
                elif status in {StageStatus.COMPLETE, StageStatus.FAILED, StageStatus.SKIPPED}:
                    state.completed_at = utcnow()
                state.status = status
                state.message = message
        self.repo.save(run)

    def _documents(self, application: Application) -> list[tuple[ApplicationDocument, object]]:
        docs = sorted(self.repo.list(ApplicationDocument, application_id=application.id), key=lambda d: d.uploaded_at)
        return [(meta, self.repo.get_content(meta.id)) for meta in docs]

    def _rfp_text(self, grant_call_id: str) -> str:
        rfps = sorted(self.repo.list(RfpDocument, grant_call_id=grant_call_id), key=lambda r: r.version)
        if not rfps:
            return ""
        content = self.repo.get_content(rfps[-1].id)
        return content.text if content else ""

    def _universe(self, application: Application) -> tuple[list[ComparisonRecord], list[SourceCoverage]]:
        records: list[ComparisonRecord] = []
        for other in self.repo.list(Application, grant_call_id=application.grant_call_id):
            if other.id == application.id:
                continue
            readable = [
                (meta, doc) for meta, doc in self._documents(other)
                if doc is not None and doc.extraction_status == "success" and doc.text.strip()
            ]
            narrative = [(m, d) for m, d in readable if m.document_type == "proposal"] or readable
            for meta, doc in narrative:
                records.append(ComparisonRecord(
                    record_id=f"{other.application_reference}:{meta.filename}",
                    source_type="same_call_application",
                    title=f"{other.application_reference} · {other.title or meta.filename}",
                    text=doc.text,
                    data_origin=other.data_origin,
                    application_id=other.id,
                    document_meta=meta,
                    document=doc,
                ))
        coverage = [SourceCoverage("same_call_applications", RunState.COMPLETE, f"{len(records)} document(s) compared")]
        for provider in self.providers:
            try:
                historical = provider.historical_records()
            except ProviderUnavailable as exc:
                coverage.append(SourceCoverage(provider.provider_id, RunState.BLOCKED, f"{source_failure_message(provider.provider_id)} {exc}"))
                continue
            except Exception as exc:
                logger.exception("Provider %s failed", provider.provider_id)
                coverage.append(SourceCoverage(provider.provider_id, RunState.FAILED, f"{source_failure_message(provider.provider_id)} {exc}"))
                continue
            records.extend(
                ComparisonRecord(
                    record_id=item.record_id, source_type=item.source_type, title=item.title, text=item.text,
                    data_origin=item.data_origin, year=item.year, outcome=item.outcome,
                )
                for item in historical
            )
            coverage.append(SourceCoverage(provider.provider_id, RunState.COMPLETE, f"{len(historical)} record(s) compared"))
        return records, coverage

    def _duplication_context(self, ctx: ScreeningContext) -> ScreeningContext:
        """Expand only duplication's sources; all other checks keep their inputs."""
        application = ctx.application
        records = [record for record in ctx.universe if record.source_type != "same_call_application"]
        coverage = [source for source in ctx.coverage if source.source_id != "same_call_applications"]
        applications = self.repo.list(Application)
        active_ids = {item.id for item in applications}
        counts = {"same_call_applications": 0, "previous_call_applications": 0}
        unreadable = {key: 0 for key in counts}
        for other in applications:
            if other.id == application.id:
                continue
            same_call = other.grant_call_id == application.grant_call_id
            if not same_call and other.submitted_at > application.submitted_at:
                continue
            source_id = "same_call_applications" if same_call else "previous_call_applications"
            selected = narrative_documents(self._documents(other))
            readable = [
                (meta, doc) for meta, doc in selected
                if doc is not None and meta.extraction_status == "success" and doc.text.strip()
            ]
            if not readable or len(readable) < len(selected):
                unreadable[source_id] += 1
            if not readable:
                continue
            single_meta, single_doc = readable[0] if len(readable) == 1 else (None, None)
            records.append(ComparisonRecord(
                record_id=other.id,
                source_type="same_call_application" if same_call else "historical_application",
                title=f"{other.application_reference} · {other.title or 'Submitted proposal'}",
                text="\n\n".join(
                    "\n\n".join("\n".join(p.lines) if p.lines else p.text for p in doc.pages) or doc.text
                    for _, doc in readable
                ),
                data_origin=other.data_origin, application_id=other.id,
                document_meta=single_meta, document=single_doc,
                year=other.submitted_at.year, outcome="Submitted",
            ))
            counts[source_id] += 1
        for source_id, count in counts.items():
            missing = unreadable[source_id]
            coverage.append(SourceCoverage(
                source_id, RunState.PARTIAL if missing else RunState.COMPLETE,
                f"{count} proposal(s) compared; {missing} application(s) with missing or unreadable narrative content",
            ))
        if self.duplication_archive is not None:
            source_id = self.duplication_archive.provider_id
            try:
                archived = self.duplication_archive.historical_records()
                included = 0
                for item in archived:
                    # Live application records have current versions and page citations;
                    # don't count their persistent snapshots twice or match against self.
                    if item.application_id in active_ids:
                        continue
                    submitted_at = item.provenance.get("submitted_at")
                    if submitted_at and item.grant_call_id != application.grant_call_id:
                        if datetime.fromisoformat(submitted_at) > application.submitted_at:
                            continue
                    records.append(ComparisonRecord(
                        record_id=item.record_id, source_type=item.source_type,
                        title=item.title, text=item.text, data_origin=item.data_origin,
                        application_id=item.application_id, document_meta=item.document_meta,
                        document=item.document, year=item.year, outcome=item.outcome,
                    ))
                    included += 1
                incomplete = bool(self.duplication_archive_errors)
                coverage.append(SourceCoverage(
                    source_id, RunState.PARTIAL if incomplete else RunState.COMPLETE,
                    f"{included} archived project(s) compared"
                    + ("; some submitted proposals could not be persisted" if incomplete else ""),
                ))
            except Exception:
                logger.exception("Duplication comparison library unavailable")
                coverage.append(SourceCoverage(source_id, RunState.FAILED, source_failure_message(source_id)))
        return replace(ctx, documents=narrative_documents(ctx.documents), universe=records, coverage=coverage)

    def _plagiarism_context(self, ctx: ScreeningContext) -> ScreeningContext:
        """Add published literature (OpenAlex) to the plagiarism check's comparison universe."""
        result = self.literature.search(build_queries(ctx.application.title, ctx.narrative_text))
        records = list(ctx.universe) + [
            ComparisonRecord(
                record_id=work.record_id,
                source_type="published_work",
                title=work.title or work.record_id,
                text=PARAGRAPH_BREAK.join(part for part in (work.title, work.abstract) if part),
                data_origin=DataOrigin.PROVIDER,
                year=int(work.publication_date[:4]) if (work.publication_date or "")[:4].isdigit() else None,
                outcome="Published",
                authors=work.authors,
                published_on=work.publication_date,
                publisher=work.journal,
                source_url=work.source_url,
                doi=work.doi,
            )
            for work in result.records
        ]
        coverage = [*ctx.coverage, SourceCoverage(self.literature.provider_id, result.state, result.message)]
        return replace(ctx, universe=records, coverage=coverage)

    def _stage_failure(self, ctx: ScreeningContext, run_id: str, stage: StageName, exc: Exception) -> Finding:
        return Finding(
            screening_run_id=run_id,
            application_id=ctx.application.id,
            grant_call_id=ctx.grant_call.id,
            type=_STAGE_TYPES[stage],
            status=FindingStatus.REVIEW_REQUIRED,
            signal="NOT_ASSESSABLE",
            title=f"{stage.value.replace('_', ' ').title()} could not be completed",
            explanation=f"The {stage.value.lower().replace('_', ' ')} stage failed ({type(exc).__name__}). "
                        "No automated result is available for this check.",
            recommended_action="Assess this check manually or re-run screening.",
            method="stage_failure",
        )

    # -- pipeline ------------------------------------------------------------
    def run(self, run_id: str) -> None:
        run = self.repo.get(ScreeningRun, run_id)
        if run is None:
            return
        application = self.repo.get(Application, run.application_id)
        call = self.repo.get(GrantCall, run.grant_call_id)
        if application is None or call is None:
            run.status, run.error, run.completed_at = RunState.FAILED, "Application or grant call not found", utcnow()
            self.repo.save(run)
            return

        run.status, run.started_at = RunState.RUNNING, utcnow()
        self.repo.save(run)
        self._update_application(application.id, screening_status=ScreeningStatus.RUNNING)
        self.audit.record("screening.run_started", run.created_by, application.id, call.id, run_id=run.id)

        findings: list[Finding] = []
        failed_stages = 0

        self._set_stage(run, StageName.DOCUMENT_EXTRACTION, StageStatus.RUNNING)
        documents = self._documents(application)
        readable_count = sum(1 for _, d in documents if d is not None and d.extraction_status == "success" and d.text.strip())
        self._set_stage(run, StageName.DOCUMENT_EXTRACTION, StageStatus.COMPLETE,
                        f"{readable_count} of {len(documents)} document(s) readable")
        if readable_count == 0:
            findings.append(Finding(
                screening_run_id=run.id, application_id=application.id, grant_call_id=call.id,
                type=FindingType.COMPLETENESS, status=FindingStatus.REVIEW_REQUIRED, signal="NOT_ASSESSABLE",
                title="No readable documents",
                explanation="None of the submitted documents could be read, so no check can be assessed.",
                recommended_action="Open the original files or request readable copies.", method="document_extraction",
            ))
            for stage in StageName:
                if stage != StageName.DOCUMENT_EXTRACTION:
                    self._set_stage(run, stage, StageStatus.SKIPPED, "Blocked: no readable documents")
            self._finish(run, application, call, findings, RunState.BLOCKED)
            return

        self._set_stage(run, StageName.REQUIREMENT_MAPPING, StageStatus.RUNNING)
        criteria = active_criteria(self.repo, call.id)
        applicant = self.repo.get(Applicant, application.applicant_id) if application.applicant_id else None
        institution = self.repo.get(Institution, application.institution_id) if application.institution_id else None
        universe, coverage = self._universe(application)
        readable_docs = [(m, d) for m, d in documents if d is not None and d.extraction_status == "success" and d.text.strip()]
        ctx = ScreeningContext(
            grant_call=call, application=application, applicant=applicant, institution=institution,
            documents=documents, criteria=criteria, rfp_text=self._rfp_text(call.id), universe=universe,
            coverage=coverage, metadata=parse_metadata([(m.document_type, d) for m, d in readable_docs]),
            embedder=self.embedder_factory(), reranker=self.reranker_factory(),
        )
        requirement_map = {}
        for criterion in criteria:
            best = None
            for meta, doc in ctx.readable:
                for candidate in select_evidence(criterion.requirement_text, doc, embedder=ctx.embedder, top_k=1):
                    if best is None or candidate.score > best["score"]:
                        best = {"document_id": meta.id, "filename": meta.filename, "page": candidate.page_number,
                                "score": round(candidate.score, 4)}
            requirement_map[criterion.criterion_code] = best
        run.coverage = {
            "sources": [{"source_id": c.source_id, "state": c.state.value, "message": c.message} for c in coverage],
            "requirement_map": requirement_map,
            "criteria_applied": len(criteria),
        }
        self._set_stage(run, StageName.REQUIREMENT_MAPPING, StageStatus.COMPLETE,
                        f"{len(criteria)} verified requirement(s) mapped to application documents")

        for stage, function in _STAGE_FUNCTIONS.items():
            self._set_stage(run, stage, StageStatus.RUNNING)
            try:
                stage_ctx = ctx
                if stage == StageName.DUPLICATION:
                    stage_ctx = self._duplication_context(ctx)
                    run.coverage["duplication_sources"] = [
                        {"source_id": c.source_id, "state": c.state.value, "message": c.message}
                        for c in stage_ctx.coverage
                    ]
                elif stage == StageName.TEXT_SIMILARITY:
                    stage_ctx = self._plagiarism_context(ctx)
                    run.coverage["plagiarism_sources"] = [
                        {"source_id": c.source_id, "state": c.state.value, "message": c.message}
                        for c in stage_ctx.coverage
                    ]
                produced = function(stage_ctx, run.id)
                findings.extend(produced)
                self._set_stage(run, stage, StageStatus.COMPLETE, f"{len(produced)} finding(s)")
            except Exception as exc:
                logger.exception("Stage %s failed for run %s", stage, run.id)
                failed_stages += 1
                findings.append(self._stage_failure(ctx, run.id, stage, exc))
                self._set_stage(run, stage, StageStatus.FAILED, f"{type(exc).__name__}: {exc}")

        self._set_stage(run, StageName.EVIDENCE, StageStatus.RUNNING)
        findings, stats = self._validate_evidence(findings)
        run.coverage["evidence"] = stats
        self._set_stage(run, StageName.EVIDENCE, StageStatus.COMPLETE,
                        f"{stats['evidence_items']} evidence item(s); {stats['valid_citations']} validated citation(s)")

        status = derive_run_state(requested=len(StageName), completed=len(StageName) - failed_stages, failed=failed_stages)
        self._finish(run, application, call, findings, status)

    @staticmethod
    def _validate_evidence(findings: list[Finding]) -> tuple[list[Finding], dict]:
        items = valid = downgraded = 0
        for finding in findings:
            items += len(finding.evidence)
            valid += sum(1 for e in finding.evidence if e.citation_valid)
            has_application_evidence = any(
                e.source_type in {"application_document", "submission_inventory"} for e in finding.evidence
            )
            if finding.status == FindingStatus.FAIL and not has_application_evidence:
                finding.status = FindingStatus.REVIEW_REQUIRED
                finding.confidence = None
                finding.explanation += " (Downgraded to review: no application evidence could be cited.)"
                downgraded += 1
        return findings, {"evidence_items": items, "valid_citations": valid, "downgraded_findings": downgraded}

    def _update_application(self, application_id: str, **changes) -> Application | None:
        with self.repo.lock:
            application = self.repo.get(Application, application_id)
            if application is None:
                return None
            updated = application.model_copy(update={**changes, "updated_at": utcnow()})
            self.repo.save(updated)
            return updated

    def _finish(self, run: ScreeningRun, application: Application, call: GrantCall,
                findings: list[Finding], status: RunState) -> None:
        for finding in findings:
            self.repo.save(finding)
        run.finding_ids = [f.finding_id for f in findings]
        run.status, run.completed_at = status, utcnow()
        self.repo.save(run)

        if status == RunState.BLOCKED:
            screening_status = ScreeningStatus.BLOCKED
        elif status == RunState.PARTIAL:
            screening_status = ScreeningStatus.PARTIAL
        elif any(f.status != FindingStatus.PASS for f in findings):
            screening_status = ScreeningStatus.REVIEW_REQUIRED
        else:
            screening_status = ScreeningStatus.SCREENED
        self._update_application(
            application.id, screening_status=screening_status, status=ApplicationStatus.IN_REVIEW,
            latest_run_id=run.id, last_screened_at=run.completed_at,
        )
        counts = {s.value: sum(1 for f in findings if f.status == s) for s in FindingStatus}
        self.audit.record("screening.run_completed", "system", application.id, call.id,
                          run_id=run.id, status=status.value, findings=counts)
        self._refresh_call_status(call.id)

    def _refresh_call_status(self, grant_call_id: str) -> None:
        with self.repo.lock:
            call = self.repo.get(GrantCall, grant_call_id)
            if call is None or call.status != GrantCallStatus.SCREENING:
                return
            runs = self.repo.list(ScreeningRun, grant_call_id=grant_call_id)
            if runs and all(r.status in FINISHED_RUN_STATES for r in runs):
                self.repo.save(call.model_copy(update={"status": GrantCallStatus.REVIEW, "updated_at": utcnow()}))
                self.audit.record("grant_call.status_changed", "system", call.id, call.id,
                                  from_status=GrantCallStatus.SCREENING.value, to_status=GrantCallStatus.REVIEW.value)
