"""Elo rating system tests"""
import sys
sys.path.insert(0, ".")

from src.elo import (
    _expected_score, get_model_rating, get_leaderboard,
    DEFAULT_ELO
)


def test_expected_score():
    assert abs(_expected_score(1200, 1200) - 0.5) < 0.001
    assert _expected_score(1400, 1200) > 0.7
    assert _expected_score(1000, 1200) < 0.3
    print("  expected_score: OK")


def test_default_rating():
    r = get_model_rating("new_model_test", "test_empty")
    assert r["elo"] == DEFAULT_ELO
    assert r["wins"] == 0
    assert r["games"] == 0
    print("  default_rating: OK")


def test_leaderboard_empty():
    lb = get_leaderboard("nonexistent_scenario")
    assert isinstance(lb, list)
    print("  leaderboard_empty: OK")


if __name__ == "__main__":
    test_expected_score()
    test_default_rating()
    test_leaderboard_empty()
    print("All Elo tests passed")
