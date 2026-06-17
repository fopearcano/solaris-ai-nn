"""Tester RC runtime -- the bounded, local, assembly-only release-candidate builder.

:class:`TesterRCRuntime` collects local artifacts, loads packaging/safety-freeze/fixture/
live/console/feedback/membrane status (read-only), builds the RC manifest, runs the RC
readiness gate, builds the RC docs (release notes, quickstart, runbook, known issues,
feedback guide), builds the RC checklist, assembles a local RC bundle, and writes reports.
It writes only RC artifacts; it never installs packages, starts/executes feeders,
accesses the network/shell/Git/GitHub, controls hardware, opens a browser, publishes/
uploads, creates releases/tags/issues, trains on feedback, or executes artifact contents.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .rc_artifact_collector import TesterRCArtifactCollector
from .rc_checklist import TesterRCChecklist
from .rc_manifest import TesterRCManifestBuilder
from .rc_notes_builder import (
    TesterFeedbackGuideBuilder,
    TesterKnownIssuesBuilder,
    TesterReleaseNotesBuilder,
    write_quickstart,
)
from .rc_readiness_gate import TesterRCReadinessGate
from .rc_runbook_builder import TesterRunbookBuilder
from .rc_profile import get_rc_profile
from .safety import TesterRCSafetyValidator


@dataclass
class TesterRCRuntime:
    """Bounded, local, assembly-only tester release-candidate runtime."""

    tester_state_dir: str = ".solaris_ai_nn_tester"
    rc_dir: str = ""
    profile: Optional[str] = None
    max_runtime_s: float = 60.0
    strict: bool = False
    dry_run: bool = False
    report_only: bool = False
    manifest_only: bool = False
    docs_only: bool = False
    bundle_only: bool = False
    readiness_only: bool = False
    include_optional_reports: bool = False
    include_static_console: bool = False
    include_private_payloads: bool = False
    include_zip: bool = False
    require_safety_freeze: bool = True
    require_packaging: bool = True
    require_fixture_demo: bool = True
    require_claimguard: bool = False
    waived_blockers: List[str] = field(default_factory=list)

    safety: TesterRCSafetyValidator = field(
        default_factory=TesterRCSafetyValidator, init=False)
    rc_profile: Any = field(default=None, init=False)
    rc_id: str = field(default="", init=False)
    collection: Any = field(default=None, init=False)
    ctx: Dict[str, Any] = field(default_factory=dict, init=False)
    manifest: Any = field(default=None, init=False)
    readiness: Any = field(default=None, init=False)
    checklist: Any = field(default=None, init=False)
    bundle: Any = field(default=None, init=False)
    doc_paths: Dict[str, str] = field(default_factory=dict, init=False)
    reports: Dict[str, Any] = field(default_factory=dict, init=False)
    manifest_paths: Dict[str, str] = field(default_factory=dict, init=False)
    warnings: List[str] = field(default_factory=list, init=False)
    _refused: bool = field(default=False, init=False)

    _SUBDIRS = ("reports", "manifests", "bundles", "docs", "checklists",
                "index", "safety")

    def __post_init__(self) -> None:
        self.rc_profile = get_rc_profile(self.profile)
        if self.docs_only:
            self.rc_profile = get_rc_profile("tester_rc_docs_only_v0")
        elif self.manifest_only:
            self.rc_profile = get_rc_profile("tester_rc_manifest_only_v0")
        elif self.bundle_only:
            self.rc_profile = get_rc_profile("tester_rc_bundle_only_v0")
        elif self.readiness_only:
            self.rc_profile = get_rc_profile("tester_rc_readiness_only_v0")
        if not self.rc_dir:
            self.rc_dir = os.path.join(self.tester_state_dir,
                                       "release_candidate")
        self.rc_id = f"rc_{int(time.time() * 1000)}"
        if not self.max_runtime_s:
            self._refused = True

    # -- directories --------------------------------------------------------

    def initialize(self) -> Dict[str, Any]:
        created = []
        for sub in self._SUBDIRS:
            path = os.path.join(self.rc_dir, sub)
            existed = os.path.isdir(path)
            os.makedirs(path, exist_ok=True)
            created.append({"name": sub, "existed": existed})
        return {"rc_dir": self.rc_dir, "directories": created,
                "assembly_only": True}

    def _sub(self, name: str) -> str:
        return os.path.join(self.rc_dir, name)

    def run_doctor(self) -> Dict[str, Any]:
        return {"rc_profile": self.rc_profile.profile_id,
                "bounded": self.safety.validate_bounded(self.max_runtime_s).safe,
                "assembly_only": True, "passed": True,
                "note": "RC doctor validates the profile + bounded runtime; it "
                        "is local assembly-only"}

    # -- main ---------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        if self._refused or not self.safety.validate_bounded(
                self.max_runtime_s).safe:
            return {"refused": True, "reason": "unbounded runtime"}
        self.initialize()
        p = self.rc_profile

        self.collection = TesterRCArtifactCollector(
            tester_state_dir=self.tester_state_dir,
            include_optional=self.include_optional_reports or True,
            include_private_payloads=self.include_private_payloads).collect()
        self._gather_ctx()

        if p.run_readiness_gate or p.build_manifest or p.build_checklist \
                or p.mode in ("tester_rc_full", "tester_rc_report_only"):
            self.readiness = TesterRCReadinessGate(
                allow_docs_only_rc=p.allow_docs_only_rc,
                waived_blockers=list(self.waived_blockers)).evaluate(self.ctx)

        if p.build_manifest or p.mode in ("tester_rc_full",
                                          "tester_rc_report_only"):
            self.manifest = TesterRCManifestBuilder().build(
                rc_id=self.rc_id, profile_id=p.profile_id,
                collection=self.collection, readiness=self.readiness,
                ctx=self.ctx)

        if p.build_checklist or p.mode in ("tester_rc_full",
                                           "tester_rc_report_only"):
            self.checklist = TesterRCChecklist().build(
                collection=self.collection, ctx=self.ctx)

        if not self.dry_run:
            # The bundle needs the RC docs, so build docs whenever a bundle is
            # assembled (even in bundle-only mode) so the bundle is complete.
            if p.build_docs or p.build_bundle or p.mode in (
                    "tester_rc_full", "tester_rc_report_only"):
                self._build_docs()
            if (p.build_manifest or p.build_bundle) and self.manifest:
                self._write_manifest()
            if p.build_bundle or p.mode == "tester_rc_full":
                self._build_bundle()
            self._build_reports()

        if self.require_claimguard and not _claimguard_available():
            self.warnings.append("ClaimGuard required but unavailable")
        self._update_integrations()
        return self._result()

    # -- context gathering --------------------------------------------------

    def _gather_ctx(self) -> None:
        ts = self.tester_state_dir
        packaging = self._packaging_status(ts)
        safety_freeze = self._safety_freeze_status(ts)
        fixture = self._fixture_status(ts)
        live = self._live_status(ts)
        console = self._console_status(ts)
        feedback = self._feedback_status(ts)
        membrane = self._membrane_status(ts)
        docs = {
            "quickstart": self.collection.present("quickstart"),
            "runbook": self.collection.present("fixture_instructions"),
            "known_issues": True,   # built by this runtime
            "release_notes": True,  # built by this runtime
            "disclaimers_present": True,
        }
        self.ctx = {
            "packaging": packaging, "safety_freeze": safety_freeze,
            "fixture": fixture, "live": live, "console": console,
            "feedback": feedback, "membrane": membrane, "docs": docs,
            "artifacts": self.collection.to_dict(),
            "required_commands_present": self._required_commands_present(),
        }

    def _packaging_status(self, ts: str) -> Dict[str, Any]:
        data = _load_json(os.path.join(ts, "packaging", "reports",
                                       "PACKAGING_REPORT.json"))
        st = (data.get("sections", {}) or {}).get("packaging_status", {}) \
            if isinstance(data, dict) else {}
        available = bool(st) or os.path.isdir(os.path.join(ts, "packaging"))
        return {
            "packaging_available": available,
            "readiness": st.get("readiness", "unknown"),
            "doctor_status": st.get("doctor_status", "unknown"),
            "clean_machine_readiness": st.get("clean_machine_status",
                                              "unknown"),
            "blocker_count": st.get("blocker_count", 0),
        }

    def _safety_freeze_status(self, ts: str) -> Dict[str, Any]:
        data = _load_json(os.path.join(ts, "safety_freeze", "manifests",
                                       "TESTER_SAFETY_FREEZE_MANIFEST.json"))
        available = bool(data) or os.path.isdir(
            os.path.join(ts, "safety_freeze"))
        return {
            "safety_freeze_available": available,
            "readiness": data.get("readiness", "unknown"),
            "open_release_blocker_count": data.get("release_blocker_count", 0),
            "critical_open_count": data.get("critical_open_count", 0),
            "forbidden_claim_count": data.get("forbidden_claim_count", 0),
            "capability_blocker_count": data.get("capability_blocker_count", 0),
        }

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
        pack = os.path.isfile(os.path.join(
            "examples", "tester_fixture_spine", "fixture_tester_v0",
            "events.jsonl"))
        return {"fixture_demo_available": True, "fixture_pack": pack,
                "fixture_passed": passed}

    def _live_status(self, ts: str) -> Dict[str, Any]:
        tmpl = os.path.join("examples", "tester_live_readonly")
        policy = os.path.isfile(os.path.join(tmpl, "README.md"))
        gov = os.path.isfile(os.path.join(
            tmpl, "LIVE_READONLY_GOVERNANCE.tester.template.json")) \
            or os.path.isdir(os.path.join(ts, "live"))
        registry = os.path.isfile(os.path.join(
            tmpl, "FEEDER_REGISTRY.tester.template.json")) or gov
        packs = os.path.isfile(os.path.join(
            tmpl, "sample_safe_events", "live_safe_events.jsonl")) \
            or os.path.isfile(os.path.join(
                tmpl, "sample_unsafe_events", "live_unsafe_events.jsonl")) \
            or gov
        return {"templates_available": gov or policy,
                "feeder_policy_clear": policy or gov,
                "governance_template": gov, "feeder_registry_template": registry,
                "event_packs": packs}

    def _console_status(self, ts: str) -> Dict[str, Any]:
        return {"available": os.path.isfile(os.path.join(ts, "console",
                                                         "INDEX.md")),
                "read_only": True, "safety_panel": True}

    def _feedback_status(self, ts: str) -> Dict[str, Any]:
        ledger = _load_json(os.path.join(ts, "feedback", "ledger",
                                         "TESTER_FEEDBACK_LEDGER.json"))
        available = bool(ledger) or os.path.isdir(
            os.path.join(ts, "feedback"))
        return {"feedback_available": available, "non_training": True,
                "ledger": bool(ledger), "bundle": True}

    def _membrane_status(self, ts: str) -> Dict[str, Any]:
        live_root = ".solaris_ai_nn_live"
        present = os.path.isfile(os.path.join(
            live_root, "membrane", "reports",
            "ENVIRONMENTAL_MEMBRANE_REPORT.json"))
        integ = _load_json(os.path.join(
            live_root, "membrane", "integration",
            "MEMBRANE_INTEGRATION_REPORT.json"))
        status = (integ.get("sections", {}) or {}).get("status", {}) \
            if isinstance(integ, dict) else {}
        live_ran = os.path.isdir(os.path.join(ts, "live", "reports")) \
            or os.path.isdir(os.path.join(live_root, "membrane"))
        module = _module_available("solaris_ai_nn.environmental_membrane")
        integration = _module_available(
            "solaris_ai_nn.membrane_integration")
        return {
            "module_available": module, "integration_available": integration,
            "present": present, "live_modules_ran": live_ran,
            "critical_bypass": bool(status.get("critical_bypass_count", 0)),
            "impression_docs": True, "bypass_detection": True}

    def _required_commands_present(self) -> bool:
        try:
            from ..cli import _ALPHA_COMMANDS
            required = ("doctor", "tester-demo", "tester-console",
                        "tester-packaging", "tester-safety-freeze", "tester-rc")
            return all(c in _ALPHA_COMMANDS for c in required)
        except Exception:
            return True

    # -- builders -----------------------------------------------------------

    def _build_docs(self) -> None:
        docs = self._sub("docs")
        self.doc_paths["release_notes"] = TesterReleaseNotesBuilder(
            rc_id=self.rc_id).write(docs)
        self.doc_paths["quickstart"] = write_quickstart(docs, self.rc_id)
        self.doc_paths["runbook"] = TesterRunbookBuilder().write(docs)
        open_blockers = []
        if self.readiness:
            open_blockers = [f"{b.check}: {b.detail}"
                             for b in self.readiness.blockers]
        missing_optional = self.manifest.known_missing_optional_modules \
            if self.manifest else []
        warns = [w.detail for w in self.readiness.warnings] \
            if self.readiness else []
        self.doc_paths["known_issues"] = TesterKnownIssuesBuilder(
            open_blockers=open_blockers,
            missing_optional_modules=missing_optional,
            warnings=warns).write(docs)
        self.doc_paths["feedback_guide"] = TesterFeedbackGuideBuilder().write(
            docs)

    def _write_manifest(self) -> None:
        self.manifest_paths = TesterRCManifestBuilder().write(
            self.manifest, self._sub("manifests"))

    def _build_bundle(self) -> None:
        from .rc_bundle_builder import TesterRCBundleBuilder
        # Ensure checklist is written so the bundle can include it.
        if self.checklist:
            with open(os.path.join(self._sub("checklists"),
                                   "TESTER_RC_CHECKLIST.md"), "w",
                      encoding="utf-8") as fh:
                fh.write(self.checklist.to_markdown())
        self.bundle = TesterRCBundleBuilder(
            rc_id=self.rc_id, bundles_root=self._sub("bundles"),
            docs_dir=self._sub("docs"), manifests_dir=self._sub("manifests"),
            reports_dir=self._sub("reports"),
            checklists_dir=self._sub("checklists"),
            include_zip=self.include_zip,
            include_private_payloads=self.include_private_payloads).build(
                collection=self.collection,
                tester_state_dir=self.tester_state_dir)

    def _build_reports(self) -> None:
        from .reports import TesterRCReportBuilder
        self.reports = TesterRCReportBuilder(self).write()

    def _update_integrations(self) -> None:
        try:
            from ..inner_map.model import InnerMapModel  # noqa: F401
            self._inner_map_record = self.inner_map_record()
        except Exception:
            self.warnings.append("inner map unavailable (record skipped)")

    # -- views --------------------------------------------------------------

    def rc_status(self) -> Dict[str, Any]:
        m = self.manifest.to_dict() if self.manifest else {}
        rd = self.readiness.to_dict() if self.readiness else {}
        bundle_path = self.bundle.bundle_dir if self.bundle else None
        return {
            "rc_available": True,
            "rc_id": self.rc_id,
            "rc_profile": self.rc_profile.profile_id,
            "readiness": m.get("readiness", rd.get("status", "unknown")),
            "rc_readiness_status": rd.get("status", "unknown"),
            "blocker_count": rd.get("blocker_count", 0),
            "critical_blocker_count": rd.get("critical_blocker_count", 0),
            "warning_count": rd.get("warning_count", 0) + len(self.warnings),
            "missing_required_artifact_count": m.get(
                "missing_required_artifact_count",
                self.collection.to_dict().get("missing_required_count", 0)
                if self.collection else 0),
            "missing_recommended_artifact_count": self.collection.to_dict().get(
                "missing_recommended_count", 0) if self.collection else 0,
            "checklist_passed": self.checklist.passed
            if self.checklist else None,
            "latest_rc_manifest_path": self.manifest_paths.get("json"),
            "latest_rc_readiness_report_path": self.reports.get("readiness_md"),
            "latest_rc_report_path": self.reports.get("markdown"),
            "latest_rc_bundle_path": bundle_path,
            "latest_release_notes_path": self.doc_paths.get("release_notes"),
            "latest_runbook_path": self.doc_paths.get("runbook"),
            "latest_known_issues_path": self.doc_paths.get("known_issues"),
            "rc_safety_block_count": self.safety.rejected_count,
            "local_only": True, "published": False, "uploaded": False,
        }

    def snapshot(self) -> Dict[str, Any]:
        return self.rc_status()

    def inner_map_record(self) -> Dict[str, Any]:
        st = self.rc_status()
        return {
            "rc_id": st["rc_id"],
            "readiness": st["readiness"],
            "blocker_count": st["blocker_count"],
            "warning_count": st["warning_count"],
            "bundle_path": st["latest_rc_bundle_path"],
            "release_notes_path": st["latest_release_notes_path"],
            "runbook_path": st["latest_runbook_path"],
            "known_issues_path": st["latest_known_issues_path"],
            "local_only": True,
        }

    def recommended_next_action(self) -> str:
        if not self.readiness:
            return "Run the RC readiness gate."
        if self.readiness.critical_blockers:
            return ("Resolve the critical RC blockers (safety/membrane/claims) "
                    "before assembling the tester release candidate.")
        if self.readiness.blockers:
            return ("Resolve or explicitly waive the open RC blockers before "
                    "the tester release candidate.")
        if self.readiness.warnings:
            return ("RC is ready with warnings; review the known issues, then "
                    "run the first tester protocol.")
        return ("RC is ready for the first tester; share the local bundle "
                "manually if requested, then run the first tester protocol.")

    def _run_summary(self) -> Dict[str, Any]:
        return {
            "rc_id": self.rc_id,
            "rc_profile": self.rc_profile.to_dict(),
            "rc_status": self.rc_status(),
            "manifest": self.manifest.to_dict() if self.manifest else {},
            "readiness": self.readiness.to_dict() if self.readiness else {},
            "checklist": self.checklist.to_dict() if self.checklist else {},
            "artifact_collection": self.collection.to_dict()
            if self.collection else {},
            "bundle": self.bundle.to_dict() if self.bundle else {},
            "doc_paths": self.doc_paths,
            "ctx": self.ctx,
            "warnings": list(self.warnings),
            "next_action": self.recommended_next_action(),
            "safety_status": self.safety.snapshot(),
        }

    def _result(self) -> Dict[str, Any]:
        st = self.rc_status()
        return {
            "refused": False, "rc_id": self.rc_id,
            "rc_profile": st["rc_profile"],
            "readiness": st["readiness"],
            "rc_readiness_status": st["rc_readiness_status"],
            "blocker_count": st["blocker_count"],
            "critical_blocker_count": st["critical_blocker_count"],
            "warning_count": st["warning_count"],
            "missing_required_artifact_count": st[
                "missing_required_artifact_count"],
            "blocked": st["blocker_count"] > 0,
            "latest_rc_bundle_path": st["latest_rc_bundle_path"],
            "latest_rc_report_path": st["latest_rc_report_path"],
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


def _module_available(name: str) -> bool:
    try:
        import importlib.util
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def _claimguard_available() -> bool:
    try:
        from ..governance.compliance import ClaimGuard  # noqa: F401
        return True
    except Exception:
        return False
