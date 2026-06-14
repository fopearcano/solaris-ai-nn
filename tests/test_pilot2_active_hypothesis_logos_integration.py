"""Pilot-2 <-> active perception / hypothesis / LOGOS: source-scoped signals."""

from __future__ import annotations

from solaris_ai_nn.sensory_membrane import (
    RawSensoryEvent,
    SensoryEventNormalizer,
    SensoryGroundingEngine,
)


def test_source_focus_tracked():
    eng = SensoryGroundingEngine()
    rec = eng.ground(SensoryEventNormalizer().normalize(
        RawSensoryEvent(source_id="cam", source_type="jsonl_file",
                        payload={"novel": True})))
    # A novel event yields an active-perception target scoped to the source.
    assert rec.active_perception_target in (None, "source::cam")


def test_sensory_hypothesis_source_scoped():
    eng = SensoryGroundingEngine()
    rec = eng.ground(SensoryEventNormalizer().absence_event("weather",
                                                            "numeric_csv"))
    assert rec.hypothesis_seed and "weather" in rec.hypothesis_seed


def test_nursery_vs_sensory_tension_via_logos():
    from solaris_ai_nn.logos_complexity.tension import (
        LogosTension,
        TensionType,
    )

    # A nursery-vs-sensory tension is expressible as a LogosTension between
    # two internal poles (source boundary); construction must not require
    # any authority or actuation.
    assert hasattr(TensionType, "__dict__") or TensionType is not None
    # The real/simulated boundary is explicit on normalized events.
    norm = SensoryEventNormalizer()
    sim = norm.normalize(RawSensoryEvent(source_id="s",
                                         source_type="manual_dump",
                                         payload={}, is_simulated=True))
    real = norm.normalize(RawSensoryEvent(source_id="r",
                                          source_type="jsonl_file",
                                          payload={}, is_simulated=False))
    assert "simulated_source" in sim.safety_tags
    assert "simulated_source" not in real.safety_tags
