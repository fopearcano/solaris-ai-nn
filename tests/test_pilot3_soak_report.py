"""Pilot3SoakReportBuilder: JSON+Markdown, non-actuation proof, ClaimGuard."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.motor_membrane import (
    EmbodimentSandboxRuntime,
    MotorAction,
    MotorActionScope,
    MotorActionType,
)
from solaris_ai_nn.pilot3 import (
    ActionGroundingAnalyzer,
    FirewallAudit,
    Pilot3Config,
    Pilot3SoakReportBuilder,
)


def _runtime(tmp_path):
    rt = EmbodimentSandboxRuntime(state_dir=str(tmp_path), seed=4)
    rt.initialize()
    rt.submit(MotorAction(MotorActionType.MOVE_EAST,
                          scope=MotorActionScope.SANDBOX_ONLY))
    rt.submit(MotorAction(MotorActionType.MOVE_NORTH,
                          scope=MotorActionScope.FORBIDDEN_REAL_WORLD))
    return rt


def test_json_and_markdown_generated(tmp_path):
    rt = _runtime(tmp_path)
    cfg = Pilot3Config(base_dir=str(tmp_path))
    report = Pilot3SoakReportBuilder(base_dir=str(tmp_path)).build_and_write(
        config=cfg, motor_membrane=rt)
    assert os.path.exists(os.path.join(str(tmp_path),
                                       "PILOT3_SOAK_REPORT.md"))
    assert os.path.exists(os.path.join(str(tmp_path),
                                       "PILOT3_SOAK_REPORT.json"))
    assert "report_paths" in report.sections


def test_non_actuation_proof_included(tmp_path):
    rt = _runtime(tmp_path)
    audit = FirewallAudit().audit(rt)
    report = Pilot3SoakReportBuilder(base_dir=str(tmp_path)).build(
        config=Pilot3Config(base_dir=str(tmp_path)), motor_membrane=rt,
        firewall_audit=audit, grounding=ActionGroundingAnalyzer())
    proof = report.sections["proof_of_non_actuation"]
    assert proof["real_world_authority"] is False
    assert proof["real_world_actions_executed"] == 0


def test_claim_guard_scans_report(tmp_path):
    rt = _runtime(tmp_path)
    report = Pilot3SoakReportBuilder(base_dir=str(tmp_path)).build(
        config=Pilot3Config(base_dir=str(tmp_path)), motor_membrane=rt)
    assert report.claim_guard_safe is True


def test_limitations_present(tmp_path):
    rt = _runtime(tmp_path)
    report = Pilot3SoakReportBuilder(base_dir=str(tmp_path)).build(
        config=Pilot3Config(base_dir=str(tmp_path)), motor_membrane=rt)
    joined = " ".join(report.sections["limitations"]).lower()
    assert "no real-world actuation" in joined
    assert "not real embodiment" in joined
    assert "consciousness" in joined
