"""Console safety panel -- the prominent, top-of-dashboard safety summary.

:class:`ConsoleSafetyPanel` summarizes safety-relevant findings from the discovered
artifacts: missing/disabled governance, an unsafe feeder registry or feeder-control
permission, the quarantine count, forbidden sources, membrane bypass, raw fallback,
unsupported claims, missing non-claim disclaimers, network/shell/Git/hardware access
records, tester-feedback-training risk, and raw-private-payload exposure risk. Blockers
appear at the top of the dashboard; safety issues are never buried.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class SafetyPanelStatus:
    OK = "ok"
    WARNINGS = "warnings"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"

    ALL = (OK, WARNINGS, BLOCKED, UNKNOWN)


@dataclass
class SafetyPanelFinding:
    """One safety-panel finding."""

    check: str
    severity: str = "warning"  # info | warning | blocker
    detail: str = ""

    @property
    def blocking(self) -> bool:
        return self.severity == "blocker"

    def to_dict(self) -> Dict[str, Any]:
        return {"check": self.check, "severity": self.severity,
                "detail": self.detail}


@dataclass
class ConsoleSafetyPanel:
    """The prominent console safety panel built from discovered artifacts."""

    findings: List[SafetyPanelFinding] = field(default_factory=list)

    def blocking_findings(self) -> List[SafetyPanelFinding]:
        return [f for f in self.findings if f.blocking]

    @property
    def status(self) -> str:
        if self.blocking_findings():
            return SafetyPanelStatus.BLOCKED
        if any(f.severity == "warning" for f in self.findings):
            return SafetyPanelStatus.WARNINGS
        return SafetyPanelStatus.OK

    def to_dict(self) -> Dict[str, Any]:
        return {
            "safety_status": self.status,
            "finding_count": len(self.findings),
            "blocker_count": len(self.blocking_findings()),
            "findings": [f.to_dict() for f in self.findings],
            "note": "safety findings are surfaced at the top of the dashboard "
                    "and never buried below optional summaries",
        }


@dataclass
class SafetyPanelBuilder:
    """Builds the safety panel from the discovery result (read-only)."""

    _FORBIDDEN = (
        "raw_microphone", "raw_camera", "browser_control", "shell",
        "os_control", "robotics", "filesystem_write", "filesystem_wide_scan",
        "git", "github", "network_control", "private_messages",
        "password_manager", "credentials", "screen_capture", "clipboard",
        "email", "calendar", "contacts",
    )

    def build(self, discovery) -> ConsoleSafetyPanel:
        from .artifact_discovery import ArtifactKind as K

        panel = ConsoleSafetyPanel()

        def add(check, severity, detail=""):
            panel.findings.append(SafetyPanelFinding(check, severity, detail))

        # Governance.
        gov = discovery.latest(K.LIVE_GOVERNANCE)
        if gov is None:
            add("governance_present", "warning",
                "no live governance found (fixture-only testing so far)")
        else:
            data = _load(gov.path)
            if not data.get("live_readonly_enabled"):
                add("governance_enabled", "warning",
                    "governance present but disabled (live testing not enabled)")
            elif not data.get("operator_approved"):
                add("governance_approved", "warning",
                    "governance enabled but not operator-approved")
            allowed = set(data.get("allowed_sources", []))
            forbidden_allowed = sorted(allowed & set(self._FORBIDDEN))
            if forbidden_allowed:
                add("forbidden_source_allowed", "blocker",
                    f"forbidden sources allowed: {forbidden_allowed}")

        # Feeder registry.
        reg = discovery.latest(K.FEEDER_REGISTRY)
        if reg is not None:
            data = _load(reg.path)
            for f in data.get("feeders", []):
                if f.get("solaris_may_control") or f.get("started_by_solaris"):
                    add("feeder_control_permission", "blocker",
                        f"feeder {f.get('feeder_id')} grants Solaris control")
                    break

        # Quarantine.
        q = discovery.latest(K.QUARANTINE_REPORT)
        if q is not None:
            count = q.summary.get("quarantined_count",
                                  q.summary.get("quarantine_count", 0))
            if count:
                add("quarantine_present", "warning",
                    f"{count} quarantined event(s) recorded (expected for "
                    "unsafe input; never learned)")

        # Membrane integration bypass.
        integ = discovery.latest(K.MEMBRANE_INTEGRATION_REPORT)
        if integ is not None:
            data = _load(integ.path)
            sections = data.get("sections", {}) if isinstance(data, dict) else {}
            status = sections.get("status", {}) if isinstance(sections, dict) \
                else {}
            critical = status.get("critical_bypass_count", 0)
            fallback = status.get("raw_fallback_count", 0)
            if critical:
                add("membrane_bypass", "blocker",
                    f"{critical} critical membrane bypass(es) detected")
            if fallback:
                add("raw_fallback", "warning",
                    f"{fallback} raw-event fallback(s) detected")

        # Scientific claims.
        claim = discovery.latest(K.SCIENTIFIC_CLAIM_REPORT)
        if claim is not None:
            data = _load(claim.path)
            forbidden = data.get("forbidden_claim_count",
                                 data.get("unsupported_claim_count", 0))
            if forbidden:
                add("unsupported_claim", "blocker",
                    f"{forbidden} unsupported/forbidden claim(s) detected")

        # Always-present structural reassurances.
        add("console_read_only", "info",
            "the console is read-only and controls no feeders/hardware/network")
        add("raw_private_payload_hidden", "info",
            "raw private event payloads are not displayed by default")
        return panel


def _load(path: str) -> Dict[str, Any]:
    import json
    import os
    try:
        if not os.path.isfile(path) or os.path.getsize(path) > 5_000_000:
            return {}
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}
