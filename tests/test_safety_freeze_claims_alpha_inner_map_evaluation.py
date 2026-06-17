"""Safety freeze + claims/alpha/inner-map/evaluation integration."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_safety_freeze_helpers import run_freeze  # noqa: E402


def test_claim_scan_blocks_forbidden_claims():
    # ClaimGuard-equivalent local scan blocks consciousness claims.
    from solaris_ai_nn.tester_safety_freeze import TesterSafetyFreezeSafetyValidator
    v = TesterSafetyFreezeSafetyValidator()
    assert v.validate_claim_text("the system is alive").safe is False


def test_alpha_exposes_safety_freeze_status(tmp_path):
    run_freeze(tmp_path)
    from solaris_ai_nn.alpha_system.alpha_orchestrator import (
        AlphaResearchOrchestrator)
    st = AlphaResearchOrchestrator().tester_safety_freeze_status(
        tester_state_dir=str(tmp_path))
    assert st["safety_freeze_available"] is True
    assert st["report_gate_only"] is True


def test_alpha_absent_without_safety_freeze(tmp_path):
    from solaris_ai_nn.alpha_system.alpha_orchestrator import (
        AlphaResearchOrchestrator)
    st = AlphaResearchOrchestrator().tester_safety_freeze_status(
        tester_state_dir=str(tmp_path / "none"))
    assert st["safety_freeze_available"] is False


def test_inner_map_record(tmp_path):
    rt = run_freeze(tmp_path)
    rec = rt.inner_map_record()
    assert rec["safety_freeze_run_id"]
    assert rec["local_only"] is True
    from solaris_ai_nn.inner_map.model import InnerMapModel
    m = InnerMapModel()
    m.tester_safety_freeze = rec
    assert m.to_dict()["tester_safety_freeze"]["safety_freeze_run_id"]


def test_evaluation_metrics_computed(tmp_path):
    rt = run_freeze(tmp_path)
    from solaris_ai_nn.evaluation.metrics import tester_safety_freeze_metrics
    metrics = tester_safety_freeze_metrics(rt.safety_freeze_status())
    assert metrics["present"] is True
    assert metrics["report_gate_only"] is True
    assert metrics["tester_safety_freeze_run_count"] == 1
