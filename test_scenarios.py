"""Scenario system tests"""
import sys
sys.path.insert(0, ".")

from src.scenarios import list_scenarios, get_scenario


def test_scenario_list():
    scenarios = list_scenarios()
    assert len(scenarios) == 6, f"Expected 6, got {len(scenarios)}"
    ids = [s["id"] for s in scenarios]
    assert "werewolf" in ids
    assert "silly_debate" in ids
    assert "debate" in ids
    print("  scenario_list: OK")


def test_scenario_instantiation():
    for s in list_scenarios():
        scenario = get_scenario(s["id"])
        assert scenario is not None
        assert scenario.name is not None
        assert scenario.min_players >= 2
    print("  scenario_instantiation: OK")


def test_silly_debate_topics():
    from src.scenarios.silly_debate import SILLY_TOPICS
    assert len(SILLY_TOPICS) >= 10
    for t in SILLY_TOPICS:
        assert len(t) == 3
    print("  silly_debate_topics: OK")


if __name__ == "__main__":
    test_scenario_list()
    test_scenario_instantiation()
    test_silly_debate_topics()
    print("All scenario tests passed")
