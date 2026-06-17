"""Shared helpers for first tester protocol tests (not a test module)."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.first_tester_protocol import FirstTesterProtocolRuntime


def seed_rc(base: str, readiness: str = "ready_with_warnings") -> None:
    """Write a minimal RC + packaging + safety-freeze status for the protocol."""
    man = os.path.join(base, "release_candidate", "manifests")
    os.makedirs(man, exist_ok=True)
    with open(os.path.join(man, "TESTER_RC_MANIFEST.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"readiness": readiness,
                   "blocker_count": 0 if "ready" in readiness else 3}, fh)
    pkg = os.path.join(base, "packaging", "reports")
    os.makedirs(pkg, exist_ok=True)
    with open(os.path.join(pkg, "PACKAGING_REPORT.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"sections": {"packaging_status": {
            "readiness": "ready_with_warnings", "doctor_status": "pass"}}}, fh)
    sf = os.path.join(base, "safety_freeze", "manifests")
    os.makedirs(sf, exist_ok=True)
    with open(os.path.join(sf, "TESTER_SAFETY_FREEZE_MANIFEST.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"readiness": "ready_with_warnings",
                   "release_blocker_count": 0}, fh)


def seed_packaging_blocked(base: str) -> None:
    pkg = os.path.join(base, "packaging", "reports")
    os.makedirs(pkg, exist_ok=True)
    with open(os.path.join(pkg, "PACKAGING_REPORT.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"sections": {"packaging_status": {
            "readiness": "blocked", "doctor_status": "blocked"}}}, fh)


def seed_safety_blocked(base: str) -> None:
    sf = os.path.join(base, "safety_freeze", "manifests")
    os.makedirs(sf, exist_ok=True)
    with open(os.path.join(sf, "TESTER_SAFETY_FREEZE_MANIFEST.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"readiness": "critical_blocked",
                   "release_blocker_count": 2}, fh)


def run_protocol(base: str, **kwargs) -> FirstTesterProtocolRuntime:
    rt = FirstTesterProtocolRuntime(tester_state_dir=base, max_runtime_s=60.0,
                                    **kwargs)
    rt.run()
    return rt
