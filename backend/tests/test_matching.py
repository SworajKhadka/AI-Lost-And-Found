import pytest

from core.matching import cosine_similarity, score_pair, shared_keywords


def test_cosine_similarity_basics():
    assert cosine_similarity([1, 0], [1, 0]) == pytest.approx(1.0)
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)
    assert cosine_similarity([], [1]) == 0.0
    assert cosine_similarity([1, 2], [1, 2, 3]) == 0.0


def test_shared_keywords_is_case_insensitive_and_fuzzy():
    assert shared_keywords(["iPhone", "Black"], ["phone", "black"]) == ["black", "iphone"]
    assert shared_keywords(["ab"], ["abc"]) == []  # too short for substring matching
    assert shared_keywords([], ["x"]) == []


def test_semantic_scoring_rewards_similarity_category_and_keywords():
    a = {"embedding": [1.0, 0.0], "category": "laptop", "keywords": ["macbook", "silver"]}
    b = {"embedding": [1.0, 0.0], "category": "laptop", "keywords": ["macbook", "silver"]}
    score, reasons = score_pair(a, b)
    assert score == 100
    assert len(reasons) == 3


def test_semantic_scoring_filters_unrelated_items():
    a = {"embedding": [1.0, 0.0], "category": "laptop", "keywords": ["macbook"]}
    b = {"embedding": [0.0, 1.0], "category": "phone", "keywords": ["iphone"]}
    assert score_pair(a, b)[0] == 0


def test_generic_category_gives_no_bonus():
    a = {"embedding": [1.0, 0.0], "category": "other", "keywords": []}
    b = {"embedding": [0.0, 1.0], "category": "other", "keywords": []}
    assert score_pair(a, b)[0] == 0


def test_legacy_items_without_embeddings_use_keyword_scoring():
    a = {"category": "laptop", "keywords": ["macbook", "laptop", "13inch"]}
    b = {"category": "laptop", "keywords": ["apple", "macbook", "small", "laptop"]}
    score, reasons = score_pair(a, b)
    assert score == 70  # 40 category + 2 x 15 keywords, same as the original algorithm
    assert "Same category: laptop" in reasons


def test_legacy_uncategorized_items_do_not_match_on_category_alone():
    a = {"category": "uncategorized", "keywords": []}
    b = {"category": "uncategorized", "keywords": []}
    assert score_pair(a, b)[0] == 0


def _vector_with_similarity(target: float) -> list[float]:
    """A unit vector whose cosine similarity with [1, 0] is `target`."""
    return [target, (1 - target**2) ** 0.5]


@pytest.mark.parametrize(
    ("similarity", "should_match"),
    [
        (0.93, True),   # same MacBook, owner vs finder (measured in production)
        (0.83, False),  # headphones vs iPhone (measured)
        (0.81, False),  # MacBook vs iPhone (measured)
        (0.77, False),  # MacBook vs vague "item found" post (measured)
    ],
)
def test_thresholds_match_real_gemini_similarity_levels(similarity, should_match):
    source = {"embedding": [1.0, 0.0], "category": "other", "keywords": []}
    candidate = {"embedding": _vector_with_similarity(similarity), "category": "phone", "keywords": []}
    score, _ = score_pair(source, candidate)
    assert (score > 0) is should_match
