"""Tests for the pilot readiness check."""

from __future__ import annotations

import json

from solaris_ai_nn.governance import GovernancePolicy
from solaris_ai_nn.pilot.pilot_manifest import PilotManifest
from solaris_ai_nn.pilot.readiness import PilotReadinessCheck
from solaris_ai_nn.pilot.safety import PilotSafetyValidator


def _manifest(tmp_path, profile="simulated", **kw):
    defaults = dict(profile=profile, operator="tester",
                    state_dir=str(tmp_path / "state"),
                    artifact_dir=str(tmp_path / "pilots"),
                    max_steps=50, notes="readiness test")
    defaults.update(kw)
    return PilotManifest(**defaults)


def _check(tmp_path, manifest, **kw):
    kw.setdefault("governance", GovernancePolicy())
    return PilotReadinessCheck(manifest=manifest, **kw)


def _ctx(tmp_path, **kw):
    return {"approved_output_roots": [str(tmp_path)],
            "quick_suite_passed": "skipped",
            "restart_demo_passed": "skipped", **kw}


def test_ready_report_passes_for_safe_profile(tmp_path):
    report = _check(tmp_path, _manifest(tmp_path)).run(_ctx(tmp_path))
    assert report.ready, [i.detail for i in report.blocking_issues()]
    assert report.profile == "simulated"
    # Skips are visible as warnings, not silently green.
    warned = [i.detail for i in report.warnings()]
    assert any("skipped" in w for w in warned)
    assert "ready" in report.recommended_next_step


def test_missing_governance_blocks_readiness(tmp_path):
    check = PilotReadinessCheck(manifest=_manifest(tmp_path),
                                governance=None)
    report = check.run(_ctx(tmp_path))
    assert not report.ready
    assert any(i.area == "governance" for i in report.blocking_issues())


def test_missing_emergency_stop_severity_depends_on_profile(tmp_path):
    # Simulated: warning only.
    simulated = _manifest(tmp_path)
    simulated.emergency_stop_path = ""
    report = _check(tmp_path, simulated).run(_ctx(tmp_path))
    assert any("emergency stop" in i.detail.lower() for i in report.warnings())

    # Read-only stream: blocking. (The safety validator also flags it, so
    # readiness must come out not-ready.)
    src = tmp_path / "in.jsonl"
    src.write_text(json.dumps({"payload": "x"}) + "\n")
    stream = _manifest(tmp_path, profile="read_only_stream",
                       input_sources=[str(src)])
    stream.emergency_stop_path = ""
    report = _check(tmp_path, stream).run(_ctx(tmp_path))
    assert not report.ready
    assert any("emergency stop" in i.detail.lower()
               for i in report.blocking_issues())


def test_unwritable_dirs_block(tmp_path):
    manifest = _manifest(tmp_path,
                         state_dir="/proc/definitely_not_writable/state")
    report = _check(tmp_path, manifest).run(_ctx(tmp_path))
    assert not report.ready
    assert any("state dir" in i.detail for i in report.blocking_issues())


def test_active_plasticity_needs_approval_record(tmp_path):
    manifest = _manifest(tmp_path)
    manifest.enabled_features["plasticity"] = True
    report = _check(tmp_path, manifest).run(_ctx(tmp_path))
    assert not report.ready
    assert any("approval" in i.detail for i in report.blocking_issues())
    # With an approval id on the manifest the approvals check passes.
    approved = _manifest(tmp_path, governance_approval_ids=["appr-1"])
    approved.enabled_features["plasticity"] = True
    report = _check(tmp_path, approved).run(_ctx(tmp_path))
    blocking = [i.detail for i in report.blocking_issues()]
    assert not any("approval record" in d for d in blocking)


def test_report_serializes_and_renders(tmp_path):
    report = _check(tmp_path, _manifest(tmp_path)).run(_ctx(tmp_path))
    data = report.to_dict()
    json.dumps(data)
    for key in ("pilot_id", "profile", "ready", "blocking_issues",
                "warnings", "checks", "recommended_next_step"):
        assert key in data, key
    md = report.to_markdown()
    assert "Pilot readiness" in md
    assert "READY" in md
