def relationship_score(
    spatial_score,
    temporal_score,
    category_prior,
):
    """Directional association score.

    This is an association measure, not proof of causality.
    All inputs should be 0–1.
    """
    return round(
        0.50 * spatial_score
        + 0.25 * temporal_score
        + 0.25 * category_prior,
        3,
    )
