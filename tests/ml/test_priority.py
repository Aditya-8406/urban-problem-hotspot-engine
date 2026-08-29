from ml.scoring.priority import calculate_priority

def test_priority_score():
    result = calculate_priority(
        frequency=80,
        persistence=90,
        trend=70,
        severity=80,
        density=60,
        network=90,
    )

    assert 0 <= result["priority_score"] <= 100
    assert result["priority_level"] in {
        "CRITICAL", "HIGH", "MEDIUM", "LOW"
    }
