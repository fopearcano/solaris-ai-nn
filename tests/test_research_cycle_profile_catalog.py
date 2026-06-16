"""Research cycle profiles map to the research_cycle source package."""

from __future__ import annotations

from solaris_ai_nn.operator_console.profile_catalog import _source_package


def test_research_cycle_profiles_map_to_research_cycle():
    for pid in ("research_cycle_status", "research_cycle_decision_gate",
                "research_cycle_evidence_ledger", "research_cycle_artifact_graph",
                "research_cycle_next_action", "research_cycle_blocked"):
        assert _source_package(pid) == "research_cycle"


def test_research_baseline_profiles_unaffected():
    assert _source_package("research_baseline_build") == "research_baseline"
    assert _source_package("research_baseline_random") == "research_lab"


def test_other_research_profiles_still_research_lab():
    assert _source_package("research_module_effect") == "research_lab"
    assert _source_package("research_reproducibility") == "research_lab"
