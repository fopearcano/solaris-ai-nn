"""Sensory <-> Hypothesis/LOGOS: absence seeds; real/simulated boundary."""

from __future__ import annotations

from solaris_ai_nn.sensory_membrane import (
    RawSensoryEvent,
    SensoryEventNormalizer,
    SensoryGroundingEngine,
)


def test_source_absence_creates_hypothesis_seed():
    eng = SensoryGroundingEngine()
    norm = SensoryEventNormalizer()
    absence = norm.absence_event("weather", "numeric_csv")
    rec = eng.ground(absence)
    assert rec.hypothesis_seed is not None
    assert rec.hypothesis_seed.startswith("absence::")


def test_recurring_pattern_creates_hypothesis_seed():
    eng = SensoryGroundingEngine(proto_symbol_threshold=2)
    norm = SensoryEventNormalizer()
    for _ in range(3):
        eng.ground(norm.normalize(RawSensoryEvent(
            source_id="s", source_type="jsonl_file", payload="cycle")))
    seeds = eng.context()["sensory_hypothesis_seeds"]
    assert any("recurring" in s for s in seeds)


def test_real_simulated_boundary_distinguishable():
    norm = SensoryEventNormalizer()
    real = norm.normalize(RawSensoryEvent(source_id="r",
                                          source_type="jsonl_file",
                                          payload={}, is_simulated=False))
    sim = norm.normalize(RawSensoryEvent(source_id="s",
                                         source_type="manual_dump",
                                         payload={}, is_simulated=True))
    # A LOGOS tension can form around the real-vs-simulated source boundary;
    # the boundary is explicit in the normalized events.
    assert real.is_simulated is False and sim.is_simulated is True
    assert "simulated_source" in sim.safety_tags
    assert "simulated_source" not in real.safety_tags
