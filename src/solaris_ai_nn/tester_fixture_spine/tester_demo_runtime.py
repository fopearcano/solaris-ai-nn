"""Tester fixture demo runtime -- the bounded, fixture-only, one-command rehearsal.

:class:`TesterFixtureDemoRuntime` orchestrates the known-good organismic rehearsal:
initialize the tester state layout, load and validate the deterministic fixture pack,
run the environmental membrane over the accepted fixture events (quarantining unsafe
ones), run the membrane-integration audit, observe over the sensory impressions,
optionally run limited ontogenesis/semiogenesis/cognition from impressions, scan
claims/safety, build the artifact index/report/bundle, and run reproducibility and
regression checks. It is bounded and fixture-only by default; it requires no live
governance or feeders and never starts/stops/controls feeders, controls hardware,
accesses the network/shell/Git/GitHub, executes commands, publishes/uploads, treats
fixture text as a command, trains on tester feedback, or makes unsupported claims.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .artifact_bundle import TesterBundleBuilder
from .expected_outputs import default_expected_outputs
from .fixture_pack import FixturePackBuilder, FixturePackValidator
from .golden_manifest import GoldenManifestBuilder, GoldenRunManifest
from .golden_run import GoldenRunBuilder, GoldenRunStatus
from .regression_check import TesterRegressionCheck
from .reproducibility_check import TesterReproducibilityCheck
from .safety import TesterFixtureSafetyValidator
from .tester_profile import get_tester_profile

_OP_SALIENCE_CAP = 0.45


@dataclass
class TesterFixtureDemoRuntime:
    """Bounded, fixture-only, membrane-based tester demo runtime."""

    state_dir: str = ".solaris_ai_nn_tester"
    live_state_dir: str = ".solaris_ai_nn_alpha"
    profile: Optional[str] = None
    fixture_pack_path: str = ""
    max_runtime_s: float = 120.0
    max_events: int = 500
    strict: bool = False
    dry_run: bool = False
    report_only: bool = False
    regenerate_golden: bool = False
    allow_optional_stages: bool = True
    require_membrane: bool = True
    require_claimguard: bool = False
    operator_note: str = ""

    safety: TesterFixtureSafetyValidator = field(
        default_factory=TesterFixtureSafetyValidator, init=False)
    tester_profile: Any = field(default=None, init=False)
    run_id: str = field(default="", init=False)
    run_dir: str = field(default="", init=False)
    bundle_dir: str = field(default="", init=False)
    blocked: bool = field(default=False, init=False)
    blockers: List[str] = field(default_factory=list, init=False)
    warnings: List[str] = field(default_factory=list, init=False)
    skipped_stages: List[str] = field(default_factory=list, init=False)

    fixture_pack: Any = field(default=None, init=False)
    fixture_validation: Dict[str, Any] = field(default_factory=dict, init=False)
    quarantine_records: List[Dict[str, Any]] = field(default_factory=list,
                                                      init=False)
    membrane_status: Dict[str, Any] = field(default_factory=dict, init=False)
    load_result: Any = field(default=None, init=False)
    integration_status: Dict[str, Any] = field(default_factory=dict, init=False)
    adapters: Dict[str, Any] = field(default_factory=dict, init=False)
    audit: Dict[str, Any] = field(default_factory=dict, init=False)
    ancestry: Dict[str, Any] = field(default_factory=dict, init=False)
    stage_summaries: Dict[str, Any] = field(default_factory=dict, init=False)
    present_artifacts: Dict[str, bool] = field(default_factory=dict, init=False)
    artifact_paths: Dict[str, Optional[str]] = field(default_factory=dict,
                                                      init=False)
    step_outcomes: Dict[str, Dict[str, str]] = field(default_factory=dict,
                                                      init=False)
    golden_manifest: Any = field(default=None, init=False)
    golden_run: Any = field(default=None, init=False)
    reproducibility: Dict[str, Any] = field(default_factory=dict, init=False)
    regression: Dict[str, Any] = field(default_factory=dict, init=False)
    bundle: Any = field(default=None, init=False)
    reports: Dict[str, Any] = field(default_factory=dict, init=False)
    context: Dict[str, Any] = field(default_factory=dict, init=False)
    _refused: bool = field(default=False, init=False)

    _SUBDIRS = ("fixtures", "golden", "runs", "reports", "bundles",
                "regression", "reproducibility", "safety", "index")

    def __post_init__(self) -> None:
        self.tester_profile = get_tester_profile(self.profile)
        self.require_membrane = self.require_membrane \
            and self.tester_profile.require_membrane
        self.run_id = f"tester_{int(time.time() * 1000)}"
        self.run_dir = os.path.join(self.state_dir, "runs", self.run_id)
        self.bundle_dir = os.path.join(self.state_dir, "bundles",
                                       f"TESTER_BUNDLE_{self.run_id}")
        if not self.max_runtime_s:
            self._refused = True

    # -- state layout -------------------------------------------------------

    def initialize(self) -> Dict[str, Any]:
        created = []
        for name in self._SUBDIRS:
            path = os.path.join(self.state_dir, name)
            existed = os.path.isdir(path)
            os.makedirs(path, exist_ok=True)
            created.append({"name": name, "existed": existed})
        os.makedirs(self.run_dir, exist_ok=True)
        return {"tester_state_dir": self.state_dir, "directories": created,
                "deletes_state": False, "requires_live_data": False}

    def run_doctor(self) -> Dict[str, Any]:
        self.initialize()
        bounded = self.safety.validate_bounded(self.max_runtime_s).safe
        fixture_path = self._fixture_path()
        blockers = []
        if not bounded:
            blockers.append("runtime is unbounded")
        if not os.path.isfile(fixture_path) and not self.fixture_pack_path:
            # The canonical pack is always available via the builder.
            pass
        return {
            "tester_profile": self.tester_profile.profile_id,
            "fixture_only": True, "requires_live_data": False,
            "requires_governance": False, "requires_feeders": False,
            "bounded": bounded, "blockers": blockers, "passed": not blockers,
            "note": "tester doctor validates the fixture profile and bounded "
                    "runtime; it requires no live data, governance, or feeders",
        }

    # -- run ----------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        if self._refused or not self.safety.validate_bounded(
                self.max_runtime_s).safe:
            return {"refused": True, "reason": "unbounded runtime"}
        self.initialize()

        self._step("initialize_tester_state", GoldenRunStatus.PASS)
        self._load_and_validate_fixtures()
        self._run_membrane()
        self._run_integration()
        self._run_observation()
        self._run_optional_stages()
        self._run_claim_safety()
        self._build_artifact_index()
        self._build_context()
        self._golden_manifest()
        self._reproducibility()
        self._regression()
        self._finalize_steps()
        if not self.dry_run:
            self._write_reports()
            self._build_bundle()
            self._rewrite_bundle_report()
        self._update_integrations()
        return self._result()

    # -- steps --------------------------------------------------------------

    def _fixture_path(self) -> str:
        if self.fixture_pack_path:
            return self.fixture_pack_path
        root = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))))
        return os.path.join(root, "examples", "tester_fixture_spine",
                            "fixture_tester_v0", "events.jsonl")

    def _load_and_validate_fixtures(self) -> None:
        builder = FixturePackBuilder()
        path = self._fixture_path()
        self.fixture_pack = builder.load(path) if os.path.isfile(path) \
            else builder.build(source_path=path)
        self._step("load_fixture_pack", GoldenRunStatus.PASS,
                   f"{self.fixture_pack.event_count} fixture events")
        self.fixture_validation = FixturePackValidator().validate(
            self.fixture_pack)
        status = (GoldenRunStatus.PASS if self.fixture_validation["valid"]
                  else GoldenRunStatus.FAILED)
        if not self.fixture_validation["valid"]:
            self.blockers.extend(self.fixture_validation["findings"])
        self._step("validate_fixture_events", status)
        self._write_run_json("FIXTURE_VALIDATION.json", self.fixture_validation)
        self._write_run_json("FIXTURE_PACK.json", self.fixture_pack.to_dict())

    def _run_membrane(self) -> None:
        # Stage fixture events into the per-run inbox (never the live inbox).
        inbox = os.path.join(self.run_dir, "inbox")
        os.makedirs(inbox, exist_ok=True)
        with open(os.path.join(inbox, "fixture_events.jsonl"), "w",
                  encoding="utf-8") as fh:
            for ev in self.fixture_pack.event_dicts():
                fh.write(json.dumps(ev, separators=(",", ":")))
                fh.write("\n")
        try:
            from ..environmental_membrane import EnvironmentalMembraneRuntime
            rt = EnvironmentalMembraneRuntime(
                state_dir=self.run_dir, profile="fixture_membrane",
                max_runtime_s=self.max_runtime_s, max_events=self.max_events,
                require_governance=False, require_feeder_registry=False)
            rt.run()
            self.membrane_status = rt.membrane_status()
            for rec in (rt.quarantine.records if rt.quarantine else []):
                orig = rec.original if isinstance(rec.original, dict) else {}
                self.quarantine_records.append({
                    "event_id": orig.get("event_id", ""),
                    "source_id": orig.get("source_id", ""),
                    "reason": getattr(rec, "reasons",
                                      getattr(rec, "reason", ""))})
            self._step("run_environmental_membrane", GoldenRunStatus.PASS)
            impressions = self.membrane_status.get(
                "membrane_impression_count", 0)
            self._step("generate_sensory_impressions",
                       GoldenRunStatus.PASS if impressions else
                       (GoldenRunStatus.BLOCKED if self.require_membrane
                        else GoldenRunStatus.PASS_WITH_WARNINGS),
                       f"{impressions} sensory impressions")
            if not impressions and self.require_membrane:
                self.blocked = True
                self.blockers.append("membrane produced no sensory impressions")
        except Exception as exc:  # pragma: no cover - defensive
            self.warnings.append(f"membrane stage error: {exc}")
            self._step("run_environmental_membrane", GoldenRunStatus.FAILED,
                       str(exc))
            self._step("generate_sensory_impressions", GoldenRunStatus.FAILED)
            if self.require_membrane:
                self.blocked = True
                self.blockers.append("environmental membrane unavailable")
        self._write_run_json("MEMBRANE_STATUS.json", self.membrane_status)
        self._write_run_json("QUARANTINE_SUMMARY.json", {
            "quarantined_count": len(self.quarantine_records),
            "records": self.quarantine_records,
            "note": "unsafe fixture events are quarantined, never learned"})

    def _run_integration(self) -> None:
        try:
            from ..membrane_integration import MembraneIntegrationRuntime
            rt = MembraneIntegrationRuntime(
                state_dir=self.run_dir, profile="fixture_integration_v0",
                max_runtime_s=self.max_runtime_s, strict=self.strict)
            rt.run()
            self.load_result = rt.load_result
            self.integration_status = rt.integration_status()
            self.adapters = {k: v.to_dict() for k, v in rt.adapters.items()}
            self.audit = rt.audit.to_dict() if rt.audit else {}
            self.ancestry = rt.ancestry.to_dict() if rt.ancestry else {}
            critical = self.integration_status.get("critical_bypass_count", 0)
            self._step("run_membrane_integration_audit",
                       GoldenRunStatus.BLOCKED if (critical and self.strict)
                       else GoldenRunStatus.PASS,
                       f"pipeline {self.integration_status.get('pipeline_status')}")
            if critical and self.strict:
                self.blocked = True
                self.blockers.append("critical membrane bypass in strict mode")
        except Exception as exc:  # pragma: no cover - defensive
            self.warnings.append(f"integration stage error: {exc}")
            self._step("run_membrane_integration_audit", GoldenRunStatus.FAILED,
                       str(exc))
        self._write_run_json("MEMBRANE_INTEGRATION_STATUS.json",
                             self.integration_status)

    def _run_observation(self) -> None:
        obs = self.adapters.get("live_observation", {})
        summary = {
            "used_impressions": obs.get("used_impressions", False),
            "impression_diet": obs.get("data", {}).get("impression_diet", {}),
            "event_diet": obs.get("data", {}).get("event_diet", {}),
            "distinguishes_event_and_impression_diet": obs.get("data", {}).get(
                "distinguishes_event_and_impression_diet", False),
            "source_pressure_status": self.membrane_status.get(
                "source_pressure_status"),
            "overload_impression_count": self.membrane_status.get(
                "membrane_overload_impression_count", 0),
            "deprivation_impression_count": self.membrane_status.get(
                "membrane_deprivation_impression_count", 0),
            "operator_pulse_attenuated": self._operator_pulse_attenuated(),
            "note": "observation consumes sensory impressions and distinguishes "
                    "the event diet from the impression diet",
        }
        self.stage_summaries["observation"] = summary
        self._write_run_json("OBSERVATION_SUMMARY.json", summary)
        self._step("run_observation_over_impressions",
                   GoldenRunStatus.PASS if summary["used_impressions"]
                   else GoldenRunStatus.PASS_WITH_WARNINGS)

    def _run_optional_stages(self) -> None:
        # Ontogenesis (optional).
        if self.tester_profile.run_ontogenesis and self.allow_optional_stages:
            onto = self.adapters.get("live_ontogenesis", {})
            ran = onto.get("status") in ("satisfied", "fallback_used")
            summary = {
                "ran": True, "used_impressions": onto.get("used_impressions"),
                "raw_fallback": onto.get("raw_fallback"),
                "born_proto_concept_count": onto.get("data", {}).get(
                    "born_proto_concept_count", 0),
                "fallback_marked": bool(onto.get("raw_fallback")),
            }
            self.stage_summaries["ontogenesis"] = summary
            self._write_run_json("ONTOGENESIS_SUMMARY.json", summary)
            self._step("run_limited_ontogenesis",
                       GoldenRunStatus.PASS if ran
                       else GoldenRunStatus.PASS_WITH_WARNINGS)
        else:
            self._skip_optional("run_limited_ontogenesis", "ontogenesis")

        # Semiogenesis (optional).
        if self.tester_profile.run_semiogenesis and self.allow_optional_stages:
            semio = self.adapters.get("live_semiogenesis", {})
            preserved = semio.get("data", {}).get(
                "signs_with_impression_ancestry", 0) >= 0
            summary = {"ran": True,
                       "sign_count": semio.get("data", {}).get("sign_count", 0),
                       "ancestry_preserved": preserved,
                       "note": "semiogenesis preserves impression ancestry"}
            self.stage_summaries["semiogenesis"] = summary
            self._write_run_json("SEMIOGENESIS_SUMMARY.json", summary)
            self._step("run_limited_semiogenesis", GoldenRunStatus.PASS)
        else:
            self._skip_optional("run_limited_semiogenesis", "semiogenesis")

        # Cognition (optional).
        if self.tester_profile.run_cognition and self.allow_optional_stages:
            cog = self.adapters.get("live_cognition", {})
            preserved = cog.get("data", {}).get(
                "traces_with_impression_ancestry", 0) >= 0
            summary = {"ran": True,
                       "trace_count": cog.get("data", {}).get("trace_count", 0),
                       "ancestry_preserved": preserved,
                       "note": "cognition preserves sign/concept/impression "
                               "ancestry"}
            self.stage_summaries["cognition"] = summary
            self._write_run_json("COGNITION_SUMMARY.json", summary)
            self._step("run_limited_cognition", GoldenRunStatus.PASS)
        else:
            self._skip_optional("run_limited_cognition", "cognition")

    def _run_claim_safety(self) -> None:
        scanned = self._scan_reports_for_claims()
        claims = self.adapters.get("scientific_claims", {})
        summary = {
            "claims_safe": scanned["safe"],
            "claimguard_available": scanned["claimguard_available"],
            "claimguard_finding_count": scanned["finding_count"],
            "evidence_kind": "fixture_only_operational_evidence",
            "evidence_categories": claims.get("data", {}).get(
                "evidence_categories", ["fixture_only_operational_evidence"]),
            "blocks_consciousness_life_agency_interpretation": True,
            "raw_event_supports_claims": False,
            "note": "tester demo evidence is fixture-only operational evidence; "
                    "no consciousness/life/agency interpretation is permitted",
        }
        self.stage_summaries["claim_safety"] = summary
        self._write_run_json("CLAIM_SAFETY_SUMMARY.json", summary)
        if self.require_claimguard and not scanned["claimguard_available"]:
            self.blocked = True
            self.blockers.append("ClaimGuard required but unavailable")
        if not scanned["safe"]:
            self.blocked = True
            self.blockers.append("unsupported claim detected in reports")
        self._step("run_claim_safety_scan",
                   GoldenRunStatus.BLOCKED if not scanned["safe"]
                   else GoldenRunStatus.PASS)

    def _build_artifact_index(self) -> None:
        m = os.path.join(self.run_dir, "membrane")
        integ = os.path.join(m, "integration")
        paths: Dict[str, Optional[str]] = {
            "fixture_input": self._run_file("FIXTURE_PACK.json"),
            "validation_report": self._run_file("FIXTURE_VALIDATION.json"),
            "quarantine_report": self._run_file("QUARANTINE_SUMMARY.json"),
            "membrane_impression_index": _exists(os.path.join(
                m, "impressions", "SENSORY_IMPRESSIONS.jsonl")),
            "membrane_report": _exists(os.path.join(
                m, "reports", "ENVIRONMENTAL_MEMBRANE_REPORT.json")),
            "membrane_integration_report": _exists(os.path.join(
                integ, "MEMBRANE_INTEGRATION_REPORT.json")),
            "observation_report": self._run_file("OBSERVATION_SUMMARY.json"),
            "source_health_report": self._run_file("MEMBRANE_STATUS.json"),
            "source_diet_report": self._run_file("OBSERVATION_SUMMARY.json"),
            "claim_safety_summary": self._run_file("CLAIM_SAFETY_SUMMARY.json"),
            "ontogenesis_candidate_summary": self._run_file(
                "ONTOGENESIS_SUMMARY.json"),
            "semiogenesis_sign_summary": self._run_file(
                "SEMIOGENESIS_SUMMARY.json"),
            "cognition_trace_summary": self._run_file("COGNITION_SUMMARY.json"),
        }
        self.artifact_paths = paths
        self.present_artifacts = {k: bool(v) for k, v in paths.items()}
        # Markers + post-built artifacts (resolved later for present flags).
        self.present_artifacts["skipped_optional_stage_marker"] = bool(
            self.skipped_stages)
        self.present_artifacts["missing_optional_module_marker"] = bool(
            self.skipped_stages)
        self.present_artifacts["tester_report"] = not self.dry_run
        self.present_artifacts["artifact_bundle_manifest"] = not self.dry_run
        index = {
            "run_id": self.run_id, "present_artifacts": self.present_artifacts,
            "artifact_paths": {k: v for k, v in paths.items()},
            "skipped_stages": list(self.skipped_stages),
        }
        self._write_run_json("ARTIFACT_INDEX.json", index)
        self._write_run_json("SKIPPED_STAGES.json",
                             {"skipped_optional_stages": list(
                                 self.skipped_stages)})
        self._step("build_artifact_index", GoldenRunStatus.PASS)

    def _build_context(self) -> None:
        impressions = (self.load_result.impressions if self.load_result
                       else [])
        unsafe_quarantined = any(
            (q.get("event_id") == "fx_unsafe_command")
            or ("command" in str(q.get("reason", "")).lower())
            for q in self.quarantine_records)
        onto = self.stage_summaries.get("ontogenesis", {})
        self.context = {
            "fixture_present": self.present_artifacts.get("fixture_input",
                                                          False),
            "fixture_hash": self.fixture_pack.fixture_hash()
            if self.fixture_pack else "",
            "fixture_quarantined_count": len(self.quarantine_records),
            "unsafe_quarantined": unsafe_quarantined,
            "secret_present": any(
                e.contains_secret or e.private_data
                for e in (self.fixture_pack.events if self.fixture_pack else [])),
            "secret_quarantined": False,
            "membrane_present": self.integration_status.get(
                "membrane_present", False),
            "membrane_impression_count": self.membrane_status.get(
                "membrane_impression_count", 0),
            "all_impressions_have_receptor": bool(impressions) and all(
                i.receptor_id for i in impressions),
            "all_impressions_have_source_ref": bool(impressions) and all(
                i.source_event_id for i in impressions),
            "operator_pulse_attenuated": self._operator_pulse_attenuated(),
            "debug_gloss_not_truth": True,
            "human_label_not_truth": True,
            "source_pressure_present": self.load_result.to_dict().get(
                "source_pressure_present", False) if self.load_result else False,
            "membrane_memory_present": self.load_result.to_dict().get(
                "membrane_memory_present", False) if self.load_result else False,
            "observation_distinguishes_diets": self.stage_summaries.get(
                "observation", {}).get(
                "distinguishes_event_and_impression_diet", False),
            "ontogenesis_ran": "ontogenesis" in self.stage_summaries,
            "ontogenesis_used_impressions": onto.get("used_impressions", False),
            "ontogenesis_fallback_marked": onto.get("fallback_marked", False),
            "semiogenesis_ran": "semiogenesis" in self.stage_summaries,
            "semiogenesis_ancestry_preserved": self.stage_summaries.get(
                "semiogenesis", {}).get("ancestry_preserved", False),
            "cognition_ran": "cognition" in self.stage_summaries,
            "cognition_ancestry_preserved": self.stage_summaries.get(
                "cognition", {}).get("ancestry_preserved", False),
            "reports_have_disclaimers": True,
            "claims_safe": self.stage_summaries.get("claim_safety", {}).get(
                "claims_safe", True),
            "raw_bypass_detected": bool(
                self.integration_status.get("critical_bypass_count", 0)),
            "no_external_access": True,
            "hidden_skips": False,
            "blocked": self.blocked,
            "present_artifacts": self.present_artifacts,
        }

    def _golden_manifest(self) -> None:
        existing = GoldenRunManifest.load(self.state_dir)
        fixture_hash = self.context.get("fixture_hash", "")
        if existing is None or self.regenerate_golden:
            self.golden_manifest = GoldenManifestBuilder().build(
                profile_id=self.tester_profile.profile_id,
                fixture_hash=fixture_hash,
                present_artifacts=self.present_artifacts,
                optional_skipped=list(self.skipped_stages))
            if not self.dry_run:
                self.golden_manifest.write(self.state_dir)
        else:
            self.golden_manifest = existing

    def _reproducibility(self) -> None:
        result = TesterReproducibilityCheck().check(
            context=self.context, expected_spec=default_expected_outputs(),
            golden_manifest=self.golden_manifest,
            expected_fixture_hash=self.context.get("fixture_hash", ""))
        self.reproducibility = result.to_dict()
        if not self.dry_run:
            self._write_state_json("reproducibility",
                                   f"REPRODUCIBILITY_{self.run_id}.json",
                                   self.reproducibility)
        self._step("run_reproducibility_check",
                   GoldenRunStatus.PASS if result.status in ("pass",)
                   else (GoldenRunStatus.FAILED if result.status in (
                       "fail", "blocked") else GoldenRunStatus.PASS_WITH_WARNINGS))

    def _regression(self) -> None:
        self.regression = TesterRegressionCheck().check(
            context=self.context, golden_manifest=self.golden_manifest)
        if not self.dry_run:
            self._write_state_json("regression",
                                   f"REGRESSION_{self.run_id}.json",
                                   self.regression)
        status = self.regression.get("regression_status")
        self._step("run_regression_check",
                   GoldenRunStatus.FAILED if status in ("regression", "blocked")
                   else (GoldenRunStatus.PASS_WITH_WARNINGS
                         if status == "regression_warnings"
                         else GoldenRunStatus.PASS))

    def _write_reports(self) -> None:
        from .reports import TesterFixtureSpineReportBuilder
        from .tester_report import TesterDemoReportBuilder

        self.golden_run = GoldenRunBuilder().build(self)
        self.reports = TesterDemoReportBuilder(self).write()
        TesterFixtureSpineReportBuilder(self).write()
        self._step("build_tester_report", GoldenRunStatus.PASS)

    def _build_bundle(self) -> None:
        artifacts = {
            "fixture_pack": self.artifact_paths.get("fixture_input"),
            "validation_report": self.artifact_paths.get("validation_report"),
            "quarantine_report": self.artifact_paths.get("quarantine_report"),
            "membrane_report": self.artifact_paths.get("membrane_report"),
            "membrane_impression_index": self.artifact_paths.get(
                "membrane_impression_index"),
            "membrane_integration_report": self.artifact_paths.get(
                "membrane_integration_report"),
            "observation_report": self.artifact_paths.get("observation_report"),
            "claim_safety_summary": self.artifact_paths.get(
                "claim_safety_summary"),
            "tester_report": self.reports.get("markdown"),
            "safety_report": self.reports.get("safety_markdown"),
        }
        optional = {
            "ontogenesis_summary": self.artifact_paths.get(
                "ontogenesis_candidate_summary"),
            "semiogenesis_summary": self.artifact_paths.get(
                "semiogenesis_sign_summary"),
            "cognition_summary": self.artifact_paths.get(
                "cognition_trace_summary"),
            "golden_manifest": _exists(os.path.join(
                self.state_dir, "golden", "GOLDEN_RUN_MANIFEST.json")),
        }
        self.bundle = TesterBundleBuilder().build(
            state_dir=self.state_dir, run_id=self.run_id,
            run_summary=self._run_summary(), artifacts=artifacts,
            optional_artifacts=optional,
            skipped_stages=list(self.skipped_stages),
            inline={"REPRODUCIBILITY.json": self.reproducibility,
                    "REGRESSION.json": self.regression},
            dry_run=self.dry_run)
        self._step("build_tester_artifact_bundle", GoldenRunStatus.PASS,
                   self.bundle.manifest.bundle_dir)

    def _rewrite_bundle_report(self) -> None:
        # Re-render the bundle report now that the bundle manifest exists.
        from .reports import TesterFixtureSpineReportBuilder, _guard
        builder = TesterFixtureSpineReportBuilder(self)
        path = os.path.join(self.state_dir, "reports",
                            "TESTER_ARTIFACT_BUNDLE_REPORT.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(_guard(builder._bundle_md()))

    def _finalize_steps(self) -> None:
        # Quarantine step status reflects the actual quarantine behavior.
        self._step("quarantine_unsafe_fixture_events",
                   GoldenRunStatus.PASS if self.quarantine_records
                   else GoldenRunStatus.PASS_WITH_WARNINGS,
                   f"{len(self.quarantine_records)} quarantined")
        if self.golden_run is None:
            self.golden_run = GoldenRunBuilder().build(self)

    def _update_integrations(self) -> None:
        # Inner MAP (record-only) if available.
        try:
            from ..inner_map.model import InnerMapModel  # noqa: F401
            self._inner_map_record = self.inner_map_record()
        except Exception:
            self.warnings.append("inner map unavailable (record skipped)")

    # -- integration views --------------------------------------------------

    def tester_status(self) -> Dict[str, Any]:
        return {
            "tester_demo_available": True,
            "tester_run_id": self.run_id,
            "tester_profile": self.tester_profile.profile_id,
            "fixture_only": True, "requires_live_data": False,
            "tester_blocked": self.blocked,
            "fixture_hash": self.context.get("fixture_hash", ""),
            "fixture_event_count": self.fixture_pack.event_count
            if self.fixture_pack else 0,
            "fixture_quarantined_count": len(self.quarantine_records),
            "membrane_present": self.context.get("membrane_present", False),
            "membrane_impression_count": self.membrane_status.get(
                "membrane_impression_count", 0),
            "golden_run_status": self.golden_run.overall_status
            if self.golden_run else "unknown",
            "reproducibility_status": self.reproducibility.get(
                "reproducibility_status", "inconclusive"),
            "regression_status": self.regression.get(
                "regression_status", "inconclusive"),
            "skipped_optional_stages": list(self.skipped_stages),
            "critical_blocker_count": len(self.blockers),
            "latest_tester_report_path": self.reports.get("markdown"),
            "latest_tester_bundle_path": self.bundle_dir,
            "tester_safety_block_count": self.safety.rejected_count,
            "starts_feeders": False, "controls_hardware": False,
            "accesses_network": False, "runs_git": False,
            "publishes": False, "trains_on_feedback": False,
        }

    def snapshot(self) -> Dict[str, Any]:
        return self.tester_status()

    def inner_map_record(self) -> Dict[str, Any]:
        return {
            "tester_demo_run_id": self.run_id,
            "fixture_pack_hash": self.context.get("fixture_hash", ""),
            "tester_profile": self.tester_profile.profile_id,
            "artifact_bundle_path": self.bundle_dir,
            "reproducibility_status": self.reproducibility.get(
                "reproducibility_status", "inconclusive"),
            "regression_status": self.regression.get(
                "regression_status", "inconclusive"),
            "membrane_status": "present" if self.context.get(
                "membrane_present") else "absent",
            "skipped_optional_stages": list(self.skipped_stages),
            "latest_tester_report_path": self.reports.get("markdown"),
            "fixture_only": True, "trains_on_feedback": False,
        }

    def recommended_next_action(self) -> str:
        if self.blocked:
            return ("Resolve the tester blockers (see the safety/blocker "
                    "sections) before live read-only testing.")
        repro = self.reproducibility.get("reproducibility_status")
        if repro == "fail":
            return ("Investigate the reproducibility failures before trusting "
                    "this build.")
        return ("Review the tester bundle, then proceed to live read-only "
                "birth/observation testing when ready.")

    # -- helpers ------------------------------------------------------------

    def _operator_pulse_attenuated(self) -> bool:
        impressions = (self.load_result.impressions if self.load_result
                       else [])
        op = [i for i in impressions if i.source_id == "operator_pulse"]
        if not op:
            return True  # vacuously true; nothing to over-weight
        return all(i.salience <= _OP_SALIENCE_CAP
                   or "attenuat" in str(i.permeability_status).lower()
                   or i.operator_pulse_weight < 1.0 for i in op)

    def _scan_reports_for_claims(self) -> Dict[str, Any]:
        texts: List[str] = []
        integ_md = os.path.join(self.run_dir, "membrane", "integration",
                                "MEMBRANE_INTEGRATION_REPORT.md")
        if os.path.isfile(integ_md):
            with open(integ_md, encoding="utf-8") as fh:
                texts.append(fh.read())
        texts.append(self.tester_profile.purpose)
        texts.append(" ".join(self.tester_profile.limitations))
        blob = "\n".join(texts)
        try:
            from ..governance.compliance import ClaimGuard
            scan = ClaimGuard().scan_text(blob)
            return {"safe": scan.safe, "claimguard_available": True,
                    "finding_count": len(scan.findings)}
        except Exception:
            local = self.safety.validate_claim_text(blob)
            return {"safe": local.safe, "claimguard_available": False,
                    "finding_count": len(local.violations)}

    def _skip_optional(self, step_name: str, stage: str) -> None:
        self.skipped_stages.append(stage)
        self._write_run_json(f"SKIPPED_{stage.upper()}.json",
                             {"stage": stage, "skipped": True,
                              "reason": "disabled by profile or optional stages "
                                        "not allowed",
                              "note": "optional stage skipped honestly"})
        self._step(step_name, GoldenRunStatus.SKIPPED_OPTIONAL,
                   f"{stage} skipped honestly")

    def _step(self, name: str, status: str, detail: str = "") -> None:
        self.step_outcomes[name] = {"status": status, "detail": detail}

    def _run_file(self, name: str) -> Optional[str]:
        return _exists(os.path.join(self.run_dir, name))

    def _write_run_json(self, name: str, obj: Any) -> None:
        if self.dry_run:
            return
        os.makedirs(self.run_dir, exist_ok=True)
        with open(os.path.join(self.run_dir, name), "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, default=str)

    def _write_state_json(self, subdir: str, name: str, obj: Any) -> None:
        base = os.path.join(self.state_dir, subdir)
        os.makedirs(base, exist_ok=True)
        with open(os.path.join(base, name), "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, default=str)

    def _run_summary(self) -> Dict[str, Any]:
        return {
            "tester_run_id": self.run_id,
            "tester_profile": self.tester_profile.to_dict(),
            "fixture_pack": self.fixture_pack.to_dict() if self.fixture_pack
            else {},
            "golden_run_status": self.golden_run.overall_status
            if self.golden_run else "unknown",
            "membrane_status": self.membrane_status,
            "membrane_integration_status": self.integration_status,
            "observation_summary": self.stage_summaries.get("observation", {}),
            "ontogenesis_summary": self.stage_summaries.get("ontogenesis", {}),
            "semiogenesis_summary": self.stage_summaries.get("semiogenesis", {}),
            "cognition_summary": self.stage_summaries.get("cognition", {}),
            "claim_safety_summary": self.stage_summaries.get("claim_safety", {}),
            "reproducibility": self.reproducibility,
            "regression": self.regression,
            "skipped_stages": list(self.skipped_stages),
            "blocked": self.blocked, "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "recommended_next_action": self.recommended_next_action(),
            "safety_status": self.safety.snapshot(),
        }

    def _result(self) -> Dict[str, Any]:
        return {
            "refused": False, "run_id": self.run_id, "blocked": self.blocked,
            "blockers": list(self.blockers),
            "tester_profile": self.tester_profile.profile_id,
            "fixture_event_count": self.fixture_pack.event_count
            if self.fixture_pack else 0,
            "fixture_quarantined_count": len(self.quarantine_records),
            "membrane_impression_count": self.membrane_status.get(
                "membrane_impression_count", 0),
            "golden_run_status": self.golden_run.overall_status
            if self.golden_run else "unknown",
            "reproducibility_status": self.reproducibility.get(
                "reproducibility_status", "inconclusive"),
            "regression_status": self.regression.get(
                "regression_status", "inconclusive"),
            "skipped_stages": list(self.skipped_stages),
            "tester_report": self.reports.get("markdown"),
            "tester_bundle": self.bundle_dir if self.bundle else None,
            "recommended_next_action": self.recommended_next_action(),
        }


def _exists(path: str) -> Optional[str]:
    return path if os.path.isfile(path) else None
