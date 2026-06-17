"""Environmental membrane runtime -- the perceptual boundary organ, bounded/read-only.

:class:`EnvironmentalMembraneRuntime` loads the membrane profile, governance, and
feeder registry; reads accepted live read-only events (from the Prompt 67 inbox
validator) or sample fixture events; builds the receptor field; matches events;
computes source pressure; assesses contamination; regulates permeability; runs immune
responses; generates sensory impressions; updates append-only membrane memory; and
writes the impression index, immune log, memory, and membrane reports.

It is bounded and local-only. It reads local accepted-event records only; it does not
start/stop/control feeders, call the network/shell/Git/GitHub, control hardware,
execute commands, modify the feeder registry or governance, publish, or claim
consciousness/life/agency.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..live_birth.event_validator import LiveEventValidator
from ..live_birth.feeder_registry import LiveFeederRegistry
from ..live_birth.governance import GovernanceValidator
from ..live_birth.inbox_spool import LiveInboxSpool
from ..live_birth.quarantine import QuarantineStore
from .contamination import MembraneContaminationAnalyzer
from .immune_response import ImmuneResponseAction, MembraneImmuneResponse
from .membrane_memory import MembraneMemory
from .membrane_profile import MembraneProfileMode, get_membrane_profile
from .permeability import MembranePermeabilityGate, PermeabilityStatus
from .receptor_field import EnvironmentalReceptorField, ReceptorKind
from .safety import EnvironmentalMembraneSafetyValidator
from .salience_modulation import MembraneSalienceModulator
from .sensory_impression import (
    SensoryImpression,
    SensoryImpressionGrounding,
    SensoryImpressionKind,
    SensoryImpressionQuality,
    SensoryImpressionStore,
)
from .source_pressure import MembraneSourcePressure

_SUBDIRS = ("receptors", "impressions", "permeability", "source_pressure",
            "immune", "memory", "reports", "index")

_HUMAN_TEXT_SOURCES = ("operator_pulse", "local_environment_manual")

_RECEPTOR_IMPRESSION = {
    ReceptorKind.CHRONOS: SensoryImpressionKind.CHRONOS_TICK,
    ReceptorKind.MACHINE_BODY: SensoryImpressionKind.MACHINE_BODY_PRESSURE,
    ReceptorKind.LOCAL_ENVIRONMENT: SensoryImpressionKind.ENVIRONMENTAL_SCALAR,
    ReceptorKind.WEATHER: SensoryImpressionKind.ENVIRONMENTAL_SCALAR,
    ReceptorKind.PROJECT_FIELD: SensoryImpressionKind.PROJECT_FIELD_CHANGE,
    ReceptorKind.OPERATOR_PULSE: SensoryImpressionKind.OPERATOR_PULSE,
    ReceptorKind.ABSENCE: SensoryImpressionKind.ABSENCE,
    ReceptorKind.NOISE: SensoryImpressionKind.SOURCE_NOISE,
    ReceptorKind.UNKNOWN_SOURCE: SensoryImpressionKind.UNKNOWN,
}


@dataclass
class EnvironmentalMembraneRuntime:
    """Bounded, local, read-only environmental membrane runtime."""

    state_dir: str = ".solaris_ai_nn_live"
    alpha_state_dir: str = ".solaris_ai_nn_alpha"
    profile: Optional[str] = None
    max_runtime_s: float = 120.0
    max_events: int = 2000
    max_files: int = 100
    report_only: bool = False
    dry_run: bool = False
    strict: bool = False
    require_governance: bool = True
    require_feeder_registry: bool = False
    require_validated_events: bool = True
    allow_fixture_events: bool = True
    require_claimguard: bool = False
    operator_note: str = ""

    safety: EnvironmentalMembraneSafetyValidator = field(
        default_factory=EnvironmentalMembraneSafetyValidator, init=False)
    membrane_profile: Any = field(default=None, init=False)
    governance: Any = field(default=None, init=False)
    governance_result: Dict[str, Any] = field(default_factory=dict, init=False)
    feeders: Any = field(default=None, init=False)
    quarantine: Any = field(default=None, init=False)
    run_id: str = field(default="", init=False)
    blocked: bool = field(default=False, init=False)
    blockers: List[str] = field(default_factory=list, init=False)
    warnings: List[str] = field(default_factory=list, init=False)

    events: List[Dict[str, Any]] = field(default_factory=list, init=False)
    quarantine_by_source: Dict[str, int] = field(default_factory=dict,
                                                 init=False)
    receptor_field: Any = field(default=None, init=False)
    matches: List[Dict[str, Any]] = field(default_factory=list, init=False)
    source_pressure: Dict[str, Any] = field(default_factory=dict, init=False)
    contamination_results: List[Dict[str, Any]] = field(default_factory=list,
                                                        init=False)
    permeability_decisions: List[Dict[str, Any]] = field(default_factory=list,
                                                         init=False)
    immune_records: List[Any] = field(default_factory=list, init=False)
    impression_store: Any = field(default=None, init=False)
    membrane_memory: Any = field(default=None, init=False)
    reports: Dict[str, Any] = field(default_factory=dict, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.state_dir == self.alpha_state_dir:
            self.state_dir = ".solaris_ai_nn_live"
        self.membrane_profile = get_membrane_profile(self.profile)
        self.run_id = f"membrane_{int(time.time())}"
        if not self.max_runtime_s:
            self._refused = True

    # -- state layout -------------------------------------------------------

    def initialize(self) -> Dict[str, Any]:
        base = os.path.join(self.state_dir, "membrane")
        os.makedirs(base, exist_ok=True)
        created = []
        for name in _SUBDIRS:
            path = os.path.join(base, name)
            existed = os.path.isdir(path)
            os.makedirs(path, exist_ok=True)
            created.append({"name": name, "existed": existed})
        return {"membrane_dir": base, "directories": created,
                "deletes_state": False}

    # -- doctor -------------------------------------------------------------

    def run_doctor(self) -> Dict[str, Any]:
        self.initialize()
        self.governance = GovernanceValidator().load(self.state_dir)
        self.governance_result = GovernanceValidator().validate(self.governance)
        self.feeders = LiveFeederRegistry.load(self.state_dir)
        inbox = os.path.join(self.state_dir, "inbox")
        has_events = os.path.isdir(inbox) and any(
            n.endswith(".jsonl") for n in os.listdir(inbox)) \
            if os.path.isdir(inbox) else False
        bounded = self.safety.validate_bounded(self.max_runtime_s).safe
        blockers = []
        if self.membrane_profile.is_live and self.require_governance \
                and not self.governance_result.get("governance_passed"):
            blockers += list(self.governance_result.get(
                "blockers", ["governance not approved"]))
        if self.membrane_profile.is_live and self.require_feeder_registry \
                and not self.feeders.present:
            blockers.append("feeder registry required but not present")
        if not bounded:
            blockers.append("runtime is unbounded")
        return {
            "membrane_profile": self.membrane_profile.profile_id,
            "governance_status": self.governance_result.get("governance_status"),
            "governance_passed": self.governance_result.get("governance_passed"),
            "feeder_registry_present": self.feeders.present,
            "inbox_has_events": has_events, "bounded": bounded,
            "blockers": blockers, "passed": not blockers,
            "note": "membrane doctor validates profile, governance, feeder "
                    "registry, accepted-event availability, and bounded runtime "
                    "read-only",
        }

    # -- run ----------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        if self._refused or not self.safety.validate_bounded(
                self.max_runtime_s).safe:
            return {"refused": True, "reason": "unbounded runtime"}

        self.initialize()
        self.quarantine = QuarantineStore(state_dir=self.state_dir)
        self.governance = GovernanceValidator().load(self.state_dir)
        self.governance_result = GovernanceValidator().validate(self.governance)
        self.feeders = LiveFeederRegistry.load(self.state_dir)

        gov_ok = self.governance_result.get("governance_passed", False)
        if self.membrane_profile.is_live and self.require_governance \
                and not gov_ok:
            self.blocked = True
            self.blockers = list(self.governance_result.get(
                "blockers", ["governance not present/approved"]))
        if self.membrane_profile.is_live and self.require_feeder_registry \
                and not self.feeders.present:
            self.blocked = True
            self.blockers.append("feeder registry required but not present")

        if not self.blocked:
            self._read_events()
            self._process()
        else:
            self.impression_store = SensoryImpressionStore(
                state_dir=self.state_dir)
            self.membrane_memory = MembraneMemory(
                state_dir=self.state_dir).load()

        if not self.dry_run:
            self.write_artifacts()
        return self._result()

    def analyze_events(self, events: List[Dict[str, Any]], *,
                       load_status: str = "",
                       quarantine_by_source: Optional[Dict[str, int]] = None,
                       ) -> "EnvironmentalMembraneRuntime":
        """Process already-trusted event dicts directly (component demos/tests)."""
        self.events = list(events)
        self.quarantine_by_source = dict(quarantine_by_source or {})
        if not self.governance_result:
            self.governance_result = {"governance_passed": True}
        self._process(load_status=load_status)
        return self

    def _read_events(self) -> None:
        from ..live_birth.birth_profile import ALLOWED_FIRST_BIRTH_SOURCES

        inbox = os.path.join(self.state_dir, "inbox")
        if not os.path.isdir(inbox):
            return
        allowed = (self.governance.allowed_sources
                   or list(ALLOWED_FIRST_BIRTH_SOURCES))
        validator = LiveEventValidator(
            allowed_sources=allowed,
            registered_sources=[r.source_id for r in self.feeders.records]
            if self.feeders else [], strict=False)
        spool = LiveInboxSpool(
            inbox_dir=inbox, validator=validator, quarantine=self.quarantine,
            max_files=self.max_files, max_events=self.max_events)
        read = spool.read()
        for env in read.accepted_envelopes:
            if env.event is not None:
                self.events.append(env.event.to_dict())
        for rec in self.quarantine.records:
            orig = rec.original
            sid = orig.get("source_id", "") if isinstance(orig, dict) else ""
            self.quarantine_by_source[sid] = \
                self.quarantine_by_source.get(sid, 0) + 1

    def _load_observation_load(self) -> str:
        report = os.path.join(self.state_dir, "observation", "reports",
                              "LIVE_OBSERVATION_REPORT.json")
        if os.path.isfile(report):
            try:
                with open(report, encoding="utf-8") as fh:
                    sections = (json.load(fh).get("sections", {}) or {})
                return (sections.get("load", {}) or {}).get("load_status", "")
            except Exception:
                return ""
        return ""

    def _process(self, load_status: str = "") -> None:
        load_status = load_status or self._load_observation_load()
        self.receptor_field = EnvironmentalReceptorField()
        self.impression_store = SensoryImpressionStore(state_dir=self.state_dir)
        self.membrane_memory = MembraneMemory(state_dir=self.state_dir).load()

        # Source pressure (informs permeability, never modifies feeders).
        expected = ([r.source_id for r in self.feeders.records]
                    if self.feeders and self.feeders.records else [])
        sp = MembraneSourcePressure().assess(
            events=self.events, quarantined=self.quarantine_by_source,
            expected_sources=expected)
        self.source_pressure = sp.to_dict()

        gate = MembranePermeabilityGate(
            operator_attenuation=1.0 - self.membrane_profile
            .operator_pulse_salience_cap)
        analyzer = MembraneContaminationAnalyzer()
        immune = MembraneImmuneResponse()
        modulator = MembraneSalienceModulator(
            operator_pulse_cap=self.membrane_profile.operator_pulse_salience_cap,
            human_text_cap=self.membrane_profile.human_text_salience_cap)
        gov_ok = self.governance_result.get("governance_passed", False)
        feeder_present = bool(self.feeders and self.feeders.present)

        seen_payloads: Dict[str, int] = {}
        for ev in self.events:
            match = self.receptor_field.match(ev)
            self.matches.append(match.to_dict())
            receptor = self.receptor_field.receptor(match.receptor_id)

            contamination = analyzer.evaluate(ev, source_pressure=self.source_pressure)
            self.contamination_results.append(contamination.to_dict())

            decision = gate.decide(
                event=ev, receptor=receptor, contamination=contamination,
                source_pressure=self.source_pressure, governance_passed=gov_ok,
                feeder_registry_present=feeder_present, validated=True,
                load_status=load_status)
            self.permeability_decisions.append(decision.to_dict())

            rec = immune.respond(decision=decision, contamination=contamination)
            self.immune_records.append(rec)

            self._make_impression(ev, match, decision, contamination,
                                  modulator, seen_payloads, load_status)

        self._update_memory()

    def _make_impression(self, ev, match, decision, contamination, modulator,
                         seen_payloads, load_status) -> None:
        import json as _json

        sid = str(ev.get("source_id", ""))
        quality = ev.get("quality", {}) or {}
        receptor = self.receptor_field.receptor(match.receptor_id)
        base_perm = getattr(receptor, "baseline_permeability", 0.5)

        payload_key = sid + "|" + _json.dumps(ev.get("payload"), sort_keys=True,
                                              default=str)
        seen = seen_payloads.get(payload_key, 0)
        seen_payloads[payload_key] = seen + 1
        repetition = min(1.0, seen / 5.0)
        novelty = max(0.0, 1.0 - repetition)

        op_weight = 1.0 if sid == "operator_pulse" else 0.0
        human_weight = 1.0 if sid in _HUMAN_TEXT_SOURCES else 0.0
        gloss_weight = 1.0 if str(ev.get("debug_gloss", "")).strip() else 0.0

        overload = 1.0 if decision.creates_overload else 0.0
        deprivation = 1.0 if decision.creates_deprivation else 0.0
        salience = modulator.modulate(
            novelty=novelty, recurrence=repetition,
            is_absence=match.is_absence,
            source_reliability=getattr(
                self.membrane_memory._source(sid), "reliability", 0.7),
            source_count=len(self.source_pressure.get("by_source", {})),
            payload_change=novelty, overload=overload, deprivation=deprivation,
            contamination=contamination.score, operator_weight=op_weight,
            human_text_weight=human_weight, debug_gloss_weight=gloss_weight)

        kind = _RECEPTOR_IMPRESSION.get(match.receptor_id,
                                        SensoryImpressionKind.UNKNOWN)
        if decision.creates_overload:
            kind = SensoryImpressionKind.SOURCE_OVERLOAD
        elif decision.creates_deprivation:
            kind = SensoryImpressionKind.SOURCE_DEPRIVATION
        elif match.is_absence:
            kind = SensoryImpressionKind.ABSENCE
        elif match.is_noisy and contamination.score < 0.5:
            kind = SensoryImpressionKind.SOURCE_NOISE
        if decision.status == PermeabilityStatus.QUARANTINE:
            kind = SensoryImpressionKind.QUARANTINE_SHADOW

        grounding = self._grounding(match, kind)
        intensity = round(base_perm * decision.attenuation, 3)
        imp = SensoryImpression(
            impression_id=f"{self.run_id}_imp{len(self.impression_store.impressions)}",
            source_event_id=str(ev.get("event_id", "")),
            timestamp_utc=str(ev.get("timestamp_utc", "")), source_id=sid,
            receptor_id=match.receptor_id, modality=str(ev.get("modality", "")),
            channel=str(ev.get("channel", "")), impression_kind=kind,
            perceptual_intensity=intensity, salience=salience.score,
            novelty=novelty, repetition=repetition,
            risk=getattr(receptor, "baseline_risk", 0.1),
            contamination=contamination.score,
            source_pressure=float(self.source_pressure.get(
                "membrane_source_pressure_dominance_score", 0.0) or 0.0),
            absence_component=1.0 if match.is_absence else 0.0,
            overload_component=overload, deprivation_component=deprivation,
            human_text_weight=human_weight, operator_pulse_weight=op_weight,
            debug_gloss_weight=gloss_weight, grounding=grounding,
            quality=SensoryImpressionQuality(
                completeness=float(quality.get("completeness", 1.0) or 0.0),
                noise=float(quality.get("noise", 0.0) or 0.0),
                confidence=round(1.0 - contamination.score, 3),
                is_noisy=bool(quality.get("is_noisy"))),
            permeability_status=decision.status,
            evidence_refs=[str(ev.get("event_id", ""))])
        gloss = str(ev.get("debug_gloss", "")).strip()
        if gloss:
            imp.debug_gloss_annotation = gloss[:160]
            imp.limitations.append("debug gloss kept as annotation, not truth")
        if op_weight:
            imp.limitations.append("operator pulse is stimulus, not teaching")
        self.impression_store.add(imp)

    @staticmethod
    def _grounding(match, kind) -> str:
        if match.is_absence:
            return SensoryImpressionGrounding.ABSENCE_BASED
        if kind in (SensoryImpressionKind.MACHINE_BODY_PRESSURE,
                    SensoryImpressionKind.SOURCE_OVERLOAD,
                    SensoryImpressionKind.SOURCE_DEPRIVATION):
            return SensoryImpressionGrounding.PRESSURE_BASED
        if kind == SensoryImpressionKind.CHRONOS_TICK:
            return SensoryImpressionGrounding.RHYTHM_BASED
        if kind == SensoryImpressionKind.OPERATOR_PULSE:
            return SensoryImpressionGrounding.SOURCE_BASED
        if kind == SensoryImpressionKind.UNKNOWN:
            return SensoryImpressionGrounding.UNKNOWN
        return SensoryImpressionGrounding.FEATURE_BASED

    def _update_memory(self) -> None:
        # Aggregate per-source signals for boundary memory.
        per_source: Dict[str, Dict[str, int]] = {}
        for d in self.permeability_decisions:
            sid = d["source_id"]
            agg = per_source.setdefault(sid, {"quarantined": 0, "useful": 0,
                                              "operator": 0, "gloss": 0,
                                              "overload": 0, "deprivation": 0})
            if d["status"] == PermeabilityStatus.QUARANTINE:
                agg["quarantined"] += 1
            elif d["allowed"]:
                agg["useful"] += 1
            if d.get("creates_overload"):
                agg["overload"] += 1
            if d.get("creates_deprivation"):
                agg["deprivation"] += 1
        for c in self.contamination_results:
            sid = c["source_id"]
            agg = per_source.setdefault(sid, {"quarantined": 0, "useful": 0,
                                              "operator": 0, "gloss": 0,
                                              "overload": 0, "deprivation": 0})
            if "operator_pulse_dominance" in [f["contamination_type"]
                                              for f in c["findings"]]:
                agg["operator"] += 1
            if "debug_gloss_ground_truth_attempt" in [
                    f["contamination_type"] for f in c["findings"]]:
                agg["gloss"] += 1
        dominant = self.source_pressure.get("dominant_source", "")
        for sid, agg in per_source.items():
            self.membrane_memory.update_source(
                self.run_id, sid, quarantined=agg["quarantined"],
                useful=agg["useful"], operator_contamination=agg["operator"],
                debug_gloss=agg["gloss"], overload=agg["overload"],
                deprivation=agg["deprivation"], dominant=(sid == dominant))
        for sid in self.source_pressure.get("missing_expected_sources", []):
            self.membrane_memory.update_source(self.run_id, sid, silent=True)

    # -- result + integration views -----------------------------------------

    def _result(self) -> Dict[str, Any]:
        perm = MembranePermeabilityGate.summary(
            [self._mk_decision(d) for d in self.permeability_decisions])
        idx = self.impression_store.index() if self.impression_store else {}
        return {
            "refused": False, "run_id": self.run_id, "blocked": self.blocked,
            "blockers": list(self.blockers),
            "membrane_event_input_count": len(self.events),
            "membrane_impression_count": idx.get("membrane_impression_count", 0),
            "membrane_blocked_count": perm.get("membrane_blocked_count", 0),
            "membrane_quarantined_count": perm.get(
                "membrane_quarantined_count", 0),
            "source_pressure_status": self.source_pressure.get("status"),
            "report": self.reports.get("markdown"),
            "impression_index": (self.impression_store.index_json_path
                                 if self.impression_store else None),
        }

    @staticmethod
    def _mk_decision(d: Dict[str, Any]):
        from .permeability import PermeabilityDecision

        return PermeabilityDecision(
            event_id=d.get("event_id", ""), source_id=d.get("source_id", ""),
            receptor_id=d.get("receptor_id", ""),
            status=d.get("status", "unknown"))

    @staticmethod
    def _mk_contamination(c: Dict[str, Any]):
        from .contamination import (
            MembraneContaminationAssessment, MembraneContaminationFinding)

        a = MembraneContaminationAssessment(
            event_id=c.get("event_id", ""), source_id=c.get("source_id", ""))
        for f in c.get("findings", []):
            a.findings.append(MembraneContaminationFinding(
                f.get("contamination_type", "unknown"), f.get("detail", ""),
                blocks=f.get("blocks", False)))
        return a

    def membrane_status(self) -> Dict[str, Any]:
        perm = MembranePermeabilityGate.summary(
            [self._mk_decision(d) for d in self.permeability_decisions])
        immune = MembraneImmuneResponse.summary(self.immune_records)
        contamination = self.source_pressure
        idx = self.impression_store.index() if self.impression_store else {}
        return {
            "membrane_enabled": True, "membrane_run_id": self.run_id,
            "membrane_blocked": self.blocked,
            "membrane_profile": self.membrane_profile.profile_id,
            "membrane_receptor_count": (self.receptor_field.index()[
                "membrane_receptor_count"] if self.receptor_field else 0),
            "membrane_event_input_count": len(self.events),
            "membrane_impression_count": idx.get("membrane_impression_count", 0),
            "membrane_allowed_count": perm.get("membrane_allowed_count", 0),
            "membrane_attenuated_count": perm.get(
                "membrane_attenuated_count", 0),
            "membrane_amplified_count": perm.get("membrane_amplified_count", 0),
            "membrane_blocked_count": perm.get("membrane_blocked_count", 0),
            "membrane_quarantined_count": perm.get(
                "membrane_quarantined_count", 0),
            "membrane_deferred_count": perm.get("membrane_deferred_count", 0),
            "membrane_absence_impression_count": immune.get(
                "membrane_absence_impression_count", 0),
            "membrane_overload_impression_count": immune.get(
                "membrane_overload_impression_count", 0),
            "membrane_deprivation_impression_count": immune.get(
                "membrane_deprivation_impression_count", 0),
            "membrane_contamination_count": sum(
                len(c["findings"]) for c in self.contamination_results),
            "membrane_immune_response_count": immune.get(
                "membrane_immune_response_count", 0),
            "membrane_source_pressure_dominance_score": float(
                contamination.get(
                    "membrane_source_pressure_dominance_score", 0.0) or 0.0),
            "membrane_operator_dominance_score": float(
                contamination.get("membrane_operator_dominance_score", 0.0)
                or 0.0),
            "source_pressure_status": contamination.get("status"),
            "latest_membrane_report_path": self.reports.get("markdown"),
            "latest_membrane_memory_path": (self.membrane_memory.memory_path
                                            if self.membrane_memory else None),
            "membrane_safety_block_count": self.safety.rejected_count,
            "membrane_safety_status": ("blocked" if self.blocked else "pass"),
            "starts_feeders": False, "controls_hardware": False,
            "accesses_network": False, "runs_git": False,
        }

    def snapshot(self) -> Dict[str, Any]:
        return self.membrane_status()

    def downstream_readiness(self) -> Dict[str, Any]:
        idx = self.impression_store.index() if self.impression_store else {}
        impressions = idx.get("membrane_impression_count", 0)
        if self.blocked:
            phase = "resolve_membrane_blockers"
        elif impressions:
            phase = "run_post_birth_observation_using_sensory_impressions"
        else:
            phase = "collect_more_events"
        return {"downstream_ready": (not self.blocked) and bool(impressions),
                "recommended_next_phase": phase,
                "raw_event_bypass": False,
                "note": "downstream modules should consume sensory impressions, "
                        "not raw events"}

    # -- integrations (optional; read-only / record-only) -------------------

    def impressions_for_downstream(self) -> List[Dict[str, Any]]:
        """The membrane's output for downstream modules (impressions, not events).

        Downstream live modules (observation, ontogenesis, semiogenesis,
        cognition) should consume these sensory impressions -- never raw events.
        Blocked/quarantined impressions are included but flagged so downstream
        gating can reject them.
        """
        if not self.impression_store:
            return []
        return [imp.to_dict() for imp in self.impression_store.impressions]

    def metabolism_nutrients(self) -> Dict[str, Any]:
        """Membrane outputs as perceptual-metabolism nutrient records (report-only).

        Metabolism should not request more data or alter feeder behavior; this is
        a report-only handoff of impression-derived nutrients.
        """
        impressions = (self.impression_store.impressions
                       if self.impression_store else [])
        allowed = [i for i in impressions if not i.blocked]
        n = max(1, len(allowed))
        return {
            "nutrient_impression_count": len(allowed),
            "mean_intensity": round(sum(i.perceptual_intensity
                                        for i in allowed) / n, 3),
            "mean_salience": round(sum(i.salience for i in allowed) / n, 3),
            "mean_novelty": round(sum(i.novelty for i in allowed) / n, 3),
            "mean_repetition": round(sum(i.repetition for i in allowed) / n, 3),
            "overload_count": sum(1 for i in allowed
                                  if i.overload_component > 0),
            "deprivation_count": sum(1 for i in allowed
                                     if i.deprivation_component > 0),
            "mean_contamination": round(sum(i.contamination
                                            for i in allowed) / n, 3),
            "source_pressure_status": self.source_pressure.get("status"),
            "requests_more_data": False, "alters_feeder_behavior": False,
            "note": "report-only nutrient handoff; metabolism requests no data "
                    "and alters no feeder behavior",
        }

    def research_cycle_update(self) -> Dict[str, Any]:
        action = ("Run post-birth live observation using sensory impressions."
                  if not self.blocked else
                  "Resolve membrane blockers, source pressure, or contamination.")
        return {"membrane_evidence_recorded": True, "next_action": action,
                "operational_only": True}

    def scientific_claims_update(self) -> Dict[str, Any]:
        idx = self.impression_store.index() if self.impression_store else {}
        return {
            "impression_count": idx.get("membrane_impression_count", 0),
            "evidence_kind": "operational_membrane_filtered_impression",
            "distinguishes_raw_from_impression": True,
            "blocks_consciousness_life_agency_interpretation": True,
        }

    def write_artifacts(self) -> Dict[str, Any]:
        from .reports import EnvironmentalMembraneReportBuilder

        if self.impression_store is None:
            self.impression_store = SensoryImpressionStore(
                state_dir=self.state_dir)
        if self.membrane_memory is None:
            self.membrane_memory = MembraneMemory(
                state_dir=self.state_dir).load()
        self._write_state()
        if not self.dry_run:
            self.impression_store.write()
            MembraneImmuneResponse.write(self.immune_records, self.state_dir)
            self.membrane_memory.write()
            if self.receptor_field:
                self._dump("receptors", f"{self.run_id}.json",
                           self.receptor_field.index())
        self.reports = EnvironmentalMembraneReportBuilder(self).write()
        return {"reports": self.reports}

    def _dump(self, subdir: str, name: str, obj: Any) -> None:
        path = os.path.join(self.state_dir, "membrane", subdir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, default=str)

    def _write_state(self) -> None:
        self._dump("permeability", f"{self.run_id}.json",
                   {"decisions": self.permeability_decisions})
        self._dump("source_pressure", f"{self.run_id}.json", self.source_pressure)
        self._dump("index", f"{self.run_id}.json", self.membrane_status())
