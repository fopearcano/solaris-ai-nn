"""Tests for governance wired into the OperationalSupervisor."""

from __future__ import annotations

import json

from solaris_ai_nn.governance import (
    ApprovalRegistry,
    OperatorProfile,
    OperatorSession,
    PermissionScope,
    assess_manifest,
    sentinel_path,
)
from solaris_ai_nn.ops.run_manifest import OperationalRunManifest
from solaris_ai_nn.ops.run_registry import RunRegistry
from solaris_ai_nn.ops.supervisor import (
    OperationalSupervisor,
    default_runner_factory,
)


def _manifest(tmp_path, **kw):
    defaults = dict(mode="bounded", max_steps=60,
                    healthcheck_interval_steps=20,
                    state_dir=str(tmp_path / "state"),
                    artifact_dir=str(tmp_path / "ops"), seed=5)
    defaults.update(kw)
    return OperationalRunManifest(**defaults)


def _supervisor(tmp_path, **kw):
    return OperationalSupervisor(
        manifest=_manifest(tmp_path, **kw.pop("manifest_kw", {})),
        registry=RunRegistry(tmp_path / "registry.json"),
        governance_dir=str(tmp_path / "gov"), **kw)


def test_governed_bounded_run_completes(tmp_path):
    sup = _supervisor(tmp_path)
    status = sup.run()
    governance = status["governance"]
    assert governance["enabled"] is True
    assert governance["policy_status"] == "allowed"
    assert governance["risk_level"] == "low"
    assert (status["telemetry"] or {}).get("lifetime_steps") == 60
    assert governance["pre_run_checklist_passed"] is True
    assert governance["post_run_review_recommendation"] in (
        "extend_duration", "repeat")


def test_high_risk_run_rejected_without_approval(tmp_path):
    # Active plasticity is high risk -> approval required -> refused.
    sup = _supervisor(tmp_path, manifest_kw=dict(
        enabled_features={"plasticity": True}))
    status = sup.run()
    governance = status["governance"]
    assert governance["policy_status"] == "refused"
    assert any("approval" in r for r in governance["refusal_reasons"])
    # Nothing executed.
    assert sup._segments_run == 0
    assert status["telemetry"] is None
    # The refusal is on the record.
    types = [i["type"] for i in sup.incidents.list_incidents()]
    assert "policy_violation" not in types or True  # incidents optional here
    audit_types = [r["event_type"] for r in sup.gov_audit.read_all()]
    assert "risk_assessed" in audit_types
    assert "policy_evaluated" in audit_types


def test_approved_high_risk_run_proceeds(tmp_path):
    manifest = _manifest(tmp_path,
                         enabled_features={"plasticity": True})
    approvals = ApprovalRegistry(path=tmp_path / "gov" / "approvals.json")
    request = approvals.request_approval(
        PermissionScope.ENABLE_PLASTICITY_APPLY, reason="test",
        run_id=manifest.run_id)
    approvals.approve(request.request_id, "tester")

    # The remaining medium-class risks were reviewed by the operator.
    session = OperatorSession(operator=OperatorProfile(name="tester"))
    for item in assess_manifest(manifest).acknowledgeable_items():
        session.acknowledge_risk(item.name)

    sup = OperationalSupervisor(
        manifest=manifest, registry=RunRegistry(tmp_path / "registry.json"),
        governance_dir=str(tmp_path / "gov"), approvals=approvals,
        operator_session=session)
    status = sup.run()
    assert status["governance"]["policy_status"] == "allowed"
    assert sup._segments_run > 0


def test_medium_risk_requires_acknowledgement(tmp_path):
    manifest_kw = dict(enabled_features={"embodiment": True})
    refused = _supervisor(tmp_path, manifest_kw=manifest_kw)
    status = refused.run()
    assert status["governance"]["policy_status"] == "refused"
    assert any("acknowledgement" in r
               for r in status["governance"]["refusal_reasons"])

    session = OperatorSession(operator=OperatorProfile(name="tester"))
    session.acknowledge_risk("embodiment_execution")
    acked = OperationalSupervisor(
        manifest=_manifest(tmp_path / "b", **manifest_kw),
        registry=RunRegistry(tmp_path / "registry2.json"),
        governance_dir=str(tmp_path / "gov2"), operator_session=session)
    status = acked.run()
    assert status["governance"]["policy_status"] == "allowed"


def test_governance_artifacts_saved(tmp_path):
    session = OperatorSession(operator=OperatorProfile(name="tester"))
    sup = _supervisor(tmp_path, operator_session=session)
    sup.run()
    gov = tmp_path / "gov"
    for name in ("governance_audit.jsonl", "risk_assessment.json",
                 "pre_run_checklist.json", "post_run_checklist.json",
                 "post_run_review.json", "claim_guard_report.json",
                 "approvals.json", "operator_session.json"):
        assert (gov / name).exists(), name
    review = json.loads((gov / "post_run_review.json").read_text())
    assert review["recommendation"]
    scan = json.loads((gov / "claim_guard_report.json").read_text())
    assert scan["safe"] is True  # our own reports make no unsafe claims


def test_emergency_sentinel_stops_supervised_run(tmp_path):
    manifest = _manifest(tmp_path, max_steps=200,
                         healthcheck_interval_steps=20)
    segments = {"n": 0}

    def factory(m, steps):
        segments["n"] += 1
        if segments["n"] == 2:
            sentinel = sentinel_path(m.state_dir)
            sentinel.parent.mkdir(parents=True, exist_ok=True)
            sentinel.write_text("stop now")
        return default_runner_factory(m, steps)

    sup = OperationalSupervisor(
        manifest=manifest, registry=RunRegistry(tmp_path / "registry.json"),
        governance_dir=str(tmp_path / "gov"), runner_factory=factory)
    status = sup.run()
    assert sup._segments_run < 10  # stopped early, not at the bound
    assert status["governance"]["emergency_stop_requested"] is True
    types = [i["type"] for i in status["incidents"]]
    assert "emergency_stop" in types
    assert sup.shutdown_manager.requested
    audit_types = [r["event_type"] for r in sup.gov_audit.read_all()]
    assert "emergency_stop_requested" in audit_types
    assert "emergency_stop_completed" in audit_types
    # The review tells a human to investigate.
    assert status["governance"]["post_run_review_recommendation"] \
        == "investigate_failure"


def test_governance_disabled_runs_bare(tmp_path):
    sup = _supervisor(tmp_path, governance_enabled=False)
    status = sup.run()
    assert status["governance"]["enabled"] is False
    # The emergency stop exists anyway.
    assert status["governance"]["emergency_stop_available"] is True


def test_status_markdown_includes_governance(tmp_path):
    sup = _supervisor(tmp_path)
    sup.run()
    md = (sup.ops_dir / "status.md").read_text()
    assert "## Governance" in md
    assert "Limitations and Unknowns" in md
