"""LifeHistory: built from evidence refs; no biography/personhood language."""

from __future__ import annotations

from solaris_ai_nn.developmental_life import (
    LifeHistoryBuilder,
    LifeHistoryEventKind,
)


def test_life_history_built_from_evidence_refs():
    builder = LifeHistoryBuilder()
    ev = builder.record(LifeHistoryEventKind.CONCEPT_BIRTH, tick=1,
                        detail="first stable concept", evidence_refs=["MAT_1"])
    assert ev.evidence_refs == ["MAT_1"]
    assert builder.history.events


def test_build_from_tick_uses_markers_and_regressions():
    class _M:
        marker_type = "first_stable_proto_concept"
        marker_id = "MAT_1"

    class _R:
        reason = "prediction_success_decline"
        regression_id = "REG_1"

    builder = LifeHistoryBuilder()
    builder.build_from_tick(
        {"perceptual_metabolism": {"overload_state": True}},
        maturation_markers=[_M()], regressions=[_R()], tick=2)
    kinds = {e.kind for e in builder.history.events}
    assert LifeHistoryEventKind.CONCEPT_BIRTH in kinds
    assert LifeHistoryEventKind.REGRESSION in kinds
    assert LifeHistoryEventKind.OVERLOAD_DEPRIVATION in kinds


def test_no_biography_or_personhood_language():
    builder = LifeHistoryBuilder()
    builder.record(LifeHistoryEventKind.SIGN_BIRTH, tick=0)
    note = builder.history.to_dict()["note"].lower()
    assert "not biography or personhood" in note
    assert "operational" in builder.history.events[0].to_dict()["note"].lower()
