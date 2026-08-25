def density_score(complaints, active_months):
    """Simple complaints-per-active-month density score."""
    months = max(float(active_months), 1.0)
    return float(complaints) / months
