"""Tester RC readiness gate -- the hard gate before a tester release candidate.

:class:`TesterRCReadinessGate` evaluates packaging, safety freeze, fixture, membrane,
console, feedback, live-read-only, and docs evidence and produces a readiness result with
explicit blockers and warnings. Critical blockers prevent the RC; open release blockers
prevent the RC unless explicitly waived with a reason; missing optional modules do not
block. The gate is local and report-only; it makes no claims and hides nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class RCReadinessStatus:
    READY = "ready"
    READY_WITH_WARNINGS = "ready_with_warnings"
    BLOCKED = "blocked"
    CRITICAL_BLOCKED = "critical_blocked"
    UNKNOWN = "unknown"

    ALL = (READY, READY_WITH_WARNINGS, BLOCKED, CRITICAL_BLOCKED, UNKNOWN)


@dataclass
class RCReadinessBlocker:
    check: str
    detail: str
    critical: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"check": self.check, "detail": self.detail,
                "critical": self.critical}


@dataclass
class RCReadinessWarning:
    check: str
    detail: str

    def to_dict(self) -> Dict[str, Any]:
        return {"check": self.check, "detail": self.detail}


@dataclass
class RCReadinessResult:
    """The RC readiness verdict with explicit blockers and warnings."""

    status: str = RCReadinessStatus.UNKNOWN
    blockers: List[RCReadinessBlocker] = field(default_factory=list)
    warnings: List[RCReadinessWarning] = field(default_factory=list)
    passed_checks: List[str] = field(default_factory=list)

    @property
    def critical_blockers(self) -> List[RCReadinessBlocker]:
        return [b for b in self.blockers if b.critical]

    @property
    def ready(self) -> bool:
        return self.status in (RCReadinessStatus.READY,
                               RCReadinessStatus.READY_WITH_WARNINGS)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "ready": self.ready,
            "blocker_count": len(self.blockers),
            "critical_blocker_count": len(self.critical_blockers),
            "warning_count": len(self.warnings),
            "passed_check_count": len(self.passed_checks),
            "blockers": [b.to_dict() for b in self.blockers],
            "warnings": [w.to_dict() for w in self.warnings],
            "passed_checks": list(self.passed_checks),
            "local_only": True, "report_only": True,
            "note": "local RC readiness gate; critical blockers prevent the "
                    "release candidate and are never hidden",
        }

    def to_markdown(self) -> str:
        d = self.to_dict()
        lines = ["# Tester RC Readiness Report", "",
                 f"- status: **{d['status']}**",
                 f"- blockers: {d['blocker_count']} "
                 f"(critical {d['critical_blocker_count']})",
                 f"- warnings: {d['warning_count']}",
                 f"- passed checks: {d['passed_check_count']}", "",
                 "## Blockers", ""]
        lines += [f"- {'[critical] ' if b['critical'] else ''}{b['check']}: "
                  f"{b['detail']}" for b in d["blockers"]] or ["- none"]
        lines += ["", "## Warnings", ""]
        lines += [f"- {w['check']}: {w['detail']}"
                  for w in d["warnings"]] or ["- none"]
        lines += ["", "_Local RC readiness gate. Critical blockers prevent the "
                  "tester release candidate and cannot be hidden. This is a "
                  "local assessment, not a public release and not a claim of "
                  "consciousness/life/agency._"]
        return "\n".join(lines)


@dataclass
class TesterRCReadinessGate:
    """Evaluates RC readiness from collected evidence."""

    allow_docs_only_rc: bool = False
    waived_blockers: List[str] = field(default_factory=list)

    def evaluate(self, ctx: Dict[str, Any]) -> RCReadinessResult:
        r = RCReadinessResult()

        def ok(check: str) -> None:
            r.passed_checks.append(check)

        def block(check: str, detail: str, critical: bool = False) -> None:
            if check in self.waived_blockers and not critical:
                r.warnings.append(RCReadinessWarning(
                    check, f"WAIVED: {detail}"))
                return
            r.blockers.append(RCReadinessBlocker(check, detail, critical))

        def warn(check: str, detail: str) -> None:
            r.warnings.append(RCReadinessWarning(check, detail))

        pkg = ctx.get("packaging", {}) or {}
        sf = ctx.get("safety_freeze", {}) or {}
        fixture = ctx.get("fixture", {}) or {}
        live = ctx.get("live", {}) or {}
        console = ctx.get("console", {}) or {}
        feedback = ctx.get("feedback", {}) or {}
        membrane = ctx.get("membrane", {}) or {}
        artifacts = ctx.get("artifacts", {}) or {}
        docs = ctx.get("docs", {}) or {}

        # -- Packaging --------------------------------------------------------
        if not pkg.get("packaging_available"):
            block("packaging_present", "no tester packaging report present")
        else:
            ok("packaging_present")
            doctor = pkg.get("doctor_status", "unknown")
            if doctor in ("ok", "pass", "pass_with_warnings", "healthy",
                          "ready", "ready_with_warnings"):
                ok("packaging_doctor")
            elif doctor == "unknown":
                warn("packaging_doctor", "packaging doctor status unknown")
            else:
                block("packaging_doctor",
                      f"packaging doctor status is {doctor!r}")
            clean = pkg.get("clean_machine_readiness",
                            pkg.get("clean_machine_status", "unknown"))
            if clean in ("pass", "ready", "passed", "ready_with_warnings",
                         "pass_with_warnings"):
                ok("clean_machine_readiness")
            elif clean == "unknown":
                warn("clean_machine_readiness",
                     "clean-machine readiness unknown")
            else:
                block("clean_machine_readiness",
                      f"clean-machine readiness is {clean!r}")
            if pkg.get("readiness") == "blocked":
                block("packaging_readiness",
                      "packaging readiness is blocked")

        # -- Required CLI commands -------------------------------------------
        if ctx.get("required_commands_present", True):
            ok("required_cli_commands")
        else:
            block("required_cli_commands",
                  "one or more required tester CLI commands are missing")

        # -- Fixture demo -----------------------------------------------------
        if not fixture.get("fixture_demo_available", True):
            block("fixture_demo_available",
                  "the fixture tester demo command/pack is not available")
        else:
            ok("fixture_demo_available")
        fixture_passed = fixture.get("fixture_passed")
        if fixture_passed is False:
            if self.allow_docs_only_rc:
                warn("fixture_demo_passed",
                     "fixture demo did not pass; docs-only RC profile allows it")
            else:
                block("fixture_demo_passed",
                      "the fixture tester demo did not pass reproducibility")
        elif fixture_passed is None:
            warn("fixture_demo_passed",
                 "fixture demo not yet run; runbook gives clear instructions")
        else:
            ok("fixture_demo_passed")

        # -- Safety freeze ----------------------------------------------------
        if not sf.get("safety_freeze_available"):
            block("safety_freeze_present", "no tester safety freeze present")
        else:
            ok("safety_freeze_present")
            sf_ready = sf.get("readiness", "unknown")
            if sf_ready == "critical_blocked":
                block("safety_freeze_readiness",
                      "safety freeze is critically blocked", critical=True)
            elif sf_ready in ("blocked",):
                block("safety_freeze_readiness", "safety freeze is blocked")
            elif sf_ready in ("ready_for_release_candidate", "ready",
                              "ready_with_warnings"):
                ok("safety_freeze_readiness")
            else:
                warn("safety_freeze_readiness",
                     f"safety freeze readiness is {sf_ready!r}")
            crit = int(sf.get("critical_open_count", 0) or 0)
            opn = int(sf.get("open_release_blocker_count",
                             sf.get("release_blocker_count", 0)) or 0)
            if crit:
                block("zero_open_critical_release_blockers",
                      f"{crit} open critical release blocker(s)", critical=True)
            else:
                ok("zero_open_critical_release_blockers")
            if opn and not crit:
                block("zero_open_release_blockers",
                      f"{opn} open release blocker(s)")
            elif not opn:
                ok("zero_open_release_blockers")
            fc = int(sf.get("forbidden_claim_count", 0) or 0)
            if fc:
                block("zero_forbidden_claims",
                      f"{fc} forbidden consciousness/life/agency claim(s)",
                      critical=True)
            else:
                ok("zero_forbidden_claims")
            cap = int(sf.get("capability_blocker_count", 0) or 0)
            if cap:
                block("zero_capability_blockers",
                      f"{cap} unsafe capability blocker(s)", critical=True)
            else:
                ok("zero_capability_blockers")

        # -- Feedback ---------------------------------------------------------
        if not feedback.get("feedback_available", True):
            warn("feedback_present", "no tester feedback system initialized")
        else:
            ok("feedback_present")
        if feedback.get("non_training", True):
            ok("feedback_non_training")
        else:
            block("feedback_non_training",
                  "feedback docs imply training/teaching", critical=True)

        # -- Console ----------------------------------------------------------
        if console.get("read_only", True):
            ok("console_read_only")
        else:
            block("console_read_only", "tester console is not read-only",
                  critical=True)

        # -- Live-read-only templates ----------------------------------------
        if live.get("templates_available", True):
            ok("live_readonly_templates")
        else:
            block("live_readonly_templates",
                  "live-read-only templates are missing")
        if live.get("feeder_policy_clear", True):
            ok("external_feeder_policy")
        else:
            block("external_feeder_policy",
                  "external feeder policy is unclear/missing")

        # -- Membrane ---------------------------------------------------------
        if membrane.get("module_available", True):
            ok("membrane_module")
        else:
            block("membrane_module", "membrane module unavailable")
        if membrane.get("integration_available", True):
            ok("membrane_integration")
        else:
            block("membrane_integration", "membrane integration unavailable")
        if membrane.get("critical_bypass"):
            block("no_raw_event_downstream_bypass",
                  "raw-event/membrane downstream bypass detected", critical=True)
        else:
            ok("no_raw_event_downstream_bypass")
        if membrane.get("live_modules_ran") and not membrane.get("present"):
            block("membrane_present_for_live",
                  "live modules ran but no membrane report is present",
                  critical=True)
        else:
            ok("membrane_present_for_live")

        # -- Docs -------------------------------------------------------------
        for key in ("quickstart", "runbook", "known_issues", "release_notes"):
            if docs.get(key, True):
                ok(f"doc_{key}")
            else:
                block(f"doc_{key}", f"required doc {key} is missing")
        if docs.get("disclaimers_present", True):
            ok("required_disclaimers_present")
        else:
            block("required_disclaimers_present",
                  "required disclaimers are missing in required docs",
                  critical=True)

        # -- Required artifacts ----------------------------------------------
        missing_required = artifacts.get("missing_required", []) or []
        if missing_required:
            block("required_artifacts_present",
                  f"missing required artifacts: {', '.join(missing_required)}")
        else:
            ok("required_artifacts_present")
        for key in artifacts.get("missing_recommended", []) or []:
            warn("recommended_artifact", f"recommended artifact missing: {key}")

        r.status = self._status(r)
        return r

    @staticmethod
    def _status(r: RCReadinessResult) -> str:
        if r.critical_blockers:
            return RCReadinessStatus.CRITICAL_BLOCKED
        if r.blockers:
            return RCReadinessStatus.BLOCKED
        if r.warnings:
            return RCReadinessStatus.READY_WITH_WARNINGS
        return RCReadinessStatus.READY
