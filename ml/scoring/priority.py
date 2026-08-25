import math

DEFAULT_WEIGHTS = {
    "frequency": 0.15,
    "persistence": 0.20,
    "trend": 0.15,
    "severity": 0.20,
    "density": 0.10,
    "network": 0.20,
}

def priority_level(score):
    if score >= 70:
        return "CRITICAL"
    if score >= 55:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"

def calculate_priority(
    frequency,
    persistence,
    trend,
    severity,
    density,
    network,
    weights=None,
):
    """Calculate the V7 Municipal Priority Score.

    Inputs are expected on a 0–100 scale.
    """
    w = weights or DEFAULT_WEIGHTS

    score = (
        w["frequency"] * frequency
        + w["persistence"] * persistence
        + w["trend"] * trend
        + w["severity"] * severity
        + w["density"] * density
        + w["network"] * network
    )

    score = round(float(score), 2)

    return {
        "priority_score": score,
        "priority_level": priority_level(score),
    }
