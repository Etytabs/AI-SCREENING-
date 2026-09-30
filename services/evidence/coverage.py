from dataclasses import dataclass

from ml.evidence.state import RunState


@dataclass(frozen=True)
class SourceCoverage:
    source_id: str
    state: RunState
    message: str


def summarize_coverage(items: list[SourceCoverage]) -> RunState:
    if not items:
        return RunState.BLOCKED
    states = {item.state for item in items}
    if RunState.BLOCKED in states:
        return RunState.BLOCKED
    if RunState.FAILED in states or RunState.PARTIAL in states:
        return RunState.PARTIAL
    if all(item.state == RunState.COMPLETE for item in items):
        return RunState.COMPLETE
    return RunState.RUNNING


def source_failure_message(source_id: str) -> str:
    return f"Source {source_id} could not be searched; this is not equivalent to zero evidence."
