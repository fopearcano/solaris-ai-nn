"""Pilot-1 failure modes: detection and recommended actions."""

from __future__ import annotations

import time

from solaris_ai_nn.pilot1 import (
    FailureModeDetector,
    FailureModeType,
    FailureSeverity,
    RecommendedAction,
)


def test_heartbeat_stopped_detected():
    det = FailureModeDetector()
    modes = det.detect({}, now=time.time(),
                       last_heartbeat=time.time() - 100000)
    types = {m.type for m in modes}
    assert FailureModeType.HEARTBEAT_STOPPED in types


def test_disk_budget_exceeded_detected():
    det = FailureModeDetector()
    modes = det.detect({"disk_over_budget": True})
    assert any(m.type == FailureModeType.DISK_BUDGET_EXCEEDED for m in modes)


def test_safety_incidents_recommend_shutdown():
    det = FailureModeDetector()
    modes = det.detect({"safety_incident_count": 5})
    assert det.overall_recommendation(modes) == RecommendedAction.SAFE_SHUTDOWN


def test_governance_violation_recommends_emergency_stop():
    det = FailureModeDetector()
    modes = det.detect({"governance_block_count": 1,
                        "governance_violation_attempt": True})
    assert det.overall_recommendation(modes) == RecommendedAction.EMERGENCY_STOP


def test_clean_observation_recommends_continue():
    det = FailureModeDetector()
    modes = det.detect({"safety_incident_count": 0})
    assert det.overall_recommendation(modes) == RecommendedAction.CONTINUE


def test_critical_severity_listed():
    det = FailureModeDetector()
    det.detect({"identity_continuity_lost": True})
    snap = det.snapshot()
    assert FailureModeType.IDENTITY_CONTINUITY_LOST in snap["critical"]
    assert FailureSeverity.CRITICAL in FailureSeverity.ALL
