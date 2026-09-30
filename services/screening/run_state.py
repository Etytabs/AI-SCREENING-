from ml.evidence.state import RunState


def derive_run_state(*, requested: int, completed: int, failed: int, blocked: int = 0) -> RunState:
    if requested < 1:
        raise ValueError("requested must be positive")
    if min(completed, failed, blocked) < 0:
        raise ValueError("run counters cannot be negative")
    if completed + failed + blocked > requested:
        raise ValueError("run counters cannot exceed requested sources")
    if blocked == requested:
        return RunState.BLOCKED
    if failed == requested:
        return RunState.FAILED
    if completed == requested:
        return RunState.COMPLETE
    if completed + failed + blocked == requested:
        return RunState.PARTIAL
    return RunState.RUNNING
