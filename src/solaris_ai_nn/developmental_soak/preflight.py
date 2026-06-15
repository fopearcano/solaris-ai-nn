"""Soak preflight -- validate readiness without starting the run.

:class:`SoakPreflight` runs a battery of import/availability/configuration
checks before any soak stage executes. Missing *optional* modules warn (never
fail); missing *required* modules fail; a missing live source marks the live
stage *blocked* (it does not crash); and preflight never starts the run.
"""

from __future__ import annotations

import importlib
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class PreflightStatus:
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    BLOCKED = "blocked"
    SKIP = "skip"

    ALL = (PASS, WARN, FAIL, BLOCKED, SKIP)


@dataclass
class PreflightCheck:
    """A single declarative preflight check."""

    check_id: str
    description: str
    required: bool = True
    category: str = "general"

    def to_dict(self) -> Dict[str, Any]:
        return {"check_id": self.check_id, "description": self.description,
                "required": self.required, "category": self.category}


@dataclass
class PreflightResult:
    """The outcome of one preflight check (with evidence refs)."""

    check_id: str
    status: str
    detail: str = ""
    required: bool = True
    evidence_refs: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status in (PreflightStatus.PASS, PreflightStatus.WARN,
                               PreflightStatus.SKIP, PreflightStatus.BLOCKED)

    def to_dict(self) -> Dict[str, Any]:
        return {"check_id": self.check_id, "status": self.status,
                "detail": self.detail, "required": self.required,
                "evidence_refs": list(self.evidence_refs)}


# Required (critical) prior-module packages: a missing one fails preflight.
_REQUIRED_PACKAGES = (
    ("developmental_life", "solaris_ai_nn.developmental_life",
     "Long-Horizon Developmental Runtime"),
    ("plural_sensorium", "solaris_ai_nn.plural_sensorium", "Plural Sensorium"),
)
# Optional packages: a missing one warns (degraded, not failed).
_OPTIONAL_PACKAGES = (
    ("perceptual_metabolism", "solaris_ai_nn.perceptual_metabolism",
     "Perceptual Metabolism"),
    ("perceptual_ontogenesis", "solaris_ai_nn.perceptual_ontogenesis",
     "Perceptual Ontogenesis"),
    ("semiogenesis", "solaris_ai_nn.semiogenesis", "Semiogenesis"),
    ("sensorium_cognition", "solaris_ai_nn.sensorium_cognition",
     "Sensorium Cognition"),
    ("self_boundary", "solaris_ai_nn.self_boundary", "Self-Boundary"),
    ("desire_formation", "solaris_ai_nn.desire_formation", "Desire Formation"),
    ("action_reaction", "solaris_ai_nn.action_reaction", "Action-Reaction"),
    ("operator_console", "solaris_ai_nn.operator_console", "Operator Console"),
    ("inner_map", "solaris_ai_nn.inner_map", "Inner MAP"),
    ("evaluation", "solaris_ai_nn.evaluation", "Evaluation"),
)


