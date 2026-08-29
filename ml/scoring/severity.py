def severity_score(severity):
    """Convert a 1–5 severity value to a 0–100 score."""
    if severity is None:
        return 0.0
    value = max(1.0, min(5.0, float(severity)))
    return (value - 1.0) / 4.0 * 100.0
