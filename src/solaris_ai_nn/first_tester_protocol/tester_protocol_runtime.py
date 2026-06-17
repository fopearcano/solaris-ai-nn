"""First tester protocol runtime -- bounded, local, documentation-only generation.

:class:`FirstTesterProtocolRuntime` reads the RC, packaging, and safety-freeze status
(read-only), generates the session script, acceptance criteria, stop conditions, task
sheet, handoff guide, and post-test review template, and writes the protocol reports. It
computes a session status (``ready``/``ready_with_warnings``/``blocked``) from the
preconditions. It never runs the tester session, installs packages, accesses the network/
shell/Git/GitHub, controls hardware/feeders, opens a browser, publishes/uploads, creates
releases/tags/issues, trains on feedback, or executes artifact contents.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .acceptance_criteria import FirstTesterAcceptanceCriteria
from .artifact_handoff import FirstTesterArtifactHandoff
from .post_test_review import FirstTesterPostTestReview
from .protocol_profile import get_protocol_profile
from .safety import FirstTesterProtocolSafetyValidator
from .session_script import FirstTesterSessionScript
from .stop_conditions import FirstTesterStopConditions
from .tester_task_sheet import FirstTesterTaskSheet


class SessionStatus:
    READY = "ready"
    READY_WITH_WARNINGS = "ready_with_warnings"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"

    ALL = (READY, READY_WITH_WARNINGS, BLOCKED, UNKNOWN)


@dataclass
class FirstTesterProtocolRuntime:
    """Bounded, local, documentation-only first-tester protocol runtime."""

    tester_state_dir: str = ".solaris_ai_nn_tester"
    protocol_dir: str = ""
    profile: Optional[str] = None
    max_runtime_s: float = 60.0
    strict: bool = False
    dry_run: bool = False
    report_only: bool = False
    script_only: bool = False
    acceptance_only: bool = False
    handoff_only: bool = False
    review_only: bool = False
    require_rc: bool = False
    require_safety_freeze: bool = False
    require_packaging: bool = False
    require_claimguard: bool = False

    safety: FirstTesterProtocolSafetyValidator = field(
        default_factory=FirstTesterProtocolSafetyValidator, init=False)
    protocol_profile: Any = field(default=None, init=False)
    run_id: str = field(default="", init=False)
    rc_status: Dict[str, Any] = field(default_factory=dict, init=False)
    packaging_status: Dict[str, Any] = field(default_factory=dict, init=False)
    safety_freeze_status: Dict[str, Any] = field(default_factory=dict,
                                                 init=False)
    fixture_status: Dict[str, Any] = field(default_factory=dict, init=False)
    session_script: Any = field(default=None, init=False)
    acceptance: Any = field(default=None, init=False)
    stop_conditions: Any = field(default=None, init=False)
    task_sheet: Any = field(default=None, init=False)
    handoff: Any = field(default=None, init=False)
    review: Any = field(default=None, init=False)
    doc_paths: Dict[str, str] = field(default_factory=dict, init=False)
    reports: Dict[str, Any] = field(default_factory=dict, init=False)
    blockers: List[str] = field(default_factory=list, init=False)
    warnings: List[str] = field(default_factory=list, init=False)
    _refused: bool = field(default=False, init=False)

    _SUBDIRS = ("reports", "scripts", "checklists", "handoff", "review",
                "index", "safety")

    def __post_init__(self) -> None:
        prof = self.profile
        if self.script_only:
            prof = "first_tester_script_only_v0"
        elif self.acceptance_only:
            prof = "first_tester_acceptance_only_v0"
        elif self.handoff_only:
            prof = "first_tester_handoff_only_v0"
        elif self.review_only:
            prof = "first_tester_review_only_v0"
        self.protocol_profile = get_protocol_profile(prof)
        if not self.protocol_dir:
            self.protocol_dir = os.path.join(self.tester_state_dir,
                                             "first_tester_protocol")
        self.run_id = f"firsttester_{int(time.time() * 1000)}"
        if not self.max_runtime_s:
            self._refused = True

    def _sub(self, name: str) -> str:
        return os.path.join(self.protocol_dir, name)

    def initialize(self) -> Dict[str, Any]:
        created = []
        for sub in self._SUBDIRS:
            path = self._sub(sub)
            existed = os.path.isdir(path)
            os.makedirs(path, exist_ok=True)
            created.append({"name": sub, "existed": existed})
        return {"protocol_dir": self.protocol_dir, "directories": created,
                "documentation_only": True}

    def run_doctor(self) -> Dict[str, Any]:
        return {"protocol_profile": self.protocol_profile.profile_id,
                "bounded": self.safety.validate_bounded(self.max_runtime_s).safe,
                "documentation_only": True, "passed": True,
                "note": "first-tester protocol doctor validates the profile + "
                        "bounded runtime; it is documentation-only"}

    def run(self) -> Dict[str, Any]:
        if self._refused or not self.safety.validate_bounded(
                self.max_runtime_s).safe:
            return {"refused": True, "reason": "unbounded runtime"}
        self.initialize()
        p = self.protocol_profile
        self._gather_preconditions()

        if p.generate_script or p.mode in ("first_tester_protocol_full",
                                           "report_only"):
            self.session_script = FirstTesterSessionScript()
        if p.generate_acceptance or p.mode in ("first_tester_protocol_full",
                                               "report_only"):
            self.acceptance = FirstTesterAcceptanceCriteria()
        if p.generate_stop_conditions or p.mode in (
                "first_tester_protocol_full", "report_only"):
            self.stop_conditions = FirstTesterStopConditions()
        if p.generate_task_sheet or p.mode in ("first_tester_protocol_full",
                                               "report_only"):
            self.task_sheet = FirstTesterTaskSheet()
        if p.generate_handoff or p.mode in ("first_tester_protocol_full",
                                            "report_only"):
            self.handoff = FirstTesterArtifactHandoff()
        if p.generate_review or p.mode in ("first_tester_protocol_full",
                                           "report_only"):
            self.review = FirstTesterPostTestReview()

        if not self.dry_run:
            self._write_docs()
            self._build_reports()

        if self.require_claimguard and not _claimguard_available():
            self.warnings.append("ClaimGuard required but unavailable")
        self._update_integrations()
        return self._result()

    # -- preconditions ------------------------------------------------------

    def _gather_preconditions(self) -> None:
        ts = self.tester_state_dir
        self.rc_status = self._rc_status(ts)
        self.packaging_status = self._packaging_status(ts)
        self.safety_freeze_status = self._safety_freeze_status(ts)
        self.fixture_status = self._fixture_status(ts)

        rc = self.rc_status
        if rc.get("rc_available"):
            if rc.get("readiness") in ("blocked", "critical_blocked"):
                self.blockers.append("RC is blocked; resolve RC blockers before "
                                     "the first tester session")
        elif self.require_rc:
            self.blockers.append("RC not present but required")
        else:
            self.warnings.append("RC not present; run `tester-rc` first")

        pkg = self.packaging_status
        if pkg.get("packaging_available"):
            if pkg.get("readiness") == "blocked":
                self.blockers.append("packaging doctor is blocked; resolve "
                                     "packaging blockers before the session")
        elif self.require_packaging:
            self.blockers.append("packaging not present but required")
        else:
            self.warnings.append("packaging not present; run `tester-packaging`")

        sf = self.safety_freeze_status
        if sf.get("safety_freeze_available"):
            if sf.get("readiness") in ("blocked", "critical_blocked"):
                self.blockers.append("safety freeze is blocked; resolve safety "
                                     "blockers before the session")
        elif self.require_safety_freeze:
            self.blockers.append("safety freeze not present but required")
        else:
            self.warnings.append("safety freeze not present; run "
                                 "`tester-safety-freeze`")

        if self.fixture_status.get("fixture_passed") is False:
            self.warnings.append("fixture demo did not pass; live-read-only is "
                                 "blocked until the fixture demo passes")

    def _rc_status(self, ts: str) -> Dict[str, Any]:
        data = _load_json(os.path.join(ts, "release_candidate", "manifests",
                                       "TESTER_RC_MANIFEST.json"))
        available = bool(data) or os.path.isdir(
            os.path.join(ts, "release_candidate"))
        return {
            "rc_available": available,
            "readiness": data.get("readiness", "unknown"),
            "blocker_count": data.get("blocker_count", 0),
            "latest_rc_manifest_path": os.path.join(
                ts, "release_candidate", "manifests",
                "TESTER_RC_MANIFEST.json"),
        }

    def _packaging_status(self, ts: str) -> Dict[str, Any]:
        data = _load_json(os.path.join(ts, "packaging", "reports",
                                       "PACKAGING_REPORT.json"))
        st = (data.get("sections", {}) or {}).get("packaging_status", {}) \
            if isinstance(data, dict) else {}
        available = bool(st) or os.path.isdir(os.path.join(ts, "packaging"))
        return {"packaging_available": available,
                "readiness": st.get("readiness", "unknown"),
                "doctor_status": st.get("doctor_status", "unknown")}

    def _safety_freeze_status(self, ts: str) -> Dict[str, Any]:
        data = _load_json(os.path.join(ts, "safety_freeze", "manifests",
                                       "TESTER_SAFETY_FREEZE_MANIFEST.json"))
        available = bool(data) or os.path.isdir(
            os.path.join(ts, "safety_freeze"))
        return {"safety_freeze_available": available,
                "readiness": data.get("readiness", "unknown"),
                "open_release_blocker_count": data.get("release_blocker_count",
                                                       0)}

    def _fixture_status(self, ts: str) -> Dict[str, Any]:
        reports = os.path.join(ts, "reports")
        passed = None
        if os.path.isdir(reports):
            summaries = sorted(f for f in os.listdir(reports)
                               if f.startswith("TESTER_RUN_SUMMARY_")
                               and f.endswith(".json"))
            if summaries:
                data = _load_json(os.path.join(reports, summaries[-1]))
                repro = (data.get("reproducibility", {}) or {}).get(
                    "reproducibility_status", "")
                passed = repro in ("pass", "pass_with_warnings")
        return {"fixture_passed": passed}

    # -- writers ------------------------------------------------------------

    def _write_docs(self) -> None:
        if self.session_script:
            self.doc_paths["session_script"] = self.session_script.write(
                self._sub("scripts"))
        if self.acceptance:
            self.doc_paths["acceptance_criteria"] = self.acceptance.write(
                self._sub("checklists"))
        if self.stop_conditions:
            self.doc_paths["stop_conditions"] = self.stop_conditions.write(
                self._sub("checklists"))
        if self.task_sheet:
            paths = self.task_sheet.write(self._sub("checklists"))
            self.doc_paths["task_sheet"] = paths["markdown"]
        if self.handoff:
            self.doc_paths["handoff_guide"] = self.handoff.write(
                self._sub("handoff"))
        if self.review:
            self.doc_paths["review_template"] = self.review.write(
                self._sub("reports"))

    def _build_reports(self) -> None:
        from .reports import FirstTesterProtocolReportBuilder
        self.reports = FirstTesterProtocolReportBuilder(self).write()

    def _update_integrations(self) -> None:
        try:
            from ..inner_map.model import InnerMapModel  # noqa: F401
            self._inner_map_record = self.inner_map_record()
        except Exception:
            self.warnings.append("inner map unavailable (record skipped)")

    # -- views --------------------------------------------------------------

    def session_status(self) -> str:
        if self.blockers:
            return SessionStatus.BLOCKED
        if self.warnings:
            return SessionStatus.READY_WITH_WARNINGS
        return SessionStatus.READY

    def protocol_status(self) -> Dict[str, Any]:
        return {
            "first_tester_protocol_available": True,
            "run_id": self.run_id,
            "protocol_profile": self.protocol_profile.profile_id,
            "session_status": self.session_status(),
            "blocker_count": len(self.blockers),
            "warning_count": len(self.warnings),
            "rc_readiness": self.rc_status.get("readiness", "unknown"),
            "packaging_readiness": self.packaging_status.get("readiness",
                                                            "unknown"),
            "safety_freeze_readiness": self.safety_freeze_status.get(
                "readiness", "unknown"),
            "latest_protocol_report_path": self.reports.get("markdown"),
            "session_script_path": self.doc_paths.get("session_script"),
            "acceptance_criteria_path": self.doc_paths.get(
                "acceptance_criteria"),
            "stop_conditions_path": self.doc_paths.get("stop_conditions"),
            "handoff_guide_path": self.doc_paths.get("handoff_guide"),
            "task_sheet_path": self.doc_paths.get("task_sheet"),
            "review_template_path": self.doc_paths.get("review_template"),
            "protocol_safety_block_count": self.safety.rejected_count,
            "local_only": True, "runs_session": False, "published": False,
        }

    def snapshot(self) -> Dict[str, Any]:
        return self.protocol_status()

    def inner_map_record(self) -> Dict[str, Any]:
        st = self.protocol_status()
        return {
            "first_tester_protocol_run_id": self.run_id,
            "protocol_profile": st["protocol_profile"],
            "session_status": st["session_status"],
            "blocker_count": st["blocker_count"],
            "warning_count": st["warning_count"],
            "session_script_path": st["session_script_path"],
            "acceptance_criteria_path": st["acceptance_criteria_path"],
            "handoff_guide_path": st["handoff_guide_path"],
            "review_template_path": st["review_template_path"],
            "local_only": True,
        }

    def recommended_next_action(self) -> str:
        if self.blockers:
            return ("Resolve the protocol blockers (RC/packaging/safety freeze) "
                    "before running the first tester session.")
        if self.warnings:
            return ("Review the warnings, then the tester can run the first "
                    "tester session following the session script.")
        return ("The first tester can run the session following the session "
                "script; stop conditions override curiosity.")

    def _run_summary(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "protocol_profile": self.protocol_profile.to_dict(),
            "protocol_status": self.protocol_status(),
            "rc_status": self.rc_status,
            "packaging_status": self.packaging_status,
            "safety_freeze_status": self.safety_freeze_status,
            "fixture_status": self.fixture_status,
            "session_script": self.session_script.to_dict()
            if self.session_script else {},
            "acceptance": self.acceptance.to_dict() if self.acceptance else {},
            "stop_conditions": self.stop_conditions.to_dict()
            if self.stop_conditions else {},
            "task_sheet": self.task_sheet.to_dict() if self.task_sheet else {},
            "handoff": self.handoff.to_dict() if self.handoff else {},
            "review": self.review.to_dict() if self.review else {},
            "doc_paths": self.doc_paths,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "next_action": self.recommended_next_action(),
            "safety_status": self.safety.snapshot(),
        }

    def _result(self) -> Dict[str, Any]:
        st = self.protocol_status()
        return {
            "refused": False, "run_id": self.run_id,
            "protocol_profile": st["protocol_profile"],
            "session_status": st["session_status"],
            "blocker_count": st["blocker_count"],
            "warning_count": st["warning_count"],
            "blocked": st["blocker_count"] > 0,
            "latest_protocol_report_path": st["latest_protocol_report_path"],
            "session_script_path": st["session_script_path"],
            "next_action": self.recommended_next_action(),
        }


def _load_json(path: str) -> Dict[str, Any]:
    try:
        if not os.path.isfile(path) or os.path.getsize(path) > 5_000_000:
            return {}
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _claimguard_available() -> bool:
    try:
        from ..governance.compliance import ClaimGuard  # noqa: F401
        return True
    except Exception:
        return False
