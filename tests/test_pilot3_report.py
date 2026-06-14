"""Pilot3ReportBuilder: builds a claim-safe report with non-actuation proof."""

from __future__ import annotations

import os

from solaris_ai_nn.motor_membrane import (
    EmbodimentSandboxRuntime,
    MotorAction,
    MotorActionScope,
    MotorActionType,
    Pilot3ReportBuilder,
)


def _runtime(tmp_path):
    rt = EmbodimentSandboxRuntime(state_dir=str(tmp_path))
    rt.initialize()
    rt.submit(MotorAction(MotorActionType.MOVE_EAST,
                          scope=MotorActionScope.SANDBOX_ONLY))
    rt.submit(MotorAction(MotorActionType.MOVE_NORTH,
                          scope=MotorActionScope.FORBIDDEN_REAL_WORLD))
    return rt


def test_report_has_non_actuation_proof(tmp_path):
    rt = _runtime(tmp_path)
    report = Pilot3ReportBuilder(base_dir=str(tmp_path)).build(runtime=rt)
    proof = report.sections["proof_of_non_actuation"]
    assert proof["real_world_authority"] is False


def test_report_is_claim_guard_safe(tmp_path):
    rt = _runtime(tmp_path)
    report = Pilot3ReportBuilder(base_dir=str(tmp_path)).build(runtime=rt)
    assert report.claim_guard_safe is True


def test_report_lists_limitations(tmp_path):
    rt = _runtime(tmp_path)
    report = Pilot3ReportBuilder(base_dir=str(tmp_path)).build(runtime=rt)
    limits = " ".join(report.sections["limitations"]).lower()
    assert "no real-world actuation" in limits
    assert "consciousness" in limits


def test_build_and_write_emits_files(tmp_path):
    rt = _runtime(tmp_path)
    builder = Pilot3ReportBuilder(base_dir=str(tmp_path))
    report = builder.build_and_write(runtime=rt)
    assert os.path.exists(os.path.join(str(tmp_path), "PILOT3_REPORT.md"))
    assert os.path.exists(os.path.join(str(tmp_path), "PILOT3_REPORT.json"))
    assert "report_paths" in report.sections
