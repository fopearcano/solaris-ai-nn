"""Post-pilot trace audit: support, sim/real, safety preservation."""

from __future__ import annotations

from solaris_ai_nn.post_pilot import DevelopmentalTraceAuditor


class _Arts:
    def __init__(self, present, data=None):
        self.index = type("I", (), {"present": present})()
        self.data = data or {}


def test_high_traceability_when_artifacts_present():
    arts = _Arts(["observability", "pilot_report", "metrics_daily",
                  "developmental_state", "incidents",
                  "developmental_epochs"],
                 {"pilot_report": {"sections": {"run": {"mode": "sim"}},
                                   "claim_guard_safe": True}})
    result = DevelopmentalTraceAuditor().audit(arts)
    assert result.traceability_score >= 0.5
    assert result.checks["safety_incidents_preserved"]


def test_missing_safety_incidents_flagged():
    arts = _Arts(["observability", "pilot_report"],
                 {"pilot_report": {"sections": {"run": {"mode": "sim"}}}})
    result = DevelopmentalTraceAuditor().audit(arts)
    assert result.checks["safety_incidents_preserved"] is False


def test_counterfactual_real_confusion_detected():
    arts = _Arts(["observability"], {"observability": [
        {"kind": "metrics", "payload": {"offline": True, "observed": True}}]})
    result = DevelopmentalTraceAuditor().audit(arts)
    assert any("offline" in c for c in result.contradictions)


def test_claim_guard_violation_warned():
    arts = _Arts(["pilot_report"],
                 {"pilot_report": {"claim_guard_safe": False,
                                   "sections": {"run": {"mode": "sim"}}}})
    result = DevelopmentalTraceAuditor().audit(arts)
    assert result.claim_guard_respected is False
    assert any("ClaimGuard" in w for w in result.warnings)


def test_audit_does_not_mutate(tmp_path):
    arts = _Arts(["observability"], {"observability": []})
    before = dict(arts.data)
    DevelopmentalTraceAuditor().audit(arts)
    assert arts.data == before
