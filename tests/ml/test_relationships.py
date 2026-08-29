from ml.relationships.problem_relationships import relationship_score

def test_relationship_score():
    score = relationship_score(1.0, 1.0, 1.0)
    assert score == 1.0