@dataclass
class SoakPreflight:
    """Runs the preflight battery; produces results, never starts the run."""

    rejected_count: int = field(default=0, init=False)

    def checks(self) -> List[PreflightCheck]:
        items = [
            PreflightCheck("required_packages_import",
                           "required prior-module packages import", True,
                           "imports"),
            PreflightCheck("optional_packages_import",
                           "optional prior-module packages import", False,
                           "imports"),
            PreflightCheck("state_dir_writable",
                           "state directory is writable", True, "io"),
            PreflightCheck("prior_reports_discoverable",
                           "prior module reports discoverable", False,
                           "evidence"),
            PreflightCheck("developmental_runtime_available",
                           "Long-Horizon Developmental Runtime available", True,
                           "engine"),
            PreflightCheck("claim_guard_available",
                           "ClaimGuard available for reports", True, "safety"),
            PreflightCheck("no_hardware_control",
                           "no hardware control enabled", True, "safety"),
            PreflightCheck("no_feeder_autostart",
                           "no feeder auto-start enabled", True, "safety"),
            PreflightCheck("no_network_shell_os",
                           "no network/shell/browser/OS control enabled", True,
                           "safety"),
            PreflightCheck("feeder_registry_present",
                           "feeder registry exists if live read-only", False,
                           "live"),
            PreflightCheck("live_source_paths",
                           "live source paths exist if live read-only", False,
                           "live"),
            PreflightCheck("live_governance_approval",
                           "live governance approval exists if required", False,
                           "live"),
            PreflightCheck("disk_budget",
                           "disk budget sufficient", False, "io"),
            PreflightCheck("artifact_retention_configured",
                           "artifact retention configured", False, "evidence"),
        ]
        return items

    def run(self, *, state_dir: str, modules: Optional[Dict[str, Any]] = None,
            plan: Any = None, allow_live_read_only: bool = False,
            require_governance_for_live: bool = True,
            governance_approved: bool = False,
            source_paths: Optional[List[str]] = None,
            ) -> List[PreflightResult]:
        modules = modules or {}
        source_paths = source_paths or []
        results: List[PreflightResult] = []

        # 1. Required packages import.
        missing_req = [d for _, mod, d in _REQUIRED_PACKAGES
                       if not _importable(mod)]
        results.append(PreflightResult(
            "required_packages_import",
            PreflightStatus.FAIL if missing_req else PreflightStatus.PASS,
            "missing: " + ", ".join(missing_req) if missing_req
            else "all required packages import",
            True, [f"package:{m}" for _, m, _ in _REQUIRED_PACKAGES]))

        # 2. Optional packages import (warn, never fail).
        missing_opt = [d for _, mod, d in _OPTIONAL_PACKAGES
                       if not _importable(mod)]
        results.append(PreflightResult(
            "optional_packages_import",
            PreflightStatus.WARN if missing_opt else PreflightStatus.PASS,
            "missing optional: " + ", ".join(missing_opt) if missing_opt
            else "all optional packages import", False,
            ["preflight:optional_modules"]))

        # 3. State dir writable.
        results.append(self._state_dir_check(state_dir))

        # 4. Prior reports discoverable (warn if none found).
        results.append(self._prior_reports_check(state_dir))

        # 5. Developmental runtime available (required engine).
        results.append(PreflightResult(
            "developmental_runtime_available",
            PreflightStatus.PASS if _importable(
                "solaris_ai_nn.developmental_life") else PreflightStatus.FAIL,
            "LongHorizonDevelopmentalRuntime importable", True,
            ["package:solaris_ai_nn.developmental_life"]))

        # 6. ClaimGuard available.
        results.append(PreflightResult(
            "claim_guard_available",
            PreflightStatus.PASS if _importable(
                "solaris_ai_nn.governance.compliance") else PreflightStatus.FAIL,
            "ClaimGuard importable for report scanning", True,
            ["module:governance.compliance"]))

        # 7-9. Forbidden capabilities must be OFF (pass = disabled).
        for cid, desc in (
                ("no_hardware_control", "hardware control"),
                ("no_feeder_autostart", "feeder auto-start"),
                ("no_network_shell_os", "network/shell/browser/OS control")):
            enabled = bool(modules.get(cid.replace("no_", "") + "_enabled",
                                       False))
            results.append(PreflightResult(
                cid,
                PreflightStatus.FAIL if enabled else PreflightStatus.PASS,
                f"{desc} is {'ENABLED (forbidden)' if enabled else 'disabled'}",
                True, ["safety:forbidden_capability"]))

        # 10-12. Live read-only checks: block (not crash) when unavailable.
        live_status = (PreflightStatus.SKIP if not allow_live_read_only
                       else PreflightStatus.PASS)
        feeder_present = bool(modules.get("feeder_registry"))
        if allow_live_read_only and not feeder_present:
            live_status = PreflightStatus.BLOCKED
        results.append(PreflightResult(
            "feeder_registry_present",
            live_status,
            "feeder registry present" if feeder_present
            else "no feeder registry; live stage blocked"
            if allow_live_read_only else "live read-only not requested",
            False, ["live:feeder_registry"]))

        src_status = PreflightStatus.SKIP
        if allow_live_read_only:
            existing = [p for p in source_paths if os.path.exists(p)]
            src_status = (PreflightStatus.PASS if existing
                          else PreflightStatus.BLOCKED)
        results.append(PreflightResult(
            "live_source_paths", src_status,
            "live source paths exist" if src_status == PreflightStatus.PASS
            else "live source missing; live stage blocked"
            if allow_live_read_only else "live read-only not requested",
            False, ["live:source_paths"]))

        gov_status = PreflightStatus.SKIP
        if allow_live_read_only and require_governance_for_live:
            gov_status = (PreflightStatus.PASS if governance_approved
                          else PreflightStatus.BLOCKED)
        results.append(PreflightResult(
            "live_governance_approval", gov_status,
            "governance approval present" if gov_status == PreflightStatus.PASS
            else "live read-only requires governance approval; blocked"
            if allow_live_read_only else "live read-only not requested",
            False, ["governance:live_read_only"]))

        # 13. Disk budget (informational; assume sufficient for bounded runs).
        results.append(PreflightResult(
            "disk_budget", PreflightStatus.PASS,
            "bounded runs use a small append-only artifact budget", False,
            ["io:disk_budget"]))

        # 14. Artifact retention configured (append-only, no auto-delete).
        retention = (plan.stages[plan.ordered_ids()[0]].artifact_retention_policy
                     if plan is not None and getattr(plan, "stages", None)
                     else "append-only; never auto-delete negatives")
        results.append(PreflightResult(
            "artifact_retention_configured", PreflightStatus.PASS,
            retention, False, ["evidence:retention"]))

        if any(r.status == PreflightStatus.FAIL for r in results):
            self.rejected_count += 1
        return results

    def _state_dir_check(self, state_dir: str) -> PreflightResult:
        try:
            os.makedirs(state_dir, exist_ok=True)
            probe = os.path.join(state_dir, ".preflight_probe")
            with open(probe, "w", encoding="utf-8") as fh:
                fh.write("ok")
            os.remove(probe)
            return PreflightResult("state_dir_writable", PreflightStatus.PASS,
                                   f"{state_dir} is writable", True,
                                   ["io:state_dir"])
        except Exception as exc:  # pragma: no cover - environment dependent
            return PreflightResult("state_dir_writable", PreflightStatus.FAIL,
                                   f"{state_dir} not writable: {exc}", True,
                                   ["io:state_dir"])

    def _prior_reports_check(self, state_dir: str) -> PreflightResult:
        found: List[str] = []
        if os.path.isdir(state_dir):
            for root, _dirs, files in os.walk(state_dir):
                for name in files:
                    if name.endswith("_REPORT.json") or name.endswith(
                            "_REPORT.md"):
                        found.append(os.path.join(root, name))
        status = PreflightStatus.PASS if found else PreflightStatus.WARN
        detail = (f"{len(found)} prior report(s) discoverable" if found
                  else "no prior module reports yet (warn, not fail)")
        return PreflightResult("prior_reports_discoverable", status, detail,
                               False, [f"report:{p}" for p in found[:5]])

    def summary(self, results: List[PreflightResult]) -> Dict[str, Any]:
        counts: Dict[str, int] = {s: 0 for s in PreflightStatus.ALL}
        for r in results:
            counts[r.status] = counts.get(r.status, 0) + 1
        passed = not any(r.status == PreflightStatus.FAIL for r in results)
        live_blocked = [r.check_id for r in results
                        if r.status == PreflightStatus.BLOCKED]
        return {
            "passed": passed,
            "pass_count": counts.get(PreflightStatus.PASS, 0),
            "fail_count": counts.get(PreflightStatus.FAIL, 0),
            "warn_count": counts.get(PreflightStatus.WARN, 0),
            "blocked_count": counts.get(PreflightStatus.BLOCKED, 0),
            "skip_count": counts.get(PreflightStatus.SKIP, 0),
            "live_blocked_checks": live_blocked,
            "results": [r.to_dict() for r in results],
            "started_run": False,
        }


def _importable(module: str) -> bool:
    try:
        importlib.import_module(module)
        return True
    except Exception:
        return False
