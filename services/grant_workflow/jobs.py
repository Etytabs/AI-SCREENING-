"""Background job boundary.

Screening is submitted through `JobRunner` so API requests never block on batch work.
`ThreadPoolJobRunner` is the MVP implementation; a Celery/RQ runner only needs to
implement `submit` and call the same service entry point.
"""
import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Protocol

logger = logging.getLogger(__name__)


class JobRunner(Protocol):
    def submit(self, job: Callable[[], None]) -> None: ...


def _guarded(job: Callable[[], None]) -> None:
    try:
        job()
    except Exception:
        logger.exception("Background screening job failed")


class ThreadPoolJobRunner:
    def __init__(self, max_workers: int = 2) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="screening")

    def submit(self, job: Callable[[], None]) -> None:
        self._executor.submit(_guarded, job)


class InlineJobRunner:
    """Runs jobs synchronously; used by tests and demo seeding."""

    def submit(self, job: Callable[[], None]) -> None:
        _guarded(job)
