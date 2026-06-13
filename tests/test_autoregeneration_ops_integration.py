"""Integration: ops surfaces auto-regeneration status and warnings."""

from __future__ import annotations

from solaris_ai_nn.ops import incident as I


def test_ops_incident_types_registered():
    for name in (I.CRITICAL_DEGRADATION, I.REPAIR_LOOP,
                 I.REPEATED_HARMFUL_REPAIRS, I.UNRECOVERABLE_CHECKPOINT,
                 I.MEMORY_BLOAT_UNRESOLVED, I.SYMBOL_EXPLOSION_UNRESOLVED,
                 I.WORLD_MODEL_CONTRADICTION_UNRESOLVED):
        assert name in I.INCIDENT_TYPES


def test_engine_snapshot_has_ops_fields(tmp_path):
    from solaris_ai_nn.autoregeneration import (
        AutoRegenerationEngine,
        RepairPolicy,
    )

    engine = AutoRegenerationEngine(
        state_dir=tmp_path, policy=RepairPolicy(mode="observe_only"))
    engine.tick({"memory": {"over_budget": ["hot"]}})
    summary = engine.summary()
    for key in ("repair_policy_mode", "latest_degradation_severity",
                "latest_degradation_type", "proposed_repair_count",
                "applied_repair_count", "refused_repair_count",
                "rollback_count", "quarantine_count"):
        assert key in summary


def test_critical_degradation_warns(tmp_path):
    # A critical degradation severity is surfaced by the engine summary; the
    # supervisor records a CRITICAL_DEGRADATION incident from it.
    from solaris_ai_nn.autoregeneration import (
        AutoRegenerationEngine,
        RepairPolicy,
    )
    from solaris_ai_nn.autoregeneration.degradation import (
        DegradationSeverity,
        DegradationSignal,
        DegradationType,
    )

    engine = AutoRegenerationEngine(
        state_dir=tmp_path, policy=RepairPolicy(mode="observe_only"))
    engine.tick({})
    # Inject a critical signal and confirm the summary reflects it.
    engine.diagnostics.last_state.add(DegradationSignal(
        type=DegradationType.STATE_FILE_CORRUPTION,
        severity=DegradationSeverity.CRITICAL, evidence_refs=["corrupt:x"]))
    assert engine.latest_degradation()["severity"] == "critical"
