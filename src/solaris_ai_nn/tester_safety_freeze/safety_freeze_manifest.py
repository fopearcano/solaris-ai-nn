"""Tester safety-freeze manifest -- the aggregate readiness record for the gate.

:class:`SafetyFreezeManifestBuilder` aggregates the claim freeze, capability freeze,
artifact scan, red-team checklist, and release blocker gate into a single manifest with
a readiness recommendation. The manifest is local and report-only.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


class SafetyFreezeStatus:
    READY = "ready_for_release_candidate"
    READY_WITH_WARNINGS = "ready_with_warnings"
    BLOCKED = "blocked"
    CRITICAL_BLOCKED = "critical_blocked"
    UNKNOWN = "unknown"

    ALL = (READY, READY_WITH_WARNINGS, BLOCKED, CRITICAL_BLOCKED, UNKNOWN)


@dataclass
class TesterSafetyFreezeManifest:
    """The aggregate safety-freeze manifest."""

    profile_id: str = "tester_safety_freeze_v0"
    generated_utc: str = ""
    scanned_roots: List[str] = field(default_factory=list)
    forbidden_claim_count: int = 0
    warning_count: int = 0
    blocker_count: int = 0
    release_blocker_count: int = 0
    open_release_blockers: List[str] = field(default_factory=list)
    waived_blockers: List[str] = field(default_factory=list)
    critical_open_count: int = 0
    red_team_passed: bool = True
    red_team_blocker_count: int = 0
    capability_passed: bool = True
    capability_blocker_count: int = 0
    claim_passed: bool = True
    artifact_scan_passed: bool = True
    required_disclaimers_present: bool = True
    readiness: str = SafetyFreezeStatus.UNKNOWN

    def compute_readiness(self) -> str:
        if self.critical_open_count > 0:
            self.readiness = SafetyFreezeStatus.CRITICAL_BLOCKED
        elif self.open_release_blockers or self.release_blocker_count > 0:
            self.readiness = SafetyFreezeStatus.BLOCKED
        elif self.warning_count or not self.required_disclaimers_present:
            self.readiness = SafetyFreezeStatus.READY_WITH_WARNINGS
        else:
            self.readiness = SafetyFreezeStatus.READY
        return self.readiness

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest_version": "tester_safety_freeze_v0",
            "profile_id": self.profile_id,
            "generated_utc": self.generated_utc,
            "scanned_roots": list(self.scanned_roots),
            "forbidden_claim_count": self.forbidden_claim_count,
            "warning_count": self.warning_count,
            "blocker_count": self.blocker_count,
            "release_blocker_count": self.release_blocker_count,
            "open_release_blockers": list(self.open_release_blockers),
            "waived_blockers": list(self.waived_blockers),
            "critical_open_count": self.critical_open_count,
            "red_team_status": "pass" if self.red_team_passed else "fail",
            "red_team_blocker_count": self.red_team_blocker_count,
            "capability_freeze_status": "pass" if self.capability_passed
            else "blocked",
            "capability_blocker_count": self.capability_blocker_count,
            "claim_freeze_status": "pass" if self.claim_passed else "blocked",
            "artifact_scan_status": "pass" if self.artifact_scan_passed
            else "blocked",
            "required_disclaimers_present": self.required_disclaimers_present,
            "readiness": self.readiness,
            "report_gate_only": True,
            "note": "local report/gate-only safety-freeze manifest; it does not "
                    "prove the system safe in general -- it is a tester-release "
                    "gate only",
        }

    def to_markdown(self) -> str:
        d = self.to_dict()
        lines = ["# Tester Safety Freeze Manifest", "",
                 f"- readiness: **{d['readiness']}**",
                 f"- forbidden claims: {d['forbidden_claim_count']}",
                 f"- release blockers: {d['release_blocker_count']} "
                 f"(critical open {d['critical_open_count']})",
                 f"- capability freeze: {d['capability_freeze_status']} "
                 f"(blockers {d['capability_blocker_count']})",
                 f"- claim freeze: {d['claim_freeze_status']}",
                 f"- artifact scan: {d['artifact_scan_status']}",
                 f"- red-team: {d['red_team_status']} "
                 f"(blockers {d['red_team_blocker_count']})",
                 f"- required disclaimers present: "
                 f"{d['required_disclaimers_present']}",
                 f"- waived: {', '.join(d['waived_blockers']) or 'none'}", "",
                 "_The safety freeze does NOT prove the system safe in general; "
                 "it is a tester-release gate only._"]
        return "\n".join(lines)


@dataclass
class SafetyFreezeManifestBuilder:
    """Builds the safety-freeze manifest from a finished runtime."""

    def build(self, runtime: Any) -> TesterSafetyFreezeManifest:
        m = TesterSafetyFreezeManifest(
            profile_id=runtime.safety_freeze_profile.profile_id,
            generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            scanned_roots=list(runtime.scanned_roots))
        claim = runtime.claim_result
        cap = runtime.capability_result
        artifact = runtime.artifact_result
        red = runtime.red_team_result
        gate = runtime.blocker_gate

        if claim:
            m.forbidden_claim_count = claim.forbidden_claim_count
            m.warning_count += claim.warning_count
            m.claim_passed = claim.passed
            m.required_disclaimers_present = not claim.missing_disclaimers
        if cap:
            m.capability_passed = cap.passed
            m.capability_blocker_count = cap.blocker_count
        if artifact:
            m.artifact_scan_passed = artifact.passed
            m.warning_count += len(artifact.warnings)
        if red:
            m.red_team_passed = red.passed
            m.red_team_blocker_count = len(red.blockers)
        if gate:
            m.release_blocker_count = len(gate.open_blockers)
            m.open_release_blockers = [b.blocker_id for b in gate.open_blockers]
            m.waived_blockers = [b.blocker_id for b in gate.waived]
            m.critical_open_count = len(gate.critical_open)
            m.blocker_count = len(gate.blockers)
        m.compute_readiness()
        return m

    def write(self, manifest: TesterSafetyFreezeManifest,
              manifests_dir: str) -> Dict[str, str]:
        os.makedirs(manifests_dir, exist_ok=True)
        json_path = os.path.join(manifests_dir,
                                 "TESTER_SAFETY_FREEZE_MANIFEST.json")
        md_path = os.path.join(manifests_dir,
                               "TESTER_SAFETY_FREEZE_MANIFEST.md")
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(manifest.to_dict(), fh, indent=2, default=str)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(manifest.to_markdown())
        return {"json": json_path, "markdown": md_path}
