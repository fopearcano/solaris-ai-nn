"""Membrane integration runtime -- bounded, read-only pipeline audit/enforcement.

:class:`MembraneIntegrationRuntime` loads the membrane and downstream artifacts,
runs the impression loader, validates ancestry chains, evaluates downstream
contracts, detects bypasses, runs the module adapters where safe, runs the pipeline
audit, and writes the integration report set. It is an architectural audit/
enforcement layer: bounded, local-only, and it controls no feeders, calls no
network/Git/GitHub/shell, executes no commands, modifies no source/governance, and
makes no consciousness/life/agency claim.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .ancestry import MembraneAncestryBuilder
from .bypass_detector import MembraneBypassDetector
from .downstream_contracts import evaluate_contracts, summary as contract_summary
from .impression_loader import SensoryImpressionLoader
from .integration_profile import get_integration_profile
from .module_adapters import (
    AlphaSystemMembraneAdapter,
    LiveBirthMembraneAdapter,
    LiveCognitionMembraneAdapter,
    LiveObservationMembraneAdapter,
    LiveOntogenesisMembraneAdapter,
    LiveSemiogenesisMembraneAdapter,
    ResearchCycleMembraneAdapter,
    ScientificClaimsMembraneAdapter,
)
from .pipeline_audit import MembranePipelineAudit
from .safety import MembraneIntegrationSafetyValidator


@dataclass
class MembraneIntegrationRuntime:
    """Bounded, local, read-only membrane integration runtime."""

    state_dir: str = ".solaris_ai_nn_live"
    alpha_state_dir: str = ".solaris_ai_nn_alpha"
    profile: Optional[str] = None
    max_runtime_s: float = 120.0
    report_only: bool = False
    dry_run: bool = False
    strict: bool = False
    require_membrane: bool = False
    require_impressions: bool = False
    require_ancestry: bool = False
    allow_raw_fallback: bool = True
    require_claimguard: bool = False
    operator_note: str = ""

    safety: MembraneIntegrationSafetyValidator = field(
        default_factory=MembraneIntegrationSafetyValidator, init=False)
    integration_profile: Any = field(default=None, init=False)
    run_id: str = field(default="", init=False)
    blocked: bool = field(default=False, init=False)
    blockers: List[str] = field(default_factory=list, init=False)
    warnings: List[str] = field(default_factory=list, init=False)

    load_result: Any = field(default=None, init=False)
    ancestry: Any = field(default=None, init=False)
    contracts: List[Any] = field(default_factory=list, init=False)
    bypass_findings: List[Any] = field(default_factory=list, init=False)
    adapters: Dict[str, Any] = field(default_factory=dict, init=False)
    audit: Any = field(default=None, init=False)
    reports: Dict[str, Any] = field(default_factory=dict, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.state_dir == self.alpha_state_dir:
            self.state_dir = ".solaris_ai_nn_live"
        self.integration_profile = get_integration_profile(self.profile)
        self.strict = self.strict or self.integration_profile.strict_enforced
        self.run_id = f"integ_{int(time.time())}"
        if not self.max_runtime_s:
            self._refused = True

    def run(self) -> Dict[str, Any]:
        if self._refused or not self.safety.validate_bounded(
                self.max_runtime_s).safe:
            return {"refused": True, "reason": "unbounded runtime"}
        os.makedirs(os.path.join(self.state_dir, "membrane", "integration"),
                    exist_ok=True)

        require_membrane = self.require_membrane \
            or self.integration_profile.require_membrane
        require_impressions = self.require_impressions \
            or self.integration_profile.require_impressions

        self.load_result = SensoryImpressionLoader().load(
            self.state_dir, require_membrane=require_membrane,
            require_impressions=require_impressions)
        self.blockers.extend(self.load_result.blockers)
        self.warnings.extend(self.load_result.warnings)

        # Build ancestry from downstream memories + loaded impressions.
        concept_records = self._concept_records()
        sign_records = self._sign_records()
        cognition_records = self._cognition_records()
        sp_status = self._source_pressure_status()
        self.ancestry = MembraneAncestryBuilder().build(
            impressions=self.load_result.impressions,
            concept_records=concept_records, sign_records=sign_records,
            cognition_records=cognition_records,
            membrane_available=self.load_result.membrane_present,
            source_pressure_status=sp_status)

        # Downstream contracts.
        self.contracts = evaluate_contracts(
            membrane_present=self.load_result.membrane_present,
            impressions_present=self.load_result.impressions_present,
            ancestry=self.ancestry, strict=self.strict)

        # Bypass detection.
        self.bypass_findings = MembraneBypassDetector().detect(
            impressions_present=self.load_result.impressions_present,
            membrane_present=self.load_result.membrane_present,
            ancestry=self.ancestry, contracts=self.contracts,
            strict=self.strict)

        # Module adapters (tolerant; read-only).
        self._run_adapters()

        # Pipeline audit.
        self.audit = MembranePipelineAudit().audit(
            load_result=self.load_result, ancestry=self.ancestry,
            contracts=self.contracts, bypass_findings=self.bypass_findings,
            adapters=self.adapters, strict=self.strict)

        # Strict blockers.
        if self.strict and MembraneBypassDetector.has_blocking(
                self.bypass_findings):
            self.blocked = True
            self.blockers.append(
                "critical/blocker membrane bypass in strict mode")
        if require_membrane and not self.load_result.membrane_present:
            self.blocked = True
        if require_impressions and not self.load_result.impressions_present:
            self.blocked = True

        if not self.dry_run:
            self.write_artifacts()
        return self._result()

    def run_doctor(self) -> Dict[str, Any]:
        load = SensoryImpressionLoader().load(self.state_dir)
        bounded = self.safety.validate_bounded(self.max_runtime_s).safe
        blockers = []
        if self.require_membrane and not load.membrane_present:
            blockers.append("membrane required but not present")
        if self.require_impressions and not load.impressions_present:
            blockers.append("impressions required but not present")
        if not bounded:
            blockers.append("runtime is unbounded")
        return {
            "integration_profile": self.integration_profile.profile_id,
            "membrane_present": load.membrane_present,
            "impressions_present": load.impressions_present,
            "bounded": bounded, "blockers": blockers, "passed": not blockers,
            "note": "membrane integration doctor validates profile, membrane "
                    "artifacts, impressions, and bounded runtime read-only",
        }

    # -- artifact loaders ---------------------------------------------------

    def _read_json(self, *parts) -> Dict[str, Any]:
        path = os.path.join(self.state_dir, *parts)
        if not os.path.isfile(path):
            return {}
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}

    def _concept_records(self) -> List[Dict[str, Any]]:
        data = self._read_json("ontogenesis", "concepts",
                               "LIVE_CONCEPT_MEMORY.json")
        return [r for r in data.get("records", [])
                if r.get("status") in ("born", "stable_candidate")]

    def _sign_records(self) -> List[Dict[str, Any]]:
        data = self._read_json("semiogenesis", "signs", "LIVE_SIGN_MEMORY.json")
        return [r for r in data.get("records", [])
                if r.get("status") in ("born", "stable_candidate")]

    def _cognition_records(self) -> List[Dict[str, Any]]:
        data = self._read_json("cognition", "traces",
                               "LIVE_COGNITION_MEMORY.json")
        return [r for r in data.get("records", [])
                if r.get("status") in ("useful", "stable")]

    def _source_pressure_status(self) -> str:
        sp = self.load_result.source_pressure_report if self.load_result else {}
        return sp.get("status", "unknown")

    def _run_adapters(self) -> None:
        try:
            self.adapters["live_birth"] = LiveBirthMembraneAdapter().run(
                self.state_dir, self.load_result)
            self.adapters["live_observation"] = \
                LiveObservationMembraneAdapter().run(
                    self.state_dir, self.load_result)
            self.adapters["live_ontogenesis"] = \
                LiveOntogenesisMembraneAdapter().run(
                    self.state_dir, self.load_result, strict=self.strict)
            self.adapters["live_semiogenesis"] = \
                LiveSemiogenesisMembraneAdapter().run(
                    self.state_dir, self.ancestry, strict=self.strict)
            self.adapters["live_cognition"] = \
                LiveCognitionMembraneAdapter().run(
                    self.state_dir, self.ancestry, strict=self.strict)
            bypass_summary = MembraneBypassDetector.summary(self.bypass_findings)
            self.adapters["scientific_claims"] = \
                ScientificClaimsMembraneAdapter().run(
                    self.state_dir, self.load_result, self.bypass_findings)
            self.adapters["research_cycle"] = \
                ResearchCycleMembraneAdapter().run(
                    self.state_dir, bypass_summary)
            self.adapters["alpha_system"] = AlphaSystemMembraneAdapter().run(
                self.state_dir, self.load_result, bypass_summary, self.ancestry)
        except Exception as exc:  # pragma: no cover - defensive
            self.warnings.append(f"adapter error (tolerated): {exc}")

    # -- result + integration views -----------------------------------------

    def _result(self) -> Dict[str, Any]:
        bypass = MembraneBypassDetector.summary(self.bypass_findings)
        return {
            "refused": False, "run_id": self.run_id, "blocked": self.blocked,
            "blockers": list(self.blockers),
            "membrane_present": self.load_result.membrane_present,
            "impression_count": len(self.load_result.impressions),
            "bypass_finding_count": bypass["bypass_finding_count"],
            "critical_bypass_count": bypass["critical_bypass_count"],
            "ancestry_chain_count": len(self.ancestry.chains)
            if self.ancestry else 0,
            "pipeline_status": self.audit.overall_status if self.audit
            else "unknown",
            "report": self.reports.get("markdown"),
        }

    def integration_status(self) -> Dict[str, Any]:
        bypass = MembraneBypassDetector.summary(self.bypass_findings)
        anc = self.ancestry.to_dict() if self.ancestry else {}
        return {
            "membrane_integration_enabled": True,
            "integration_run_id": self.run_id,
            "integration_blocked": self.blocked,
            "integration_profile": self.integration_profile.profile_id,
            "membrane_present": self.load_result.membrane_present
            if self.load_result else False,
            "impression_count": len(self.load_result.impressions)
            if self.load_result else 0,
            "ancestry_chain_count": anc.get("ancestry_chain_count", 0),
            "with_impression_ancestry": anc.get("with_impression_ancestry", 0),
            "missing_ancestry": anc.get("missing_ancestry", 0),
            "bypass_finding_count": bypass["bypass_finding_count"],
            "critical_bypass_count": bypass["critical_bypass_count"],
            "blocker_bypass_count": bypass["blocker_bypass_count"],
            "raw_fallback_count": sum(
                1 for c in (self.ancestry.chains if self.ancestry else [])
                if c.fallback_raw_event),
            "pipeline_status": self.audit.overall_status if self.audit
            else "unknown",
            "contract_violated_count": contract_summary(
                self.contracts)["violated_count"] if self.contracts else 0,
            "latest_integration_report_path": self.reports.get("markdown"),
            "ancestry_validation_status": (
                "ok" if anc.get("missing_ancestry", 0) == 0 else
                "missing_ancestry"),
            "membrane_integration_safety_block_count": self.safety.rejected_count,
            "starts_feeders": False, "controls_hardware": False,
            "accesses_network": False, "runs_git": False,
        }

    def snapshot(self) -> Dict[str, Any]:
        return self.integration_status()

    def recommended_next_action(self) -> str:
        if self.blocked or MembraneBypassDetector.has_blocking(
                self.bypass_findings):
            return "Resolve membrane bypass / missing ancestry before proceeding."
        if not (self.load_result and self.load_result.impressions_present):
            return "Run the environmental membrane to generate sensory impressions."
        return "Run post-birth live observation using sensory impressions."

    def write_artifacts(self) -> Dict[str, Any]:
        from .reports import MembraneIntegrationReportBuilder

        if self.ancestry is not None:
            self.ancestry.write(self.state_dir)
        self._write_index()
        self.reports = MembraneIntegrationReportBuilder(self).write()
        return {"reports": self.reports}

    def _write_index(self) -> None:
        base = os.path.join(self.state_dir, "membrane", "integration")
        os.makedirs(base, exist_ok=True)
        with open(os.path.join(base, f"{self.run_id}.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(self.integration_status(), fh, indent=2, default=str)
