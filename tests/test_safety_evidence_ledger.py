"""SafetyEvidenceLedger: append-only; critical visible; feeds assurance."""

from __future__ import annotations

import os

from solaris_ai_nn.safety_invariants import (
    SafetyEvidenceKind,
    SafetyEvidenceLedger,
    SafetyEvidenceRecord,
    SafetyInvariantRegistry,
    SafetyInvariantRunner,
)


def test_result_appended(tmp_path):
    led = SafetyEvidenceLedger(state_dir=str(tmp_path))
    led.record(SafetyEvidenceRecord(
        kind=SafetyEvidenceKind.INVARIANT_CHECK, summary="ok", passed=True))
    assert led.snapshot()["record_count"] == 1
    assert os.path.exists(os.path.join(str(tmp_path),
                                       "safety_evidence_ledger.jsonl"))


def test_critical_failure_visible(tmp_path):
    led = SafetyEvidenceLedger(state_dir=str(tmp_path))
    led.record(SafetyEvidenceRecord(
        kind=SafetyEvidenceKind.RED_TEAM_RESULT, summary="leak", passed=False,
        critical=True))
    assert len(led.critical_records()) == 1
    assert led.snapshot()["critical_count"] == 1


def test_ledger_feeds_assurance(tmp_path):
    led = SafetyEvidenceLedger(state_dir=str(tmp_path))
    bundle = SafetyInvariantRunner(registry=SafetyInvariantRegistry()).run_fast(
        {"motor_membrane": {"real_world_authority": False,
                            "firewall_enabled": True,
                            "firewall_can_be_disabled": False,
                            "current_authority": "simulation_only"}})
    led.record_invariant_bundle(bundle)
    assert led.snapshot()["record_count"] == len(bundle.results)
    assert led.completeness_score() >= 0.0


def test_red_team_records_written(tmp_path):
    from solaris_ai_nn.safety_invariants import RedTeamHarness

    led = SafetyEvidenceLedger(state_dir=str(tmp_path))
    led.record_red_team(RedTeamHarness().run_all())
    assert os.path.exists(os.path.join(str(tmp_path), "red_team_results.jsonl"))


def test_missing_evidence_recorded(tmp_path):
    led = SafetyEvidenceLedger(state_dir=str(tmp_path))
    led.record_missing_evidence("motor snapshot")
    recs = [r for r in led.records
            if r.kind == SafetyEvidenceKind.MISSING_EVIDENCE_WARNING]
    assert recs and recs[0].passed is False
