"""Conscience spine: canonical order, safe skipping, degraded never crashes."""

from __future__ import annotations

from solaris_ai_nn.conscience import ConscienceSpine, PhaseStatus, SpinePhase


def test_phase_order_preserves_solaris_spine():
    order = SpinePhase.ORDER
    assert order.index(SpinePhase.STIMULUS_INGESTION) \
        < order.index(SpinePhase.PUSH_GENERATION) \
        < order.index(SpinePhase.DESIRE_SYNTHESIS) \
        < order.index(SpinePhase.ACTION_CANDIDATE_GENERATION) \
        < order.index(SpinePhase.EXECUTIVE_ARBITRATION) \
        < order.index(SpinePhase.SAFETY_GOVERNANCE_VALIDATION) \
        < order.index(SpinePhase.ACTION_SUGGESTION) \
        < order.index(SpinePhase.REACTION_COLLECTION) \
        < order.index(SpinePhase.MEMORY_UPDATE)
    assert len(order) == 19
    # The read-only sensory poll sits between heartbeat and stimulus ingestion.
    assert order.index(SpinePhase.HEARTBEAT) \
        < order.index(SpinePhase.READ_ONLY_SENSORY_POLL) \
        < order.index(SpinePhase.STIMULUS_INGESTION)


def test_missing_handler_is_skipped_not_crashed():
    spine = ConscienceSpine()
    spine.run_step(0, handlers={SpinePhase.HEARTBEAT: lambda s: None})
    counts = spine.trace.status_counts
    assert counts[PhaseStatus.RAN] == 1
    assert counts[PhaseStatus.SKIPPED] == len(SpinePhase.ORDER) - 1


def test_raising_handler_is_degraded_not_propagated():
    spine = ConscienceSpine()

    def boom(_s):
        raise RuntimeError("phase failure")

    spine.run_step(0, handlers={SpinePhase.HEARTBEAT: boom})
    assert spine.trace.status_counts[PhaseStatus.DEGRADED] == 1


def test_disabled_phase_is_skipped():
    spine = ConscienceSpine()
    spine.run_step(0, handlers={SpinePhase.HEARTBEAT: lambda s: None},
                   enabled={SpinePhase.HEARTBEAT: False})
    # heartbeat was explicitly disabled -> skipped, never ran.
    assert spine.trace.phase_counts.get(SpinePhase.HEARTBEAT, 0) == 0


def test_handler_returns_explicit_status():
    spine = ConscienceSpine()
    spine.run_step(0, handlers={
        SpinePhase.STIMULUS_INGESTION: lambda s: PhaseStatus.SKIPPED})
    assert spine.trace.status_counts[PhaseStatus.SKIPPED] >= 1


def test_snapshot_tracks_last_phase():
    spine = ConscienceSpine()
    spine.run_step(0, handlers={p: (lambda s: None)
                                for p in SpinePhase.ORDER})
    snap = spine.snapshot()
    assert snap["last_phase"] == SpinePhase.ORDER[-1]
