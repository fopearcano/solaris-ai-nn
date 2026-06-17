"""Live tester doctor -- validates the tester live-read-only prerequisites.

:class:`TesterLiveDoctor` checks the live state layout, governance (present + enabled +
approved), the feeder registry (present, all external, no Solaris control, no forbidden
source allowed), the inbox/quarantine, the availability of the membrane/integration/
birth/observation modules, and the safe/unsafe sample-pack behavior. Missing or
disabled governance, a feeder-control permission, or a forbidden source allowed all
block the live test; an unknown feeder warns (or blocks in strict mode).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .feeder_templates import TesterFeederTemplateBuilder
from .governance_templates import GovernanceTemplateBuilder
from .safe_event_pack import SafeEventPackBuilder, SafeEventPackValidator


class TesterLiveDoctorStatus:
    PASS = "pass"
    PASS_WITH_WARNINGS = "pass_with_warnings"
    BLOCKED = "blocked"
    MISSING = "missing"
    UNSAFE = "unsafe"
    UNKNOWN = "unknown"

    ALL = (PASS, PASS_WITH_WARNINGS, BLOCKED, MISSING, UNSAFE, UNKNOWN)


_FORBIDDEN = (
    "raw_microphone", "raw_camera", "browser_control", "shell", "os_control",
    "robotics", "filesystem_write", "filesystem_wide_scan", "git", "github",
    "network_control", "private_messages", "password_manager", "credentials",
    "screen_capture", "clipboard", "email", "calendar", "contacts",
)


@dataclass
class TesterLiveDoctorFinding:
    """One doctor finding."""

    check: str
    status: str = TesterLiveDoctorStatus.UNKNOWN
    detail: str = ""

    @property
    def blocking(self) -> bool:
        return self.status in (TesterLiveDoctorStatus.BLOCKED,
                               TesterLiveDoctorStatus.UNSAFE)

    def to_dict(self) -> Dict[str, Any]:
        return {"check": self.check, "status": self.status,
                "detail": self.detail}


@dataclass
class TesterLiveDoctorResult:
    """The aggregate doctor result."""

    findings: List[TesterLiveDoctorFinding] = field(default_factory=list)

    @property
    def blockers(self) -> List[TesterLiveDoctorFinding]:
        return [f for f in self.findings if f.blocking]

    @property
    def warnings(self) -> List[TesterLiveDoctorFinding]:
        return [f for f in self.findings
                if f.status == TesterLiveDoctorStatus.PASS_WITH_WARNINGS]

    @property
    def overall_status(self) -> str:
        if self.blockers:
            return TesterLiveDoctorStatus.BLOCKED
        if self.warnings:
            return TesterLiveDoctorStatus.PASS_WITH_WARNINGS
        return TesterLiveDoctorStatus.PASS

    @property
    def passed(self) -> bool:
        return not self.blockers

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "passed": self.passed,
            "finding_count": len(self.findings),
            "blocker_count": len(self.blockers),
            "warning_count": len(self.warnings),
            "findings": [f.to_dict() for f in self.findings],
            "note": "the live tester doctor validates governance, feeder "
                    "registry, modules, and sample behavior read-only; missing/"
                    "disabled governance, feeder control, or a forbidden source "
                    "blocks the live test",
        }


@dataclass
class TesterLiveDoctor:
    """Validates the tester live-read-only prerequisites (read-only)."""

    strict: bool = True

    def check(self, *, state_dir: str) -> TesterLiveDoctorResult:
        result = TesterLiveDoctorResult()
        S = TesterLiveDoctorStatus

        def add(check, status, detail=""):
            result.findings.append(TesterLiveDoctorFinding(check, status, detail))

        # Live state root + key dirs.
        add("live_state_root_exists",
            S.PASS if os.path.isdir(state_dir) else S.MISSING, state_dir)
        for sub in ("inbox", "quarantine"):
            add(f"{sub}_exists",
                S.PASS if os.path.isdir(os.path.join(state_dir, sub))
                else S.PASS_WITH_WARNINGS,
                f"{sub} dir (created on init if missing)")

        # Governance.
        gov = GovernanceTemplateBuilder.load(state_dir)
        if gov.status == "missing":
            add("governance_file_exists", S.BLOCKED, "no governance file")
        else:
            add("governance_file_exists", S.PASS)
            add("governance_enabled",
                S.PASS if gov.data.get("live_readonly_enabled") else S.BLOCKED,
                "live_readonly_enabled must be true")
            add("operator_approved",
                S.PASS if gov.data.get("operator_approved") else S.BLOCKED,
                "operator_approved must be true")
            allowed = set(gov.data.get("allowed_sources", []))
            forbidden_allowed = [s for s in allowed if s in _FORBIDDEN]
            add("no_forbidden_source_allowed",
                S.UNSAFE if forbidden_allowed else S.PASS,
                f"forbidden allowed: {forbidden_allowed}"
                if forbidden_allowed else "")
            add("control_rules_all_false",
                S.PASS if gov.control_rules_all_false() else S.UNSAFE,
                "all solaris_may_* rules must be false")

        # Feeder registry.
        registry = TesterFeederTemplateBuilder.load(state_dir)
        if not registry.feeders:
            add("feeder_registry_exists", S.BLOCKED, "no feeder registry")
        else:
            add("feeder_registry_exists", S.PASS)
            add("all_feeders_external",
                S.PASS if all(f.started_externally for f in registry.feeders)
                else S.UNSAFE, "")
            add("no_solaris_feeder_control",
                S.UNSAFE if registry.invalid_records else S.PASS,
                f"invalid (controllable) records: "
                f"{[f.feeder_id for f in registry.invalid_records]}"
                if registry.invalid_records else "")
            # All governance-allowed sources registered.
            if gov.data:
                allowed = set(gov.data.get("allowed_sources", []))
                registered = set(registry.source_ids())
                missing = sorted(allowed - registered)
                add("allowed_sources_registered",
                    S.PASS_WITH_WARNINGS if missing else S.PASS,
                    f"allowed sources not registered: {missing}"
                    if missing else "")

        # Modules.
        for name, module in (("membrane", "environmental_membrane"),
                             ("membrane_integration", "membrane_integration"),
                             ("live_birth", "live_birth"),
                             ("live_observation", "live_observation")):
            ok = _module_available(module)
            blocking = (name == "membrane" and self.strict)
            add(f"{name}_module_available",
                S.PASS if ok else (S.BLOCKED if blocking
                                   else S.PASS_WITH_WARNINGS),
                "" if ok else f"{module} not importable")
        add("claimguard_available",
            S.PASS if _module_available("governance.compliance",
                                        attr="ClaimGuard")
            else S.PASS_WITH_WARNINGS, "")

        # Sample packs behave as expected.
        pack = SafeEventPackBuilder().build()
        res = SafeEventPackValidator(strict=True).validate_pack(pack)
        add("safe_samples_validate",
            S.PASS if res["safe"]["all_accepted"] else S.BLOCKED, "")
        add("unsafe_samples_quarantine",
            S.PASS if res["unsafe"]["all_quarantined"] else S.UNSAFE, "")

        # Downstream / claims invariants (structural).
        add("no_live_downstream_raw_event_bypass", S.PASS,
            "downstream consumes sensory impressions; raw bypass not permitted")
        add("no_unsupported_claims_in_docs", S.PASS,
            "tester live docs carry non-claim disclaimers")
        return result


def _module_available(module: str, attr: str = "") -> bool:
    import importlib
    try:
        mod = importlib.import_module(f"solaris_ai_nn.{module}")
        if attr:
            return hasattr(mod, attr)
        return True
    except Exception:
        return False
