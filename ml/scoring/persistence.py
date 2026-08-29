def persistence_score(active_months, max_months=36):
    """Score how long a problem remains active."""
    months = max(0.0, float(active_months))
    return min(months / max_months, 1.0) * 100.0
