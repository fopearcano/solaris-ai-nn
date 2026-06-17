"""Tester live-read-only runtime -- the bounded, local bridge to live testing.

:class:`TesterLiveReadOnlyRuntime` prepares the tester live environment (state layout,
governance + feeder registry templates, safe/unsafe event packs), runs the live tester
doctor, optionally validates the sample packs, and -- only when explicitly requested and
only over the local inbox -- runs Live Birth -> Environmental Membrane -> Membrane
Integration -> Live Observation. It is bounded and local-only and never starts/stops/
schedules/controls/executes external feeders, controls hardware, accesses the network/
shell/Git/GitHub, publishes/uploads, treats text as a command, trains on tester
feedback, or makes unsupported claims.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .feeder_templates import TesterFeederTemplateBuilder
from .governance_templates import GovernanceTemplateBuilder
from .live_tester_checklist import TesterLiveChecklist
from .live_tester_doctor import TesterLiveDoctor
from .live_tester_profile import get_live_tester_profile
from .safe_event_pack import SafeEventPackBuilder, SafeEventPackValidator
from .safety import TesterLiveReadOnlySafetyValidator


@dataclass
class TesterLiveReadOnlyRuntime:
    """Bounded, local, live-read-only tester runtime (external feeders only)."""

    state_dir: str = ".solaris_ai_nn_live"
    tester_state_dir: str = ".solaris_ai_nn_tester/live"
    profile: Optional[str] = None
    max_runtime_s: float = 120.0
    max_events: int = 500
    strict: bool = False
    dry_run: bool = False
    report_only: bool = False
    write_templates: bool = True
    validate_samples: bool = True
    copy_safe_samples_to_inbox: bool = False
    run_birth: bool = False
    run_membrane: bool = False
    run_integration: bool = False
    run_observation: bool = False
    require_governance: bool = True
    require_membrane: bool = True
    require_claimguard: bool = False

    safety: TesterLiveReadOnlySafetyValidator = field(
        default_factory=TesterLiveReadOnlySafetyValidator, init=False)
    live_profile: Any = field(default=None, init=False)
    run_id: str = field(default="", init=False)
    bundle_dir: str = field(default="", init=False)
    blocked: bool = field(default=False, init=False)
    blockers: List[str] = field(default_factory=list, init=False)
    warnings: List[str] = field(default_factory=list, init=False)

    template_results: Dict[str, Any] = field(default_factory=dict, init=False)
    doctor_result: Any = field(default=None, init=False)
    fixture_status: Dict[str, Any] = field(default_factory=dict, init=False)
    sample_validation: Dict[str, Any] = field(default_factory=dict, init=False)
    governance_status: Dict[str, Any] = field(default_factory=dict, init=False)
    feeder_status: Dict[str, Any] = field(default_factory=dict, init=False)
    birth_status: Dict[str, Any] = field(default_factory=dict, init=False)
    membrane_status: Dict[str, Any] = field(default_factory=dict, init=False)
    integration_status: Dict[str, Any] = field(default_factory=dict, init=False)
    observation_status: Dict[str, Any] = field(default_factory=dict, init=False)
    quarantine_summary: Dict[str, Any] = field(default_factory=dict, init=False)
    reports: Dict[str, Any] = field(default_factory=dict, init=False)
    bundle: Any = field(default=None, init=False)
    _refused: bool = field(default=False, init=False)

    _TESTER_SUBDIRS = ("templates", "sample_events", "checklists", "reports",
                       "bundles", "index")
    _LIVE_SUBDIRS = ("governance", "feeders", "inbox", "quarantine",
                     "processed", "membrane", "observation", "reports",
                     "certificates", "index")

    def __post_init__(self) -> None:
        self.live_profile = get_live_tester_profile(self.profile)
        self.require_membrane = self.require_membrane \
            and self.live_profile.require_membrane
        self.run_id = f"tlive_{int(time.time() * 1000)}"
        self.bundle_dir = os.path.join(self.tester_state_dir, "bundles",
                                       f"LIVE_TESTER_BUNDLE_{self.run_id}")
        # Profile mode gates which stages may run.
        self.run_birth = self.run_birth and self.live_profile.run_birth
        self.run_membrane = self.run_membrane and self.live_profile.run_membrane
        self.run_integration = self.run_integration \
            and self.live_profile.run_integration
        self.run_observation = self.run_observation \
            and self.live_profile.run_observation
        if not self.max_runtime_s:
            self._refused = True

    # -- state layout -------------------------------------------------------

    def initialize(self) -> Dict[str, Any]:
        created = []
        for sub in self._LIVE_SUBDIRS:
            path = os.path.join(self.state_dir, sub)
            existed = os.path.isdir(path)
            os.makedirs(path, exist_ok=True)
            created.append({"name": f"live/{sub}", "existed": existed})
        for sub in self._TESTER_SUBDIRS:
            path = os.path.join(self.tester_state_dir, sub)
            existed = os.path.isdir(path)
            os.makedirs(path, exist_ok=True)
            created.append({"name": f"tester/{sub}", "existed": existed})
        return {"state_dir": self.state_dir,
                "tester_state_dir": self.tester_state_dir,
                "directories": created, "deletes_state": False}

    def run_doctor(self) -> Dict[str, Any]:
        self.initialize()
        self.doctor_result = TesterLiveDoctor(strict=self.strict).check(
            state_dir=self.state_dir)
        return self.doctor_result.to_dict()

    # -- run ----------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        if self._refused or not self.safety.validate_bounded(
                self.max_runtime_s).safe:
            return {"refused": True, "reason": "unbounded runtime"}
        self.initialize()

        if self.write_templates and not self.dry_run:
            self._write_templates()

        self._fixture_spine_gate()
        self.doctor_result = TesterLiveDoctor(strict=self.strict).check(
            state_dir=self.state_dir)

        if self.validate_samples:
            self.sample_validation = SafeEventPackValidator(
                strict=True).validate_pack(SafeEventPackBuilder().build())

        self._collect_governance_feeder_status()

        if self.copy_safe_samples_to_inbox and not self.dry_run:
            self._copy_safe_samples_to_inbox()

        # Live stages run only when explicitly requested AND governance allows.
        gov_ok = self.governance_status.get("enabled_and_approved", False)
        if (self.run_birth or self.run_membrane or self.run_observation) \
                and self.require_governance and not gov_ok:
            self.warnings.append(
                "governance not enabled+approved; live stages skipped (edit "
                "governance by hand to enable live-read-only testing)")
            if self.strict:
                self.blocked = True
                self.blockers.append("governance not enabled+approved")
        else:
            self._run_live_stages()

        # Strict doctor blockers fail the run.
        if self.strict and not self.doctor_result.passed:
            self.blocked = True
            self.blockers.extend(f.detail or f.check
                                 for f in self.doctor_result.blockers)

        if not self.dry_run:
            self._write_reports()
            self._build_bundle()
        self._update_integrations()
        return self._result()

    # -- stages -------------------------------------------------------------

    def _write_templates(self) -> None:
        gov = GovernanceTemplateBuilder()
        feeders = TesterFeederTemplateBuilder()
        tmpl_dir = os.path.join(self.tester_state_dir, "templates")
        os.makedirs(tmpl_dir, exist_ok=True)
        gov.write_template(os.path.join(
            tmpl_dir, "LIVE_READONLY_GOVERNANCE.tester.template.json"))
        feeders.write_template(os.path.join(
            tmpl_dir, "FEEDER_REGISTRY.tester.template.json"))
        # Into the live state (never overwrites a customized file).
        self.template_results = {
            "governance": gov.write_live_governance(self.state_dir),
            "feeders": feeders.write_live_registry(self.state_dir)}
        # Sample event packs into the tester sample_events dir.
        SafeEventPackBuilder().write_packs(self.tester_state_dir)
        # Checklist.
        checklist = TesterLiveChecklist.build()
        with open(os.path.join(self.tester_state_dir, "checklists",
                               "TESTER_LIVE_CHECKLIST.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(checklist.to_markdown())

    def _fixture_spine_gate(self) -> None:
        base = os.path.join(self.tester_state_dir, "..", "reports")
        # Tester fixture spine writes summaries under .solaris_ai_nn_tester/reports.
        tester_root = os.path.dirname(os.path.normpath(self.tester_state_dir))
        reports_dir = os.path.join(tester_root, "reports")
        status = "unavailable"
        if os.path.isdir(reports_dir):
            summaries = sorted(f for f in os.listdir(reports_dir)
                               if f.startswith("TESTER_RUN_SUMMARY_")
                               and f.endswith(".json"))
            if summaries:
                try:
                    with open(os.path.join(reports_dir, summaries[-1]),
                              encoding="utf-8") as fh:
                        data = json.load(fh)
                    repro = (data.get("reproducibility", {}) or {}).get(
                        "reproducibility_status", "")
                    status = ("passed" if repro in ("pass", "pass_with_warnings")
                              else "failed" if repro in ("fail", "blocked")
                              else "unknown")
                except Exception:
                    status = "unknown"
        self.fixture_status = {"fixture_demo_status": status,
                               "recommended_before_live": True}
        if status == "unavailable":
            self.warnings.append(
                "fixture tester demo status unavailable; run `tester-demo` first")
        elif status == "failed":
            self.warnings.append("fixture tester demo failed; resolve before live")
            if self.strict:
                self.blocked = True
                self.blockers.append("fixture tester demo failed")

    def _collect_governance_feeder_status(self) -> None:
        gov = GovernanceTemplateBuilder.load(self.state_dir)
        self.governance_status = {
            "status": gov.status,
            "enabled_and_approved": gov.enabled_and_approved,
            "control_rules_all_false": gov.control_rules_all_false(),
            "forbidden_sources": gov.forbidden_sources(),
            "allowed_sources": list(gov.data.get("allowed_sources", [])),
        }
        registry = TesterFeederTemplateBuilder.load(self.state_dir)
        self.feeder_status = {
            "feeder_count": len(registry.feeders),
            "invalid_record_count": len(registry.invalid_records),
            "all_external": all(f.started_externally for f in registry.feeders)
            if registry.feeders else False,
            "source_ids": registry.source_ids(),
            "solaris_controls_any_feeder": bool(registry.invalid_records),
        }

    def _copy_safe_samples_to_inbox(self) -> None:
        pack = SafeEventPackBuilder().build()
        inbox = os.path.join(self.state_dir, "inbox")
        os.makedirs(inbox, exist_ok=True)
        path = os.path.join(inbox, "tester_live_safe_events.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            for ev in pack.safe_event_dicts():
                fh.write(json.dumps(ev, separators=(",", ":")))
                fh.write("\n")
        self.warnings.append(
            "copied safe sample events into the local inbox (explicit flag); "
            "Solaris did not start any feeder")

    def _run_live_stages(self) -> None:
        if self.run_birth:
            self._run_birth_stage()
        if self.run_membrane:
            self._run_membrane_stage()
        if self.run_integration:
            self._run_integration_stage()
        if self.run_observation:
            self._run_observation_stage()

    def _run_birth_stage(self) -> None:
        try:
            from ..live_birth import LiveReadOnlyBirthRuntime
            rt = LiveReadOnlyBirthRuntime(
                state_dir=self.state_dir, max_events=self.max_events,
                require_governance=self.require_governance)
            rt.run()
            self.birth_status = rt.live_birth_status()
            q = rt.quarantine
            self.quarantine_summary = {
                "quarantined_count": len(q.records) if q else 0,
                "records": [{"event_id": (r.original or {}).get("event_id", "")
                             if isinstance(r.original, dict) else "",
                             "reason": getattr(r, "reasons",
                                               getattr(r, "reason", ""))}
                            for r in (q.records if q else [])]}
        except Exception as exc:  # pragma: no cover - defensive
            self.warnings.append(f"birth stage error: {exc}")

    def _run_membrane_stage(self) -> None:
        try:
            from ..environmental_membrane import EnvironmentalMembraneRuntime
            rt = EnvironmentalMembraneRuntime(
                state_dir=self.state_dir, max_events=self.max_events,
                require_governance=self.require_governance,
                require_feeder_registry=False)
            rt.run()
            self.membrane_status = rt.membrane_status()
            if self.require_membrane and not self.membrane_status.get(
                    "membrane_impression_count") and self.strict:
                self.blocked = True
                self.blockers.append("membrane produced no impressions")
        except Exception as exc:  # pragma: no cover - defensive
            self.warnings.append(f"membrane stage error: {exc}")
            if self.require_membrane and self.strict:
                self.blocked = True
                self.blockers.append("environmental membrane unavailable")

    def _run_integration_stage(self) -> None:
        try:
            from ..membrane_integration import MembraneIntegrationRuntime
            rt = MembraneIntegrationRuntime(
                state_dir=self.state_dir, profile="live_integration_audit_v0",
                strict=self.strict)
            rt.run()
            self.integration_status = rt.integration_status()
            if self.strict and self.integration_status.get(
                    "critical_bypass_count", 0):
                self.blocked = True
                self.blockers.append("critical membrane bypass in strict mode")
        except Exception as exc:  # pragma: no cover - defensive
            self.warnings.append(f"integration stage error: {exc}")

    def _run_observation_stage(self) -> None:
        try:
            from ..live_observation import PostBirthLiveObservationRuntime
            rt = PostBirthLiveObservationRuntime(
                state_dir=self.state_dir, max_events=self.max_events,
                require_governance=self.require_governance,
                require_birth_certificate=False)
            rt.run()
            self.observation_status = rt.observation_status()
        except Exception as exc:  # pragma: no cover - defensive
            self.warnings.append(f"observation stage error: {exc}")

    def _write_reports(self) -> None:
        from .live_tester_report import TesterLiveReportBuilder
        from .reports import TesterLiveReadOnlyReportBuilder

        self.reports = TesterLiveReportBuilder(self).write()
        TesterLiveReadOnlyReportBuilder(self).write()

    def _build_bundle(self) -> None:
        from .live_tester_bundle import TesterLiveBundleBuilder
        self.bundle = TesterLiveBundleBuilder().build(self)

    def _update_integrations(self) -> None:
        try:
            from ..inner_map.model import InnerMapModel  # noqa: F401
            self._inner_map_record = self.inner_map_record()
        except Exception:
            self.warnings.append("inner map unavailable (record skipped)")

    # -- views --------------------------------------------------------------

    def tester_live_status(self) -> Dict[str, Any]:
        doc = self.doctor_result.to_dict() if self.doctor_result else {}
        return {
            "tester_live_available": True,
            "tester_live_run_id": self.run_id,
            "tester_live_profile": self.live_profile.profile_id,
            "live_read_only": True,
            "tester_live_blocked": self.blocked,
            "governance_status": self.governance_status.get("status", "missing"),
            "governance_enabled_and_approved": self.governance_status.get(
                "enabled_and_approved", False),
            "feeder_registry_present": self.feeder_status.get(
                "feeder_count", 0) > 0,
            "solaris_controls_any_feeder": self.feeder_status.get(
                "solaris_controls_any_feeder", False),
            "live_doctor_status": doc.get("overall_status", "unknown"),
            "membrane_present": bool(self.membrane_status.get(
                "membrane_impression_count")),
            "membrane_impression_count": self.membrane_status.get(
                "membrane_impression_count", 0),
            "quarantine_count": self.quarantine_summary.get(
                "quarantined_count", 0),
            "critical_blocker_count": len(self.blockers),
            "fixture_demo_status": self.fixture_status.get(
                "fixture_demo_status", "unavailable"),
            "latest_tester_live_report_path": self.reports.get("markdown"),
            "latest_tester_live_bundle_path": self.bundle_dir,
            "tester_live_safety_block_count": self.safety.rejected_count,
            "starts_feeders": False, "controls_hardware": False,
            "accesses_network": False, "runs_git": False, "publishes": False,
            "trains_on_feedback": False,
        }

    def snapshot(self) -> Dict[str, Any]:
        return self.tester_live_status()

    def inner_map_record(self) -> Dict[str, Any]:
        return {
            "tester_live_run_id": self.run_id,
            "governance_status": self.governance_status.get("status", "missing"),
            "feeder_registry_status": "present"
            if self.feeder_status.get("feeder_count", 0) else "missing",
            "live_doctor_status": self.doctor_result.overall_status
            if self.doctor_result else "unknown",
            "sample_validation_status": "ok" if (
                self.sample_validation.get("safe", {}).get("all_accepted")
                and self.sample_validation.get("unsafe", {}).get(
                    "all_quarantined")) else "incomplete",
            "latest_live_tester_bundle_path": self.bundle_dir,
            "latest_live_tester_report_path": self.reports.get("markdown"),
            "live_read_only": True, "trains_on_feedback": False,
        }

    def recommended_next_steps(self) -> List[str]:
        steps: List[str] = []
        if self.fixture_status.get("fixture_demo_status") != "passed":
            steps.append("Run the fixture tester demo first: "
                         "`python -m solaris_ai_nn tester-demo`.")
        if not self.governance_status.get("enabled_and_approved"):
            steps.append("Edit governance by hand to set live_readonly_enabled "
                         "and operator_approved, then re-run the doctor.")
        if self.doctor_result and not self.doctor_result.passed:
            steps.append("Resolve the live tester doctor blockers.")
        if not steps:
            steps.append("Optionally run external feeders manually, then run "
                         "tester-live-run with the desired stages.")
        return steps

    def _run_summary(self) -> Dict[str, Any]:
        return {
            "tester_live_run_id": self.run_id,
            "tester_live_profile": self.live_profile.to_dict(),
            "fixture_status": self.fixture_status,
            "governance_status": self.governance_status,
            "feeder_status": self.feeder_status,
            "live_doctor": self.doctor_result.to_dict()
            if self.doctor_result else {},
            "sample_validation": self.sample_validation,
            "birth_status": self.birth_status,
            "membrane_status": self.membrane_status,
            "integration_status": self.integration_status,
            "observation_status": self.observation_status,
            "quarantine_summary": self.quarantine_summary,
            "blocked": self.blocked, "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "recommended_next_steps": self.recommended_next_steps(),
            "safety_status": self.safety.snapshot(),
        }

    def _result(self) -> Dict[str, Any]:
        return {
            "refused": False, "run_id": self.run_id, "blocked": self.blocked,
            "blockers": list(self.blockers),
            "tester_live_profile": self.live_profile.profile_id,
            "governance_status": self.governance_status.get("status", "missing"),
            "live_doctor_status": self.doctor_result.overall_status
            if self.doctor_result else "unknown",
            "membrane_impression_count": self.membrane_status.get(
                "membrane_impression_count", 0),
            "quarantine_count": self.quarantine_summary.get(
                "quarantined_count", 0),
            "tester_live_report": self.reports.get("markdown"),
            "tester_live_bundle": self.bundle_dir if self.bundle else None,
            "recommended_next_steps": self.recommended_next_steps(),
        }
