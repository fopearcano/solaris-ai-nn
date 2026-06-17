"""RC integration: forbidden claims block, alpha status, inner map, evaluation."""

from __future__ import annotations

from _tester_rc_helpers import run_rc, seed_ready_state

from solaris_ai_nn.alpha_system.alpha_orchestrator import (
    AlphaResearchOrchestrator,
)
from solaris_ai_nn.inner_map.model import InnerMapModel


def test_forbidden_claims_block_rc():
    from solaris_ai_nn.tester_release_candidate import TesterRCReadinessGate

    r = TesterRCReadinessGate().evaluate({
        "packaging": {"packaging_available": True, "doctor_status": "pass",
                      "clean_machine_readiness": "pass"},
        "safety_freeze": {"safety_freeze_available": True, "readiness": "ready",
                          "forbidden_claim_count": 1},
        "fixture": {"fixture_demo_available": True, "fixture_passed": True},
        "artifacts": {"missing_required": []}})
    assert r.status == "critical_blocked"


def test_alpha_exposes_rc_status(tmp_path):
    base = str(tmp_path / "ready")
    seed_ready_state(base)
    run_rc(base)
    st = AlphaResearchOrchestrator().tester_release_candidate_status(base)
    assert st["rc_available"] is True
    assert st["published"] is False
    assert st["readiness"] in ("ready_for_first_tester", "ready_with_warnings",
                               "blocked", "critical_blocked", "unknown")


def test_alpha_rc_absent(tmp_path):
    st = AlphaResearchOrchestrator().tester_release_candidate_status(
        str(tmp_path / "nope"))
    assert st["rc_available"] is False


def test_inner_map_field_and_record(tmp_path):
    rt = run_rc(str(tmp_path / "rc"))
    rec = rt.inner_map_record()
    model = InnerMapModel()
    model.tester_release_candidate = rec
    d = model.to_dict()
    assert d["tester_release_candidate"]["rc_id"] == rt.rc_id
    assert d["tester_release_candidate"]["local_only"] is True


def test_evaluation_metrics_computed(tmp_path):
    from solaris_ai_nn.evaluation.metrics import (
        tester_release_candidate_metrics as rc_metrics,
    )
    rt = run_rc(str(tmp_path / "rc"))
    m = rc_metrics(rt.rc_status())
    assert m["present"] is True
    assert m["tester_rc_run_count"] == 1
    assert m["published"] is False
    assert m["is_consciousness_or_personhood"] is False
