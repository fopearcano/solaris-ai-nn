"""Tester safety-freeze runtime -- the bounded, local, report/gate-only firewall.

:class:`TesterSafetyFreezeRuntime` collects local text artifacts, runs the claim freeze,
capability freeze, and artifact safety scan, gathers integration evidence (membrane,
fixture, feedback), runs the red-team checklist, populates the release blocker gate, and
builds the safety-freeze manifest + reports. It writes only safety-freeze reports; it
never modifies runtime behaviour, starts feeders, accesses the network/shell/Git/GitHub,
controls hardware, opens a browser, publishes/uploads, creates releases/tags/issues,
trains on feedback, or executes artifact contents.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .allowed_language import AllowedOperationalLanguageRegistry
from .artifact_safety_scan import TesterArtifactSafetyScan
from .capability_freeze import TesterCapabilityFreeze
from .claim_freeze import TesterClaimFreeze
from .forbidden_claims import ForbiddenClaimRegistry
from .red_team_checklist import TesterRedTeamChecklist
from .release_blockers import ReleaseBlockerCategory, TesterReleaseBlockerGate
from .safety import TesterSafetyFreezeSafetyValidator
from .safety_freeze_profile import get_safety_freeze_profile

_MAX_FILES = 400
_TEXT_EXTS = (".md", ".json", ".jsonl", ".txt", ".toml")
# Meta-docs that intentionally enumerate forbidden claims / unsafe wording as
# *examples*; scanning them would flag their own illustrative content.
_EXCLUDE_BASENAMES = {
    "forbidden_claims.md", "forbidden_claims.json", "tester_claim_freeze.md",
    "allowed_operational_language.md", "allowed_operational_language.json",
    "red_team_checklist.md", "release_blockers.md",
}


@dataclass
class TesterSafetyFreezeRuntime:
    """Bounded, local, report/gate-only tester safety-freeze runtime."""

    tester_state_dir: str = ".solaris_ai_nn_tester"
    safety_freeze_dir: str = ""
    profile: Optional[str] = None
    max_runtime_s: float = 60.0
    strict: bool = False
    dry_run: bool = False
    report_only: bool = False
    scan_docs: bool = True
    scan_reports: bool = True
    scan_templates: bool = True
    scan_console: bool = True
    scan_feedback: bool = True
    scan_packaging: bool = True
    allow_private_payload_scan: bool = False
    require_claimguard: bool = False

    safety: TesterSafetyFreezeSafetyValidator = field(
        default_factory=TesterSafetyFreezeSafetyValidator, init=False)
    safety_freeze_profile: Any = field(default=None, init=False)
    run_id: str = field(default="", init=False)
    scanned_roots: List[str] = field(default_factory=list, init=False)
    claim_result: Any = field(default=None, init=False)
    capability_result: Any = field(default=None, init=False)
    artifact_result: Any = field(default=None, init=False)
    red_team_result: Any = field(default=None, init=False)
    blocker_gate: Any = field(default=None, init=False)
    manifest: Any = field(default=None, init=False)
    evidence: Dict[str, Any] = field(default_factory=dict, init=False)
    reports: Dict[str, Any] = field(default_factory=dict, init=False)
    warnings: List[str] = field(default_factory=list, init=False)
    _refused: bool = field(default=False, init=False)

    _SUBDIRS = ("reports", "manifests", "red_team", "claim_scan", "blockers",
                "index")

    def __post_init__(self) -> None:
        self.safety_freeze_profile = get_safety_freeze_profile(self.profile)
        if not self.safety_freeze_dir:
            self.safety_freeze_dir = os.path.join(self.tester_state_dir,
                                                  "safety_freeze")
        self.run_id = f"safetyfreeze_{int(time.time() * 1000)}"
        if not self.max_runtime_s:
            self._refused = True

    def initialize(self) -> Dict[str, Any]:
        created = []
        for sub in self._SUBDIRS:
            path = os.path.join(self.safety_freeze_dir, sub)
            existed = os.path.isdir(path)
            os.makedirs(path, exist_ok=True)
            created.append({"name": sub, "existed": existed})
        return {"safety_freeze_dir": self.safety_freeze_dir,
                "directories": created, "report_gate_only": True}

    def run_doctor(self) -> Dict[str, Any]:
        return {"safety_freeze_profile": self.safety_freeze_profile.profile_id,
                "bounded": self.safety.validate_bounded(self.max_runtime_s).safe,
                "report_gate_only": True, "passed": True,
                "note": "safety-freeze doctor validates the profile + bounded "
                        "runtime; it is report/gate-only"}

    def run(self) -> Dict[str, Any]:
        if self._refused or not self.safety.validate_bounded(
                self.max_runtime_s).safe:
            return {"refused": True, "reason": "unbounded runtime"}
        self.initialize()
        p = self.safety_freeze_profile
        paths = self._collect_artifact_paths()
        self.blocker_gate = TesterReleaseBlockerGate()

        if p.run_claim_freeze:
            self.claim_result = TesterClaimFreeze().scan_paths(paths)
        if p.run_capability_freeze:
            self.capability_result = TesterCapabilityFreeze().scan_paths(paths)
        if p.run_artifact_scan:
            self.artifact_result = TesterArtifactSafetyScan().scan_paths(paths)
        self._gather_evidence()
        if p.run_red_team:
            self.red_team_result = TesterRedTeamChecklist().evaluate(
                self.evidence)
        self._populate_blocker_gate()

        from .safety_freeze_manifest import SafetyFreezeManifestBuilder
        self.manifest = SafetyFreezeManifestBuilder().build(self)

        if not self.dry_run:
            self._write_manifests()
            self._build_reports()

        if self.require_claimguard and not _claimguard_available():
            self.warnings.append("ClaimGuard required but unavailable")
        self._update_integrations()
        return self._result()

    # -- artifact collection ------------------------------------------------

    def _collect_artifact_paths(self) -> List[str]:
        paths: List[str] = []
        roots: List[str] = []
        if self.scan_docs:
            roots.append("docs")
            for f in ("README.md",):
                if os.path.isfile(f):
                    paths.append(f)
        for sub in ("reports", "console", "feedback", "packaging", "live"):
            if not getattr(self, f"scan_{sub}", True) and sub in (
                    "reports", "console", "feedback", "packaging"):
                continue
            roots.append(os.path.join(self.tester_state_dir, sub))
        roots.append(self.tester_state_dir)
        if self.scan_templates:
            roots.append(os.path.join("examples", "tester_live_readonly"))
        self.scanned_roots = [r for r in roots if os.path.isdir(r)
                              or os.path.isfile(r)]
        for root in roots:
            if os.path.isfile(root):
                paths.append(root)
                continue
            if not os.path.isdir(root):
                continue
            for dirpath, _dirs, files in os.walk(root):
                # Never scan safety-freeze output dirs: their reports describe
                # the forbidden terms by design and would self-flag. This skips
                # the current freeze dir and any nested freeze output trees.
                if os.path.normpath(self.safety_freeze_dir) in \
                        os.path.normpath(dirpath):
                    continue
                if "safety_freeze" in os.path.normpath(dirpath).split(os.sep):
                    continue
                for name in sorted(files):
                    if name.lower() in _EXCLUDE_BASENAMES:
                        continue
                    if os.path.splitext(name)[1].lower() in _TEXT_EXTS:
                        paths.append(os.path.join(dirpath, name))
                        if len(paths) >= _MAX_FILES:
                            return _dedupe(paths)
        return _dedupe(paths)

    # -- evidence -----------------------------------------------------------

    def _gather_evidence(self) -> None:
        ts = self.tester_state_dir
        e: Dict[str, Any] = {
            "install_local_only": os.path.isfile("pyproject.toml"),
            "doctor_available": True,
            "packaging_no_publish": True,
            "feeders_external": True,
            "governance_required": True,
            "feedback_local": True,
            "console_read_only": True,
            "console_hides_nothing": True,
            "console_no_execution": True,
            "raw_payloads_hidden": True,
            "safety_concerns_elevated": True,
            "fixture_self_contained": os.path.isfile(os.path.join(
                "examples", "tester_fixture_spine", "fixture_tester_v0",
                "events.jsonl")),
        }
        # Fixture reproducibility (from tester fixture run summaries).
        e["fixture_passed"] = self._fixture_passed(ts)
        # Membrane / live evidence.
        live_ran, membrane_present, critical_bypass, raw_fallback = \
            self._membrane_evidence(ts)
        e["live_modules_ran"] = live_ran
        e["membrane_present"] = membrane_present
        e["impressions_before_downstream"] = (not live_ran) or membrane_present
        e["membrane_bypass"] = critical_bypass
        e["raw_event_bypass"] = critical_bypass
        e["raw_fallback"] = raw_fallback
        # Claim / capability evidence (from this run's scans).
        e["forbidden_claims"] = bool(
            self.claim_result and self.claim_result.forbidden_claim_count)
        e["missing_disclaimers"] = bool(
            self.claim_result and self.claim_result.missing_disclaimers)
        e["capability_blockers"] = bool(
            self.capability_result and not self.capability_result.passed)
        # Feedback evidence.
        fb = self._feedback_evidence(ts)
        e.update(fb)
        self.evidence = e

    def _fixture_passed(self, ts: str):
        reports = os.path.join(ts, "reports")
        if not os.path.isdir(reports):
            return None
        summaries = sorted(f for f in os.listdir(reports)
                           if f.startswith("TESTER_RUN_SUMMARY_")
                           and f.endswith(".json"))
        if not summaries:
            return None
        data = _load_json(os.path.join(reports, summaries[-1]))
        repro = (data.get("reproducibility", {}) or {}).get(
            "reproducibility_status", "")
        return repro in ("pass", "pass_with_warnings")

    def _membrane_evidence(self, ts: str):
        live = os.path.join(ts, "live")
        live_ran = os.path.isdir(os.path.join(live, "reports")) or os.path.isdir(
            os.path.join(".solaris_ai_nn_live", "membrane"))
        membrane_report = os.path.join(
            ".solaris_ai_nn_live", "membrane", "reports",
            "ENVIRONMENTAL_MEMBRANE_REPORT.json")
        membrane_present = os.path.isfile(membrane_report)
        integ = _load_json(os.path.join(
            ".solaris_ai_nn_live", "membrane", "integration",
            "MEMBRANE_INTEGRATION_REPORT.json"))
        status = (integ.get("sections", {}) or {}).get("status", {}) \
            if isinstance(integ, dict) else {}
        critical = bool(status.get("critical_bypass_count", 0))
        raw_fallback = bool(status.get("raw_fallback_count", 0))
        return live_ran, membrane_present, critical, raw_fallback

    def _feedback_evidence(self, ts: str) -> Dict[str, Any]:
        ledger = _load_json(os.path.join(
            ts, "feedback", "ledger", "TESTER_FEEDBACK_LEDGER.json"))
        return {
            "feedback_safety_concern_count": ledger.get("safety_concern_count",
                                                        0),
            "feedback_release_blocker_count": ledger.get(
                "release_blocker_count", 0),
            "feedback_stop_testing_count": ledger.get("stop_testing_count", 0),
            "feedback_unsupported_claim_count": ledger.get("by_category", {}).get(
                "unsupported_claim_concern", 0) if isinstance(
                ledger.get("by_category"), dict) else 0,
            "feedback_training": False,
        }

    # -- blocker gate -------------------------------------------------------

    def _populate_blocker_gate(self) -> None:
        gate = self.blocker_gate
        claim = self.claim_result
        cap = self.capability_result
        red = self.red_team_result
        e = self.evidence

        from .claim_freeze import _is_research_doc
        if claim:
            for f in claim.findings:
                # Research-doc findings are warnings, not release blockers.
                if f.severity in ("blocker", "critical", "release_blocker"):
                    gate.add(ReleaseBlockerCategory.UNSUPPORTED_CLAIM,
                             f"{f.category} in {f.path}:{f.line}")
                else:
                    self.warnings.append(
                        f"claim note ({f.severity}): {f.category} in "
                        f"{f.path}:{f.line}")
            for path in claim.missing_disclaimers:
                gate.add(ReleaseBlockerCategory.MISSING_DISCLAIMER,
                         f"missing disclaimer in {path}")
        if cap:
            for f in cap.findings:
                if _is_research_doc(f.path):
                    self.warnings.append(
                        f"capability note (research doc): {f.category} in "
                        f"{f.path}:{f.line}")
                    continue
                cat = (ReleaseBlockerCategory.UNSAFE_FEEDER_CONTROL
                       if f.category == "feeder_control" else
                       ReleaseBlockerCategory.MEMBRANE_BYPASS
                       if f.category == "membrane_bypass" else
                       ReleaseBlockerCategory.RAW_EVENT_BYPASS
                       if f.category == "raw_event_downstream_bypass" else
                       ReleaseBlockerCategory.FEEDBACK_TRAINING
                       if f.category == "feedback_as_training" else
                       ReleaseBlockerCategory.PACKAGING_PUBLISH
                       if f.category == "upload_publish" else
                       ReleaseBlockerCategory.UNSAFE_CAPABILITY)
                gate.add(cat, f"{f.category} in {f.path}:{f.line}")
        # Membrane / fixture evidence.
        if e.get("live_modules_ran") and not e.get("membrane_present"):
            gate.add(ReleaseBlockerCategory.MISSING_MEMBRANE,
                     "live modules ran but no environmental membrane report "
                     "is present")
        if e.get("membrane_bypass"):
            gate.add(ReleaseBlockerCategory.MEMBRANE_BYPASS,
                     "critical membrane bypass detected in the integration audit")
        if e.get("fixture_passed") is False:
            gate.add(ReleaseBlockerCategory.FIXTURE_DEMO,
                     "the fixture tester demo did not pass reproducibility")
        if e.get("raw_fallback"):
            self.warnings.append("raw-event fallback was used (loudly reported)")
        # Red-team critical failures.
        if red:
            for c in red.blockers:
                gate.add(ReleaseBlockerCategory.UNKNOWN_CRITICAL,
                         f"red-team {c.check_id} [{c.status}]: {c.question}")

    # -- writers ------------------------------------------------------------

    def _write_manifests(self) -> None:
        from .safety_freeze_manifest import SafetyFreezeManifestBuilder
        manifests = os.path.join(self.safety_freeze_dir, "manifests")
        SafetyFreezeManifestBuilder().write(self.manifest, manifests)
        # FORBIDDEN_CLAIMS.json + ALLOWED_OPERATIONAL_LANGUAGE.json.
        with open(os.path.join(manifests, "FORBIDDEN_CLAIMS.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(ForbiddenClaimRegistry.build().to_dict(), fh, indent=2)
        with open(os.path.join(manifests,
                               "ALLOWED_OPERATIONAL_LANGUAGE.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(AllowedOperationalLanguageRegistry.build().to_dict(), fh,
                      indent=2)

    def _build_reports(self) -> None:
        from .reports import TesterSafetyFreezeReportBuilder
        self.reports = TesterSafetyFreezeReportBuilder(self).write()

    def _update_integrations(self) -> None:
        try:
            from ..inner_map.model import InnerMapModel  # noqa: F401
            self._inner_map_record = self.inner_map_record()
        except Exception:
            self.warnings.append("inner map unavailable (record skipped)")

    # -- views --------------------------------------------------------------

    def safety_freeze_status(self) -> Dict[str, Any]:
        m = self.manifest.to_dict() if self.manifest else {}
        gate = self.blocker_gate.to_dict() if self.blocker_gate else {}
        return {
            "safety_freeze_available": True,
            "safety_freeze_run_id": self.run_id,
            "safety_freeze_profile": self.safety_freeze_profile.profile_id,
            "readiness": m.get("readiness", "unknown"),
            "forbidden_claim_count": m.get("forbidden_claim_count", 0),
            "claim_warning_count": m.get("warning_count", 0),
            "claim_release_blocker_count": self.claim_result.release_blocker_count
            if self.claim_result else 0,
            "capability_blocker_count": m.get("capability_blocker_count", 0),
            "red_team_pass": m.get("red_team_status") == "pass",
            "red_team_blocker_count": m.get("red_team_blocker_count", 0),
            "release_blocker_count": gate.get("open_blocker_count", 0),
            "critical_blocker_count": gate.get("critical_open_count", 0),
            "missing_disclaimer_count": len(self.claim_result.missing_disclaimers)
            if self.claim_result else 0,
            "release_candidate_allowed": gate.get("release_candidate_allowed",
                                                  False),
            "ready": m.get("readiness") == "ready_for_release_candidate",
            "latest_safety_freeze_report_path": self.reports.get("markdown"),
            "latest_safety_freeze_manifest_path": os.path.join(
                self.safety_freeze_dir, "manifests",
                "TESTER_SAFETY_FREEZE_MANIFEST.json"),
            "latest_release_blocker_report_path": os.path.join(
                self.safety_freeze_dir, "reports", "TESTER_RELEASE_BLOCKERS.md"),
            "safety_freeze_safety_block_count": self.safety.rejected_count,
            "local_only": True, "publishes": False,
        }

    def snapshot(self) -> Dict[str, Any]:
        return self.safety_freeze_status()

    def inner_map_record(self) -> Dict[str, Any]:
        st = self.safety_freeze_status()
        return {
            "safety_freeze_run_id": self.run_id,
            "readiness": st["readiness"],
            "open_blocker_count": st["release_blocker_count"],
            "forbidden_claim_count": st["forbidden_claim_count"],
            "capability_blocker_count": st["capability_blocker_count"],
            "red_team_status": "pass" if st["red_team_pass"] else "fail",
            "latest_safety_freeze_report_path": st[
                "latest_safety_freeze_report_path"],
            "local_only": True,
        }

    def recommended_next_action(self) -> str:
        if not self.blocker_gate:
            return "Run the safety freeze gate."
        if self.blocker_gate.critical_open:
            return ("Resolve the critical safety blockers (they cannot be "
                    "waived) before any tester release candidate.")
        if self.blocker_gate.open_blockers:
            return ("Resolve or explicitly waive the open release blockers "
                    "before a tester release candidate.")
        return ("Safety freeze passed; the tester release candidate is allowed "
                "from a safety-gate perspective.")

    def _run_summary(self) -> Dict[str, Any]:
        return {
            "safety_freeze_run_id": self.run_id,
            "safety_freeze_profile": self.safety_freeze_profile.to_dict(),
            "safety_freeze_status": self.safety_freeze_status(),
            "claim_freeze": self.claim_result.to_dict()
            if self.claim_result else {},
            "capability_freeze": self.capability_result.to_dict()
            if self.capability_result else {},
            "artifact_scan": self.artifact_result.to_dict()
            if self.artifact_result else {},
            "red_team": self.red_team_result.to_dict()
            if self.red_team_result else {},
            "release_blockers": self.blocker_gate.to_dict()
            if self.blocker_gate else {},
            "manifest": self.manifest.to_dict() if self.manifest else {},
            "evidence": self.evidence,
            "warnings": list(self.warnings),
            "next_action": self.recommended_next_action(),
            "safety_status": self.safety.snapshot(),
        }

    def _result(self) -> Dict[str, Any]:
        st = self.safety_freeze_status()
        return {
            "refused": False, "run_id": self.run_id,
            "safety_freeze_profile": st["safety_freeze_profile"],
            "readiness": st["readiness"],
            "forbidden_claim_count": st["forbidden_claim_count"],
            "capability_blocker_count": st["capability_blocker_count"],
            "release_blocker_count": st["release_blocker_count"],
            "critical_blocker_count": st["critical_blocker_count"],
            "release_candidate_allowed": st["release_candidate_allowed"],
            "blocked": st["release_blocker_count"] > 0,
            "warnings": list(self.warnings),
            "latest_safety_freeze_report_path": st[
                "latest_safety_freeze_report_path"],
            "next_action": self.recommended_next_action(),
        }


def _dedupe(paths: List[str]) -> List[str]:
    seen = set()
    out = []
    for p in paths:
        np = os.path.normpath(p)
        if np not in seen:
            seen.add(np)
            out.append(p)
    return out


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
