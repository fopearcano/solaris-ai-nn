"""First live cognition runtime -- bounded, read-only, conservative, no action.

:class:`FirstLiveCognitionRuntime` runs the first live cognition phase: it loads
governance, the birth certificate, observation/ontogenesis/semiogenesis reports, the
live concept and sign memory, and the private syntax graph; selects eligible
(born/stable, uncontaminated) private signs; builds cognition traces; generates
bounded sign-based anticipations; estimates explicit uncertainty; traverses private
relations within a bounded depth; runs bounded internal simulations; assesses
predictions against later live-read-only events; filters contamination; gates
cognition readiness; updates append-only cognition memory; and writes a cognition
record and reports.

It is bounded and local-only. It does not enable real-world action, action-reaction
learning, developmental autonomy, or self-boundary tracking; it does not
start/stop/configure feeders, control hardware, access the network/shell/browser/OS/
camera/microphone, call Git/GitHub, execute commands, or modify source; it does not
treat sensory text as a command, human labels / debug gloss as ground truth, or the
operator pulse as teaching; and it makes no claim of language understanding,
reasoning, consciousness, sentience, life, personhood, agency, free will, emotion,
feeling, self-awareness, or subjective experience.
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
from .anticipation_engine import LiveAnticipationEngine
from .cognition_contamination_filter import LiveCognitionContaminationFilter
from .cognition_memory import LiveCognitionMemory, LiveCognitionRecord
from .cognition_profile import get_cognition_profile
from .cognition_readiness_gate import LiveCognitionReadinessGate
from .cognition_trace import CognitionTraceStatus, LiveCognitionTrace
from .internal_simulation import LiveInternalSimulation
from .prediction_assessment import LivePredictionAssessment
from .relation_traversal import LiveRelationTraversal
from .safety import LiveCognitionSafetyValidator
from .sign_input import SignInputLoader
from .uncertainty_model import UncertaintyEstimator

_SUBDIRS = ("traces", "anticipations", "uncertainty", "simulations",
            "predictions", "contamination", "reports", "index")

_OUTCOME_RANK = {"matched": 5, "partially_matched": 4, "ambiguous": 3,
                 "not_yet_observed": 2, "contradicted": 1, "contaminated": 0}


@dataclass
class FirstLiveCognitionRuntime:
    """Bounded, local, read-only first live cognition runtime (no action)."""

    state_dir: str = ".solaris_ai_nn_live"
    alpha_state_dir: str = ".solaris_ai_nn_alpha"
    profile: Optional[str] = None
    max_runtime_s: float = 180.0
    max_signs: int = 200
    max_traces: int = 200
    max_simulation_steps: int = 8
    max_traversal_depth: int = 3
    min_prediction_utility: float = 0.5
    max_uncertainty: float = 0.6
    report_only: bool = False
    dry_run: bool = False
    strict: bool = False
    require_governance: bool = True
    require_birth_certificate: bool = True
    require_observation_stability: bool = True
    require_live_concepts: bool = True
    require_live_signs: bool = True
    allow_trace_only: bool = True
    allow_anticipation: bool = False
    allow_internal_simulation: bool = False
    require_claimguard: bool = False
    operator_note: str = ""

    safety: LiveCognitionSafetyValidator = field(
        default_factory=LiveCognitionSafetyValidator, init=False)
    cognition_profile: Any = field(default=None, init=False)
    governance: Any = field(default=None, init=False)
    governance_result: Dict[str, Any] = field(default_factory=dict, init=False)
    birth_certificate_present: bool = field(default=False, init=False)
    observation: Dict[str, Any] = field(default_factory=dict, init=False)
    sign_input: Dict[str, Any] = field(default_factory=dict, init=False)
    private_syntax: Dict[str, Any] = field(default_factory=dict, init=False)
    concept_memory_present: bool = field(default=False, init=False)
    run_id: str = field(default="", init=False)
    blocked: bool = field(default=False, init=False)
    blockers: List[str] = field(default_factory=list, init=False)
    warnings: List[str] = field(default_factory=list, init=False)

    eligible_signs: List[Any] = field(default_factory=list, init=False)
    traces: List[Any] = field(default_factory=list, init=False)
    anticipations: List[Any] = field(default_factory=list, init=False)
    simulations: List[Any] = field(default_factory=list, init=False)
    traversal: Dict[str, Any] = field(default_factory=dict, init=False)
    prediction: Dict[str, Any] = field(default_factory=dict, init=False)
    contamination_results: List[Dict[str, Any]] = field(default_factory=list,
                                                        init=False)
    readiness: Dict[str, Any] = field(default_factory=dict, init=False)
    cognition_memory: Any = field(default=None, init=False)
    record: Dict[str, Any] = field(default_factory=dict, init=False)
    reports: Dict[str, Any] = field(default_factory=dict, init=False)
    later_events: List[Dict[str, Any]] = field(default_factory=list, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.state_dir == self.alpha_state_dir:
            self.state_dir = ".solaris_ai_nn_live"
        self.cognition_profile = get_cognition_profile(self.profile)
        if self.cognition_profile.allow_anticipation:
            self.allow_anticipation = True
        if self.cognition_profile.allow_internal_simulation:
            self.allow_internal_simulation = True
        self.run_id = f"cog_{int(time.time())}"
        if not self.max_runtime_s:
            self._refused = True

    # -- state layout -------------------------------------------------------

    def initialize(self) -> Dict[str, Any]:
        base = os.path.join(self.state_dir, "cognition")
        os.makedirs(base, exist_ok=True)
        created = []
        for name in _SUBDIRS:
            path = os.path.join(base, name)
            existed = os.path.isdir(path)
            os.makedirs(path, exist_ok=True)
            created.append({"name": name, "existed": existed})
        return {"cognition_dir": base, "directories": created,
                "deletes_state": False}

    # -- doctor -------------------------------------------------------------

    def run_doctor(self) -> Dict[str, Any]:
        self.initialize()
        self.governance = GovernanceValidator().load(self.state_dir)
        self.governance_result = GovernanceValidator().validate(self.governance)
        cert = self._find_birth_certificate()
        observation = self._load_observation()
        sign_input = SignInputLoader().load(self.state_dir).to_dict()
        concepts = self._concept_memory_present()
        bounded = self.safety.validate_bounded(self.max_runtime_s).safe
        blockers = list(self.governance_result.get("blockers", []))
        if self.require_birth_certificate and not cert:
            blockers.append("birth certificate required but not present")
        if self.require_observation_stability and observation.get("blocked"):
            blockers.append("observation stability gate is blocked")
        if self.require_live_concepts and not concepts:
            blockers.append("live concept memory required but not present")
        if self.require_live_signs and not sign_input.get(
                "live_eligible_sign_count"):
            blockers.append("no eligible live signs present")
        if not bounded:
            blockers.append("runtime is unbounded")
        return {
            "governance_status": self.governance_result.get("governance_status"),
            "governance_passed": self.governance_result.get("governance_passed"),
            "birth_certificate_present": bool(cert),
            "observation_stability_blocked": observation.get("blocked"),
            "concept_memory_present": concepts,
            "eligible_sign_count": sign_input.get("live_eligible_sign_count", 0),
            "bounded": bounded, "blockers": blockers, "passed": not blockers,
            "note": "live cognition doctor validates governance, birth "
                    "certificate, observation stability, concepts, signs, and "
                    "bounded runtime read-only",
        }

    # -- run ----------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        if self._refused or not self.safety.validate_bounded(
                self.max_runtime_s).safe:
            return {"refused": True, "reason": "unbounded runtime"}

        self.initialize()
        self.governance = GovernanceValidator().load(self.state_dir)
        self.governance_result = GovernanceValidator().validate(self.governance)
        self.birth_certificate_present = bool(self._find_birth_certificate())
        self.observation = self._load_observation()
        self.concept_memory_present = self._concept_memory_present()
        sign_result = SignInputLoader().load(self.state_dir)
        self.sign_input = sign_result.to_dict()
        self.private_syntax = sign_result.private_syntax
        self.eligible_signs = sign_result.eligible

        gov_ok = self.governance_result.get("governance_passed", False)
        if self.require_governance and not gov_ok:
            self.blocked = True
            self.blockers = list(self.governance_result.get(
                "blockers", ["governance not present/approved"]))
        if self.require_birth_certificate and not self.birth_certificate_present:
            self.blocked = True
            self.blockers.append("birth certificate required but not present")
        if self.require_observation_stability:
            if not self.observation.get("present"):
                self.blocked = True
                self.blockers.append(
                    "observation reports required but not present")
            elif self.observation.get("blocked"):
                self.blocked = True
                self.blockers.append("observation stability gate is blocked")
        if self.require_live_concepts and not self.concept_memory_present:
            self.blocked = True
            self.blockers.append("live concept memory required but not present")
        if self.require_live_signs and not self.eligible_signs:
            self.blocked = True
            self.blockers.append("no eligible live signs present")

        if not self.blocked:
            self._read_later_events()
            self._analyze(self.eligible_signs)
        else:
            self.cognition_memory = LiveCognitionMemory(
                state_dir=self.state_dir).load()
            self._run_readiness_gate()

        if not self.dry_run:
            self.write_artifacts()
        return self._result()

    def analyze_signs(self, signs: List[Any], *,
                      observation: Optional[Dict[str, Any]] = None,
                      private_syntax: Optional[Dict[str, Any]] = None,
                      later_events: Optional[List[Dict[str, Any]]] = None,
                      ) -> "FirstLiveCognitionRuntime":
        """Run the pipeline directly on sign inputs (component demos / tests)."""
        self.eligible_signs = list(signs)
        self.observation = observation or {
            "present": True, "blocked": False, "stability_status": "ready",
            "load": {}, "source_diet": {}}
        self.private_syntax = private_syntax or {}
        self.later_events = later_events or []
        if not self.governance_result:
            self.governance_result = {"governance_passed": True}
        self.birth_certificate_present = True
        self.concept_memory_present = True
        if not self.sign_input:
            self.sign_input = {"live_eligible_sign_count": len(signs),
                               "sign_input_status": "synthetic"}
        self._analyze(signs)
        return self

    def _find_birth_certificate(self) -> str:
        cert_dir = os.path.join(self.state_dir, "certificates")
        if not os.path.isdir(cert_dir):
            return ""
        for name in sorted(os.listdir(cert_dir)):
            if name.endswith(".md") or name.endswith(".json"):
                return os.path.join(cert_dir, name)
        return ""

    def _concept_memory_present(self) -> bool:
        return os.path.isfile(os.path.join(
            self.state_dir, "ontogenesis", "concepts",
            "LIVE_CONCEPT_MEMORY.json"))

    def _load_observation(self) -> Dict[str, Any]:
        report = os.path.join(self.state_dir, "observation", "reports",
                              "LIVE_OBSERVATION_REPORT.json")
        sections: Dict[str, Any] = {}
        if os.path.isfile(report):
            try:
                with open(report, encoding="utf-8") as fh:
                    sections = (json.load(fh).get("sections", {}) or {})
            except Exception:
                sections = {}
        stability = sections.get("stability", {}) or {}
        return {
            "present": bool(sections),
            "blocked": bool(stability.get("blocked")),
            "stability_status": stability.get("live_stability_status",
                                              "unknown"),
            "load": sections.get("load", {}) or {},
            "source_diet": sections.get("source_diet", {}) or {},
            "rhythm": sections.get("rhythm", {}) or {},
        }

    def _read_later_events(self) -> None:
        """Read later live-read-only events for prediction assessment (bounded)."""
        try:
            allowed = (self.governance.allowed_sources if self.governance
                       else [])
            feeders = LiveFeederRegistry.load(self.state_dir)
            validator = LiveEventValidator(
                allowed_sources=allowed,
                registered_sources=[r.source_id for r in feeders.records],
                strict=False)
            quarantine = QuarantineStore(state_dir=self.state_dir)
            spool = LiveInboxSpool(
                inbox_dir=os.path.join(self.state_dir, "inbox"),
                validator=validator, quarantine=quarantine,
                max_files=50, max_events=self.max_signs * 4)
            read = spool.read()
            for env in read.accepted_envelopes:
                if env.event is not None:
                    self.later_events.append(env.event.to_dict())
        except Exception:
            self.later_events = []

    def _analyze(self, signs: List[Any]) -> None:
        obs = self.observation
        load = obs.get("load", {})
        load_status = load.get("load_status", "")
        rhythm = obs.get("rhythm", {})

        # Anticipations (only when allowed by the profile; else trace-only).
        engine = LiveAnticipationEngine()
        self.anticipations = (engine.anticipate(
            signs=signs[:self.max_signs], load_status=load_status,
            rhythm=rhythm, max_anticipations=self.max_traces)
            if self.allow_anticipation else [])

        # Internal simulations (only when allowed).
        self.simulations = (LiveInternalSimulation(
            max_steps=self.max_simulation_steps).simulate(
            self.anticipations, max_simulations=self.max_traces)
            if self.allow_internal_simulation else [])

        # Bounded traversal of the private syntax graph.
        self.traversal = LiveRelationTraversal(
            max_depth=self.max_traversal_depth).traverse(
            self.private_syntax).to_dict()

        # Prediction assessment against later events.
        self.prediction = LivePredictionAssessment().assess(
            anticipations=self.anticipations, later_events=self.later_events)
        outcome_by_sign = self._outcome_by_sign()

        # Build one trace per eligible sign.
        estimator = UncertaintyEstimator()
        cfilter = LiveCognitionContaminationFilter()
        self.cognition_memory = LiveCognitionMemory(
            state_dir=self.state_dir).load()
        sign_anticipations = self._anticipations_by_sign()

        for i, sign in enumerate(signs[:self.max_traces]):
            sid = getattr(sign, "sign_id", f"sign_{i}")
            sources = getattr(sign, "source_distribution", {}) or {}
            contamination_in = list(getattr(sign, "contamination_findings", [])
                                    or [])
            ant_ids = [a.anticipation_id for a in sign_anticipations.get(sid, [])]
            trace = LiveCognitionTrace(
                trace_id=f"{self.run_id}_t{i}",
                kind="anticipation" if ant_ids else "relation",
                linked_sign_ids=[sid],
                linked_concept_ids=list(getattr(sign, "linked_concept_ids", [])
                                        or []),
                anticipated_event_refs=ant_ids)
            for ref in getattr(sign, "supporting_refs", []) or []:
                trace.add_support(ref, kind="concept")
            for ref in getattr(sign, "contradicting_refs", []) or []:
                trace.add_counter(ref, reason="sign counterevidence")

            total = max(1, sum(sources.values()))
            op_share = sources.get("operator_pulse", 0) / total
            uncertainty = estimator.estimate(
                sign_stability=float(getattr(sign, "utility_score", 0.0) or 0.0),
                concept_stability=float(getattr(sign, "utility_score", 0.0)
                                        or 0.0),
                source_reliability=0.8, source_count=len(sources),
                modality_count=len(sources), recurrence=trace.supporting_count,
                rhythm_present=bool(rhythm.get("patterns")),
                quarantine_rate=0.0, contamination=bool(contamination_in),
                load_status=load_status, counter_count=trace.counter_count,
                supporting_count=trace.supporting_count,
                missing_evidence=trace.supporting_count == 0,
                operator_share=op_share)
            trace.uncertainty_state = uncertainty.to_dict()

            contamination = cfilter.evaluate(
                trace=trace, sign_sources=sources,
                sign_contamination=contamination_in,
                annotations=getattr(sign, "annotations", {}) or {})
            trace.contamination_findings = list(contamination.types)
            self.contamination_results.append(contamination.to_dict())

            outcome = outcome_by_sign.get(sid, "")
            trace.prediction_assessment = {"outcome": outcome} if outcome else {}
            self._apply_status(trace, contamination, uncertainty.uncertainty,
                               op_share, outcome)

            self.safety.validate_anticipation_evidence(
                operator_text_only=(set(sources) == {"operator_pulse"}
                                    and bool(sources)))
            self.cognition_memory.add(self._to_record(trace, outcome))
            self.traces.append(trace)

        self._run_readiness_gate()

    def _anticipations_by_sign(self) -> Dict[str, List[Any]]:
        out: Dict[str, List[Any]] = {}
        for a in self.anticipations:
            out.setdefault(a.sign_id, []).append(a)
        return out

    def _outcome_by_sign(self) -> Dict[str, str]:
        """Best (highest-ranked) assessed outcome per sign."""
        best: Dict[str, str] = {}
        anticipation_sign = {a.anticipation_id: a.sign_id
                             for a in self.anticipations}
        for o in self.prediction.get("outcomes", []):
            sid = anticipation_sign.get(o.get("anticipation_id"), "")
            cur = best.get(sid)
            if cur is None or _OUTCOME_RANK.get(o["outcome"], 0) > \
                    _OUTCOME_RANK.get(cur, 0):
                best[sid] = o["outcome"]
        return best

    def _apply_status(self, trace, contamination, uncertainty, op_share,
                      outcome) -> None:
        if contamination.contaminated:
            trace.status = CognitionTraceStatus.CONTAMINATED
        elif op_share >= 0.5:
            trace.status = CognitionTraceStatus.SUSPENDED
        elif contamination.is_source_artifact:
            trace.status = CognitionTraceStatus.SOURCE_ARTIFACT
        elif trace.counter_count > trace.supporting_count:
            trace.status = CognitionTraceStatus.SPURIOUS_RELATION
        elif outcome == "contradicted":
            trace.status = CognitionTraceStatus.WEAK
        elif uncertainty > self.max_uncertainty:
            trace.status = (CognitionTraceStatus.WEAK if uncertainty > 0.8
                            else CognitionTraceStatus.ACTIVE)
        elif self.allow_anticipation and outcome in ("matched",
                                                     "partially_matched"):
            trace.status = CognitionTraceStatus.USEFUL
        elif uncertainty <= self.max_uncertainty:
            trace.status = CognitionTraceStatus.STABLE
        else:
            trace.status = CognitionTraceStatus.ACTIVE

    def _to_record(self, trace, outcome) -> LiveCognitionRecord:
        return LiveCognitionRecord(
            trace_id=trace.trace_id, kind=trace.kind, status=trace.status,
            run_id=self.run_id, linked_sign_ids=list(trace.linked_sign_ids),
            linked_concept_ids=list(trace.linked_concept_ids),
            uncertainty=trace.uncertainty, prediction_outcome=outcome,
            supporting_refs=[e.ref for e in trace.supporting_evidence],
            contradicting_refs=[e.ref for e in trace.contradicting_evidence],
            contamination_findings=list(trace.contamination_findings))

    def _run_readiness_gate(self) -> None:
        contamination_summary = LiveCognitionContaminationFilter.summary(
            [self._mk_result(r) for r in self.contamination_results])
        self.readiness = LiveCognitionReadinessGate(
            max_uncertainty=self.max_uncertainty,
            min_prediction_utility=self.min_prediction_utility).evaluate(
            governance_passed=self.governance_result.get(
                "governance_passed", False),
            birth_certificate_present=self.birth_certificate_present,
            observation_stability_blocked=self.observation.get("blocked", False),
            concept_memory_present=self.concept_memory_present
            or bool(self.eligible_signs),
            sign_memory_present=bool(self.sign_input)
            or bool(self.eligible_signs),
            eligible_sign_count=len(self.eligible_signs),
            promoted_trace_count=self._promoted_count(),
            mean_uncertainty=self._mean_uncertainty(),
            prediction_utility=float(self.prediction.get(
                "prediction_utility", 0.0) or 0.0),
            prediction_contradicted=self._prediction_contradicted(),
            contamination_summary=contamination_summary,
            load=self.observation.get("load", {}),
            allow_anticipation=self.allow_anticipation,
            allow_internal_simulation=self.allow_internal_simulation).to_dict()

    @staticmethod
    def _mk_result(d: Dict[str, Any]):
        from .cognition_contamination_filter import (
            CognitionContaminationFinding, CognitionContaminationResult)

        r = CognitionContaminationResult(trace_id=d.get("trace_id", ""))
        for f in d.get("findings", []):
            r.findings.append(CognitionContaminationFinding(
                f.get("contamination_type", "unknown"), f.get("detail", ""),
                blocks_promotion=f.get("blocks_promotion", True)))
        return r

    # -- aggregates ---------------------------------------------------------

    def _counts(self) -> Dict[str, int]:
        def n(status):
            return sum(1 for t in self.traces if t.status == status)
        return {
            "trace_count": len(self.traces),
            "active_count": n(CognitionTraceStatus.ACTIVE)
            + n(CognitionTraceStatus.STABLE),
            "useful_count": n(CognitionTraceStatus.USEFUL),
            "rejected_count": n(CognitionTraceStatus.REJECTED),
            "contaminated_count": n(CognitionTraceStatus.CONTAMINATED),
            "weak_count": n(CognitionTraceStatus.WEAK),
            "spurious_count": n(CognitionTraceStatus.SPURIOUS_RELATION),
        }

    def _promoted_count(self) -> int:
        return sum(1 for t in self.traces if t.promoted)

    def _mean_uncertainty(self) -> float:
        if not self.traces:
            return 1.0
        return round(sum(t.uncertainty for t in self.traces)
                     / len(self.traces), 4)

    def _prediction_contradicted(self) -> bool:
        return int(self.prediction.get("live_prediction_contradicted_count", 0)
                   or 0) > int(self.prediction.get(
                       "live_prediction_matched_count", 0) or 0)

    def recommended_next_phase(self) -> str:
        if self.blocked:
            return "resolve_cognition_blockers"
        return self.readiness.get("recommended_next_phase",
                                  "continue_live_cognition")

    # -- result + integration views -----------------------------------------

    def _result(self) -> Dict[str, Any]:
        counts = self._counts()
        return {
            "refused": False, "run_id": self.run_id, "blocked": self.blocked,
            "blockers": list(self.blockers),
            "eligible_sign_count": len(self.eligible_signs),
            "cognition_trace_count": counts["trace_count"],
            "anticipation_count": len(self.anticipations),
            "internal_simulation_count": len(self.simulations),
            "prediction_matched_count": int(self.prediction.get(
                "live_prediction_matched_count", 0) or 0),
            "prediction_contradicted_count": int(self.prediction.get(
                "live_prediction_contradicted_count", 0) or 0),
            "cognition_readiness_status": self.readiness.get(
                "cognition_readiness_status"),
            "recommended_next_phase": self.recommended_next_phase(),
            "record": self.record.get("markdown"),
            "report": self.reports.get("markdown"),
            "cognition_memory": (self.cognition_memory.memory_path
                                 if self.cognition_memory else None),
        }

    def cognition_status(self) -> Dict[str, Any]:
        counts = self._counts()
        return {
            "live_cognition_enabled": True,
            "cognition_run_id": self.run_id,
            "live_cognition_blocked": self.blocked,
            "live_eligible_sign_count": len(self.eligible_signs),
            "live_cognition_trace_count": counts["trace_count"],
            "live_active_trace_count": counts["active_count"],
            "live_useful_trace_count": counts["useful_count"],
            "live_rejected_trace_count": counts["rejected_count"],
            "live_contaminated_trace_count": counts["contaminated_count"],
            "live_anticipation_count": len(self.anticipations),
            "live_internal_simulation_count": len(self.simulations),
            "live_prediction_assessment_count": int(self.prediction.get(
                "live_prediction_assessment_count", 0) or 0),
            "live_prediction_matched_count": int(self.prediction.get(
                "live_prediction_matched_count", 0) or 0),
            "live_prediction_contradicted_count": int(self.prediction.get(
                "live_prediction_contradicted_count", 0) or 0),
            "live_uncertainty_mean": self._mean_uncertainty(),
            "live_relation_traversal_path_count": self.traversal.get(
                "path_count", 0),
            "live_cognition_readiness_status": self.readiness.get(
                "cognition_readiness_status", "inconclusive"),
            "latest_cognition_memory_path": (self.cognition_memory.memory_path
                                             if self.cognition_memory else None),
            "latest_cognition_report_path": self.reports.get("markdown"),
            "recommended_next_phase": self.recommended_next_phase(),
            "live_cognition_safety_block_count": self.safety.rejected_count,
            "enables_action": False, "enables_action_reaction": False,
            "enables_developmental_autonomy": False,
            "enables_self_boundary": False,
            "signs_are_language_understanding": False,
            "traces_prove_reasoning": False,
            "starts_feeders": False, "controls_hardware": False,
            "accesses_network": False, "runs_git": False,
        }

    def snapshot(self) -> Dict[str, Any]:
        return self.cognition_status()

    def next_phase_recommendations(self) -> List[Dict[str, str]]:
        return [{"phase": self.recommended_next_phase(),
                 "detail": "advisory next phase from the cognition run; never "
                           "started automatically"}]

    def research_cycle_update(self) -> Dict[str, Any]:
        phase = self.recommended_next_phase()
        if phase == "ready_for_live_self_boundary_tracking":
            action = "Prepare live self-boundary tracking protocol"
        elif self.blocked or phase.startswith(("resolve", "fix")) or phase in (
                "reduce_operator_text", "collect_more_signs",
                "improve_prediction_assessment", "pause_live_learning"):
            action = "Resolve cognition blockers"
        else:
            action = "Continue live cognition observation"
        return {"cognition_evidence_recorded": True, "next_action": action,
                "operational_only": True}

    def scientific_claims_update(self) -> Dict[str, Any]:
        counts = self._counts()
        return {
            "useful_trace_count": counts["useful_count"],
            "evidence_kind": "operational_sign_based_anticipation_record",
            "trace_only_run": not self.allow_anticipation,
            "inconclusive_for_consciousness": True,
            "blocks_reasoning_proof_interpretation": True,
            "blocks_language_understanding_interpretation": True,
            "blocks_consciousness_life_agency_interpretation": True,
        }

    def write_artifacts(self) -> Dict[str, Any]:
        from .cognition_record import LiveCognitionRecordBuilder
        from .reports import LiveCognitionReportBuilder

        if self.cognition_memory is None:
            self.cognition_memory = LiveCognitionMemory(
                state_dir=self.state_dir).load()
        self._write_state()
        if not self.dry_run:
            self.cognition_memory.write()
        self.record = LiveCognitionRecordBuilder(self).write()
        self.reports = LiveCognitionReportBuilder(self).write()
        return {"record": self.record, "reports": self.reports}

    def _write_state(self) -> None:
        base = os.path.join(self.state_dir, "cognition")

        def dump(subdir: str, name: str, obj: Any) -> None:
            path = os.path.join(base, subdir, name)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(obj, fh, indent=2, default=str)

        dump("anticipations", f"{self.run_id}.json",
             {"anticipations": [a.to_dict() for a in self.anticipations]})
        dump("uncertainty", f"{self.run_id}.json",
             {"mean_uncertainty": self._mean_uncertainty(),
              "traces": [{"trace_id": t.trace_id,
                          "uncertainty": t.uncertainty} for t in self.traces]})
        dump("simulations", f"{self.run_id}.json",
             {"simulations": [s.to_dict() for s in self.simulations]})
        dump("predictions", f"{self.run_id}.json", self.prediction)
        dump("contamination", f"{self.run_id}.json",
             {"results": self.contamination_results})
        for t in self.traces:
            dump("traces", f"{t.trace_id}.json", t.to_dict())
        dump("index", f"{self.run_id}.json", self.cognition_status())
