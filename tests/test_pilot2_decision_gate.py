"""Pilot-2 decision gate: unsafe blocks, grounding extends, no actuation."""

from __future__ import annotations

from solaris_ai_nn.pilot2 import (
    GroundingAnalysis,
    Pilot2DecisionGate,
    Pilot2DecisionOption,
    SourceReliabilityMonitor,
)


def _grounding(strong=True):
    ga = GroundingAnalysis()
    if strong:
        ga.add("proto_symbol", provenance_complete=True, repeated_pattern=True,
               persistent=True, improves_prediction_or_compression=True,
               cross_module_support=True, evidence_refs=["r1"])
    else:
        ga.add("proto_symbol", provenance_complete=True, repeated_pattern=True,
               evidence_refs=["r1"])
    return ga


def test_unsafe_source_blocks_next_phase():
    mon = SourceReliabilityMonitor()
    mon.observe_poll("evil", success=True, events=10, unsafe=True)
    result = Pilot2DecisionGate().decide(grounding=_grounding(), reliability=mon)
    assert result.blockers
    assert result.recommendation == Pilot2DecisionOption.REVISE_SENSORY_MEMBRANE


def test_adequate_grounding_can_extend_soak():
    result = Pilot2DecisionGate().decide(grounding=_grounding(strong=True))
    assert result.recommendation == Pilot2DecisionOption.EXTEND_READ_ONLY_SOAK
    assert not result.blockers


def test_command_confusion_blocks():
    result = Pilot2DecisionGate().decide(grounding=_grounding(),
                                         command_confusion_count=1)
    assert any("command" in b for b in result.blockers)
    assert result.recommendation == Pilot2DecisionOption.REVISE_SENSORY_MEMBRANE


def test_actuation_never_an_enabled_action():
    result = Pilot2DecisionGate().decide(grounding=_grounding())
    assert result.recommendation in Pilot2DecisionOption.ALL
    # No option is "act on the environment"; pilot-3 embodiment is planning.
    assert "actuat" not in result.recommendation


def test_weak_grounding_repeats_with_curated_sources():
    result = Pilot2DecisionGate().decide(grounding=_grounding(strong=False))
    assert result.recommendation == \
        Pilot2DecisionOption.REPEAT_PILOT2_WITH_CURATED_SOURCES
