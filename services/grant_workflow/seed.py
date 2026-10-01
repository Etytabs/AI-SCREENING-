"""Synthetic demo seeding. Every entity created here is marked DataOrigin.SYNTHETIC."""
import io
import zipfile

from services.grant_workflow.demo_data import (
    DEMO_APPLICATION_FILES,
    DEMO_CALL,
    DEMO_RFP_FILENAME,
    DEMO_RFP_TEXT,
)
from services.grant_workflow.documents import UploadedFile
from services.grant_workflow.jobs import InlineJobRunner
from services.grant_workflow.models import DataOrigin, GrantCall, Role
from services.grant_workflow.service import Actor, GrantWorkflowService

DEMO_SEED_ACTOR = Actor("demo-seed-administrator", Role.GRANT_ADMINISTRATOR)
DEMO_VERIFICATION_NOTE = "Verified automatically by the synthetic demo seed; not a human verification."


def demo_rfp_bytes() -> bytes:
    return DEMO_RFP_TEXT.encode("utf-8")


def demo_applications_zip() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, text in DEMO_APPLICATION_FILES.items():
            archive.writestr(path, text)
    return buffer.getvalue()


def seed_demo(
    service: GrantWorkflowService, *, screen: bool = True, applications: bool = True
) -> GrantCall:
    """Seed the demonstration call.

    With ``applications=False`` only the call and its confirmed requirements are created,
    giving an open call to upload real documents into without the synthetic submissions
    cluttering the screening list.
    """
    call = service.create_call(DEMO_SEED_ACTOR, dict(DEMO_CALL), data_origin=DataOrigin.SYNTHETIC)
    _, criteria = service.upload_rfp(DEMO_SEED_ACTOR, call.id, DEMO_RFP_FILENAME, demo_rfp_bytes())
    for criterion in criteria:
        service.verify_requirement(DEMO_SEED_ACTOR, criterion.id, note=DEMO_VERIFICATION_NOTE)
    service.confirm_requirements(DEMO_SEED_ACTOR, call.id)
    if not applications:
        return service.get_call(call.id)
    files = [UploadedFile(path, text.encode("utf-8")) for path, text in DEMO_APPLICATION_FILES.items()]
    service.upload_applications(DEMO_SEED_ACTOR, call.id, files, data_origin=DataOrigin.SYNTHETIC)
    if screen:
        runner = service.jobs
        service.jobs = InlineJobRunner()
        try:
            service.start_screening(DEMO_SEED_ACTOR, call.id)
        finally:
            service.jobs = runner
    return service.get_call(call.id)
