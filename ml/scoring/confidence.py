def calibrate_confidence(
    *,
    model_score: float,
    evidence_strength: float,
    agreement: float,
) -> float:
    values = [model_score, evidence_strength, agreement]
    if any(not 0.0 <= value <= 1.0 for value in values):
        raise ValueError("All confidence inputs must be between 0 and 1.")
    return round((model_score * 0.5) + (evidence_strength * 0.3) + (agreement * 0.2), 4)
