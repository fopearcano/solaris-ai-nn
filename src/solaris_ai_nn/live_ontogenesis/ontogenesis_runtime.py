"""First live ontogenesis runtime -- bounded, read-only, conservative, no learning.

:class:`FirstLiveOntogenesisRuntime` runs the first live ontogenesis phase: it loads
governance, the birth certificate, and the post-birth observation reports (including
the stability gate, source diet, and overload/deprivation load), re-reads the local
inbox through the Prompt 67 validator, extracts feature vectors, tracks recurrence,
builds proto-concept candidates with supporting and contradicting evidence, scores
stability conservatively, filters contamination, gates concept birth, updates
append-only concept memory, and writes an ontogenesis record and reports.

It is bounded and local-only. It does not enable semiogenesis, action-reaction
learning, or developmental autonomy; it does not start/stop/configure feeders,
control hardware, access the network/shell/browser/OS/camera/microphone, call
Git/GitHub, execute commands, or modify source; it does not treat sensory text as a
command or human labels / debug gloss as ground truth; and it makes no claim of
consciousness, sentience, life, personhood, agency, free will, emotion, feeling,
understanding, self-awareness, or subjective experience.
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
from ..live_observation.observation_window import parse_timestamp
from .concept_birth_gate import (
    ConceptBirthGateStatus,
    LiveConceptBirthGate,
)
from .concept_memory import LiveConceptMemory, LiveConceptRecord
from .contamination_filter import LiveOntogenesisContaminationFilter
from .feature_extraction import LiveFeatureExtractor
from .ontogenesis_profile import get_ontogenesis_profile
from .proto_concept_candidate import (
    LiveProtoConceptCandidate,
    ProtoConceptCandidateStatus,
)
from .recurrence_tracker import LiveRecurrenceTracker
from .safety import LiveOntogenesisSafetyValidator
from .stability_scoring import StabilityScorer

_SUBDIRS = ("candidates", "concepts", "recurrence", "stability",
            "contamination", "reports", "index")

_STATUS_MAP = {
    ConceptBirthGateStatus.BORN: ProtoConceptCandidateStatus.BORN,
    ConceptBirthGateStatus.STABLE_CANDIDATE:
        ProtoConceptCandidateStatus.STABLE_CANDIDATE,
    ConceptBirthGateStatus.DEFER: ProtoConceptCandidateStatus.STABILIZING,
    ConceptBirthGateStatus.REJECT: ProtoConceptCandidateStatus.REJECTED,
    ConceptBirthGateStatus.CONTAMINATED:
        ProtoConceptCandidateStatus.CONTAMINATED,
    ConceptBirthGateStatus.INCONCLUSIVE:
        ProtoConceptCandidateStatus.INCONCLUSIVE,
}


@dataclass
class FirstLiveOntogenesisRuntime:
    """Bounded, local, read-only first live ontogenesis runtime (no learning)."""

    state_dir: str = ".solaris_ai_nn_live"
    alpha_state_dir: str = ".solaris_ai_nn_alpha"
    profile: Optional[str] = None
    max_runtime_s: float = 180.0
    max_events: int = 2000
    max_files: int = 100
    max_candidates: int = 200
    min_recurrence: int = 3
    min_stability: float = 0.6
    report_only: bool = False
    dry_run: bool = False
    strict: bool = False
    require_governance: bool = True
    require_birth_certificate: bool = True
    require_observation_stability: bool = True
    allow_candidate_only: bool = True
    allow_limited_birth: bool = False
    require_claimguard: bool = False
    operator_note: str = ""

    safety: LiveOntogenesisSafetyValidator = field(
        default_factory=LiveOntogenesisSafetyValidator, init=False)
    ontogenesis_profile: Any = field(default=None, init=False)
    governance: Any = field(default=None, init=False)
    governance_result: Dict[str, Any] = field(default_factory=dict, init=False)
    feeders: Any = field(default=None, init=False)
    quarantine: Any = field(default=None, init=False)
    birth_certificate_present: bool = field(default=False, init=False)
    observation: Dict[str, Any] = field(default_factory=dict, init=False)
    run_id: str = field(default="", init=False)
    blocked: bool = field(default=False, init=False)
    blockers: List[str] = field(default_factory=list, init=False)
    warnings: List[str] = field(default_factory=list, init=False)

    accepted_events: List[Dict[str, Any]] = field(default_factory=list,
                                                  init=False)
    feature_result: Dict[str, Any] = field(default_factory=dict, init=False)
    recurrence_summary: Dict[str, Any] = field(default_factory=dict, init=False)
    candidates: List[LiveProtoConceptCandidate] = field(default_factory=list,
                                                        init=False)
    stability_scores: Dict[str, Dict[str, Any]] = field(default_factory=dict,
                                                        init=False)
    contamination_results: List[Dict[str, Any]] = field(default_factory=list,
                                                        init=False)
    birth_gate_results: List[Dict[str, Any]] = field(default_factory=list,
                                                     init=False)
    concept_memory: Any = field(default=None, init=False)
    record: Dict[str, Any] = field(default_factory=dict, init=False)
    reports: Dict[str, Any] = field(default_factory=dict, init=False)
    _vectors: List[Any] = field(default_factory=list, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.state_dir == self.alpha_state_dir:
            self.state_dir = ".solaris_ai_nn_live"
        self.ontogenesis_profile = get_ontogenesis_profile(self.profile)
        self.min_recurrence = self.min_recurrence \
            or self.ontogenesis_profile.min_recurrence
        self.min_stability = self.min_stability \
            or self.ontogenesis_profile.min_stability
        self.run_id = f"onto_{int(time.time())}"
        if not self.max_runtime_s:
            self._refused = True

    # -- state layout -------------------------------------------------------

    def initialize(self) -> Dict[str, Any]:
        base = os.path.join(self.state_dir, "ontogenesis")
        os.makedirs(base, exist_ok=True)
        created = []
        for name in _SUBDIRS:
            path = os.path.join(base, name)
            existed = os.path.isdir(path)
            os.makedirs(path, exist_ok=True)
            created.append({"name": name, "existed": existed})
        return {"ontogenesis_dir": base, "directories": created,
                "deletes_state": False}

    # -- doctor -------------------------------------------------------------

    def run_doctor(self) -> Dict[str, Any]:
        self.initialize()
        self.governance = GovernanceValidator().load(self.state_dir)
        self.governance_result = GovernanceValidator().validate(self.governance)
        cert = self._find_birth_certificate()
        observation = self._load_observation()
        bounded = self.safety.validate_bounded(self.max_runtime_s).safe
        blockers = list(self.governance_result.get("blockers", []))
        if self.require_birth_certificate and not cert:
            blockers.append("birth certificate required but not present")
        if self.require_observation_stability and observation.get("blocked"):
            blockers.append("observation stability gate is blocked")
        if self.require_observation_stability and not observation.get("present"):
            blockers.append("observation reports required but not present")
        if not bounded:
            blockers.append("runtime is unbounded")
        return {
            "governance_status": self.governance_result.get("governance_status"),
            "governance_passed": self.governance_result.get("governance_passed"),
            "birth_certificate_present": bool(cert),
            "observation_present": observation.get("present"),
            "observation_stability_blocked": observation.get("blocked"),
            "bounded": bounded, "blockers": blockers, "passed": not blockers,
            "note": "live ontogenesis doctor validates governance, birth "
                    "certificate, observation stability, and bounded runtime "
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
        self.birth_certificate_present = bool(self._find_birth_certificate())
        self.observation = self._load_observation()

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

        if not self.blocked:
            self._read_events()
            self._analyze()
        else:
            # Still emit empty analysis structures + concept memory.
            self.concept_memory = LiveConceptMemory(
                state_dir=self.state_dir).load()

        if not self.dry_run:
            self.write_artifacts()
        return self._result()

    def _find_birth_certificate(self) -> str:
        cert_dir = os.path.join(self.state_dir, "certificates")
        if not os.path.isdir(cert_dir):
            return ""
        for name in sorted(os.listdir(cert_dir)):
            if name.endswith(".md") or name.endswith(".json"):
                return os.path.join(cert_dir, name)
        return ""

    def _load_observation(self) -> Dict[str, Any]:
        """Load the latest post-birth observation report (read-only)."""
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
            "stability": stability,
            "stability_status": stability.get("live_stability_status",
                                              "unknown"),
            "load": sections.get("load", {}) or {},
            "source_diet": sections.get("source_diet", {}) or {},
            "source_health": sections.get("source_health", {}) or {},
            "rhythm": sections.get("rhythm", {}) or {},
            "metabolism": sections.get("metabolism", {}) or {},
        }

    def _read_events(self) -> None:
        from ..live_birth.birth_profile import ALLOWED_FIRST_BIRTH_SOURCES

        allowed = (self.governance.allowed_sources
                   or list(ALLOWED_FIRST_BIRTH_SOURCES))
        validator = LiveEventValidator(
            allowed_sources=allowed,
            registered_sources=[r.source_id for r in self.feeders.records]
            if self.feeders else [],
            strict=self.strict)
        spool = LiveInboxSpool(
            inbox_dir=os.path.join(self.state_dir, "inbox"),
            validator=validator, quarantine=self.quarantine,
            max_files=self.max_files, max_events=self.max_events,
            strict=self.strict)
        read = spool.read()
        for env in read.accepted_envelopes:
            if env.event is None:
                continue
            d = env.event.to_dict()
            d["source_kind"] = "live_readonly"
            self.accepted_events.append(d)

    def analyze_events(self, events: List[Dict[str, Any]], *,
                       observation: Optional[Dict[str, Any]] = None,
                       ) -> "FirstLiveOntogenesisRuntime":
        """Run the analysis pipeline directly on event dicts (component demos).

        This bypasses the inbox/governance/observation *gating* (callers supply
        already-trusted event dicts) but applies the same feature extraction,
        recurrence, stability, contamination, and conservative birth gate. It is
        used by the component demos and tests; the full ``run`` path always reads
        validated events and honours the gates.
        """
        self.accepted_events = list(events)
        self.observation = observation or {
            "present": True, "blocked": False, "stability": {}, "load": {},
            "source_diet": {}, "source_health": {}, "rhythm": {},
            "metabolism": {}}
        if not self.governance_result:
            self.governance_result = {"governance_passed": True}
        self.birth_certificate_present = True
        self._analyze()
        return self

    def _analyze(self) -> None:
        obs = self.observation
        load_status = obs.get("load", {}).get("load_status", "")

        # Feature extraction.
        extractor = LiveFeatureExtractor()
        fr = extractor.extract(accepted_events=self.accepted_events,
                               rhythm=obs.get("rhythm"),
                               load_status=load_status)
        self._vectors = fr.vectors
        self.feature_result = fr.to_dict()
        vectors_by_event = {v.event_id: v for v in self._vectors}

        # Recurrence.
        tracker = LiveRecurrenceTracker(min_recurrence=self.min_recurrence)
        patterns = tracker.track(self._vectors)
        self.recurrence_summary = LiveRecurrenceTracker.summary(patterns)

        # Candidates from recurrence patterns.
        self._build_candidates(patterns, vectors_by_event)

        # Stability + contamination + birth gate per candidate.
        scorer = StabilityScorer()
        cfilter = LiveOntogenesisContaminationFilter()
        allow_birth = (self.allow_limited_birth
                       or self.ontogenesis_profile.allow_limited_birth)
        gate = LiveConceptBirthGate(min_recurrence=self.min_recurrence,
                                    min_stability=self.min_stability,
                                    allow_birth=allow_birth)
        reliability = self._source_reliability(obs.get("source_health", {}))

        self.concept_memory = LiveConceptMemory(
            state_dir=self.state_dir).load()

        for cand in self.candidates:
            strength = self._pattern_strength(cand.feature_signature, patterns)
            rel = max((reliability.get(s, 0.7)
                       for s in cand.source_distribution), default=0.7)
            score = scorer.score(candidate=cand, recurrence_strength=strength,
                                  source_reliability=rel)
            cand.stability_score = score.score
            self.stability_scores[cand.candidate_id] = score.to_dict()

            contamination = cfilter.evaluate(
                candidate=cand, vectors_by_event=vectors_by_event,
                source_diet=obs.get("source_diet", {}))
            cand.contamination_findings = [
                f.contamination_type for f in contamination.findings]
            self.contamination_results.append(contamination.to_dict())

            gate_result = gate.evaluate(
                candidate=cand, stability_score=score.score,
                contamination=contamination,
                governance_passed=self.governance_result.get(
                    "governance_passed", False),
                birth_certificate_present=self.birth_certificate_present,
                observation_stability_blocked=obs.get("blocked", False),
                source_diet=obs.get("source_diet", {}),
                load=obs.get("load", {}))
            cand.birth_gate_result = gate_result.to_dict()
            self.birth_gate_results.append(gate_result.to_dict())
            self._apply_status(cand, contamination, gate_result)

            # Honour the single-event / operator-only / gloss-only safety rule.
            self.safety.validate_birth_evidence(
                recurrence_count=cand.recurrence_count,
                operator_text_only=cand.operator_only,
                debug_gloss_only=False,
                contaminated=contamination.contaminated)

            self.concept_memory.add(self._to_record(cand))

    def _build_candidates(self, patterns, vectors_by_event) -> None:
        ts_by_event = {ev.get("event_id", ""): ev.get("timestamp_utc", "")
                       for ev in self.accepted_events}
        # Counterevidence: events at the same (source, channel) with a different
        # signature challenge a candidate's specificity at that channel.
        sig_by_channel: Dict[str, set] = {}
        for v in self._vectors:
            sig_by_channel.setdefault((v.source_id, v.channel), set()).add(
                v.feature_signature)

        for i, pattern in enumerate(patterns):
            if pattern.count < 1:
                continue
            if len(self.candidates) >= self.max_candidates:
                self.warnings.append("max candidates reached; some patterns "
                                     "were not turned into candidates")
                break
            cand = LiveProtoConceptCandidate(
                candidate_id=f"{self.run_id}_c{i}",
                feature_signature=pattern.feature_signature,
                source_distribution=dict(pattern.source_distribution),
                modality_distribution=dict(pattern.modality_distribution),
                recurrence_count=pattern.count,
                absence_windows=pattern.absence_count)
            stamps = []
            for ev_id in pattern.event_ids:
                vec = vectors_by_event.get(ev_id)
                detail = ("noisy" if (vec and vec.is_noisy) else "")
                cand.add_support(ev_id, vec.source_id if vec else "", detail)
                ts = ts_by_event.get(ev_id, "")
                t = parse_timestamp(ts)
                if t is not None:
                    stamps.append((t, ts))
            if stamps:
                stamps.sort()
                cand.first_seen = stamps[0][1]
                cand.last_seen = stamps[-1][1]
            # Counterevidence from divergent signatures at the same channel.
            for v in self._vectors:
                key = (v.source_id, v.channel)
                if v.feature_signature != pattern.feature_signature \
                        and pattern.feature_signature in sig_by_channel.get(
                            key, set()):
                    cand.add_counter(v.event_id, v.source_id,
                                     "divergent payload at same channel")
            cand.limitations.extend(pattern.contamination_risk)
            self.candidates.append(cand)

    def _apply_status(self, cand, contamination, gate_result) -> None:
        if contamination.is_source_artifact and not gate_result.born:
            cand.status = ProtoConceptCandidateStatus.SOURCE_ARTIFACT
        elif gate_result.status.startswith("blocked_by_"):
            cand.status = ProtoConceptCandidateStatus.SUSPENDED
        else:
            cand.status = _STATUS_MAP.get(
                gate_result.status, ProtoConceptCandidateStatus.INCONCLUSIVE)
        # Weak: passed gate prerequisites but low stability + weak recurrence.
        if cand.status in (ProtoConceptCandidateStatus.STABILIZING,
                           ProtoConceptCandidateStatus.INCONCLUSIVE) \
                and cand.stability_score < 0.35:
            cand.status = ProtoConceptCandidateStatus.WEAK

    def _to_record(self, cand) -> LiveConceptRecord:
        return LiveConceptRecord(
            concept_id=cand.candidate_id,
            feature_signature=cand.feature_signature, status=cand.status,
            run_id=self.run_id, stability_score=cand.stability_score,
            recurrence_count=cand.recurrence_count,
            source_distribution=dict(cand.source_distribution),
            supporting_event_ids=[e.event_id for e in cand.supporting_events],
            contradicting_event_ids=[
                e.event_id for e in cand.contradicting_events],
            contamination_findings=list(cand.contamination_findings),
            birth_gate_status=cand.birth_gate_result.get(
                "concept_birth_gate_status", ""))

    @staticmethod
    def _pattern_strength(signature: str, patterns) -> str:
        for p in patterns:
            if p.feature_signature == signature:
                return p.strength
        return "none"

    @staticmethod
    def _source_reliability(source_health: Dict[str, Any]) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for s in source_health.get("sources", []) or []:
            out[s.get("source_id", "")] = float(
                s.get("reliability_estimate", 0.7) or 0.7)
        return out

    # -- result + integration views -----------------------------------------

    def _counts(self) -> Dict[str, int]:
        def n(status):
            return sum(1 for c in self.candidates if c.status == status)
        return {
            "candidate_count": len(self.candidates),
            "stable_candidate_count": n(
                ProtoConceptCandidateStatus.STABLE_CANDIDATE),
            "born_count": n(ProtoConceptCandidateStatus.BORN),
            "rejected_count": n(ProtoConceptCandidateStatus.REJECTED),
            "contaminated_count": n(ProtoConceptCandidateStatus.CONTAMINATED),
            "source_artifact_count": n(
                ProtoConceptCandidateStatus.SOURCE_ARTIFACT),
            "suspended_count": n(ProtoConceptCandidateStatus.SUSPENDED),
            "weak_count": n(ProtoConceptCandidateStatus.WEAK),
        }

    def recommended_next_phase(self) -> str:
        if self.blocked:
            return "fix_contamination" if any(
                "contam" in b for b in self.blockers) else \
                "fix_ontogenesis_blockers"
        counts = self._counts()
        contaminated = sum(1 for r in self.contamination_results
                           if r.get("contaminated"))
        diet = self.observation.get("source_diet", {})
        if diet.get("balance") in ("operator_pulse_dominant",
                                   "human_text_dominant"):
            return "reduce_operator_text"
        if contaminated:
            return "fix_contamination"
        if counts["born_count"] >= 2:
            return "ready_for_live_semiogenesis"
        if counts["stable_candidate_count"] >= 1 or counts["born_count"] >= 1:
            return "continue_ontogenesis"
        if len(self.accepted_events) < self.min_recurrence:
            return "collect_more_events"
        return "continue_ontogenesis"

    def _result(self) -> Dict[str, Any]:
        counts = self._counts()
        return {
            "refused": False, "run_id": self.run_id, "blocked": self.blocked,
            "blockers": list(self.blockers),
            "accepted_event_count": len(self.accepted_events),
            "feature_vector_count": self.feature_result.get(
                "live_feature_vector_count", 0),
            "candidate_count": counts["candidate_count"],
            "born_proto_concept_count": counts["born_count"],
            "stable_candidate_count": counts["stable_candidate_count"],
            "recommended_next_phase": self.recommended_next_phase(),
            "record": self.record.get("markdown"),
            "report": self.reports.get("markdown"),
            "concept_memory": (self.concept_memory.memory_path
                               if self.concept_memory else None),
        }

    def ontogenesis_status(self) -> Dict[str, Any]:
        counts = self._counts()
        return {
            "live_ontogenesis_enabled": True,
            "ontogenesis_run_id": self.run_id,
            "live_ontogenesis_blocked": self.blocked,
            "live_feature_vector_count": self.feature_result.get(
                "live_feature_vector_count", 0),
            "live_recurrence_pattern_count": self.recurrence_summary.get(
                "live_recurrence_pattern_count", 0),
            "live_candidate_count": counts["candidate_count"],
            "live_stable_candidate_count": counts["stable_candidate_count"],
            "live_born_proto_concept_count": counts["born_count"],
            "live_rejected_candidate_count": counts["rejected_count"],
            "live_contaminated_candidate_count": counts["contaminated_count"],
            "live_source_artifact_candidate_count": counts[
                "source_artifact_count"],
            "live_birth_gate_status": self._overall_gate_status(),
            "latest_concept_memory_path": (
                self.concept_memory.memory_path if self.concept_memory
                else None),
            "latest_ontogenesis_report_path": self.reports.get("markdown"),
            "recommended_next_phase": self.recommended_next_phase(),
            "live_ontogenesis_safety_block_count": self.safety.rejected_count,
            "enables_semiogenesis": False, "enables_action_reaction": False,
            "enables_developmental_autonomy": False,
            "starts_feeders": False, "controls_hardware": False,
            "accesses_network": False, "runs_git": False,
        }

    def _overall_gate_status(self) -> str:
        if self.blocked:
            return "blocked"
        counts = self._counts()
        if counts["born_count"]:
            return "born"
        if counts["stable_candidate_count"]:
            return "stable_candidate"
        if counts["contaminated_count"]:
            return "contaminated"
        return "inconclusive"

    def snapshot(self) -> Dict[str, Any]:
        return self.ontogenesis_status()

    def next_phase_recommendations(self) -> List[Dict[str, str]]:
        return [{"phase": self.recommended_next_phase(),
                 "detail": "advisory next phase from the ontogenesis run; never "
                           "started automatically"}]

    # -- integrations (optional; read-only / record-only) -------------------

    def research_cycle_update(self) -> Dict[str, Any]:
        phase = self.recommended_next_phase()
        if phase == "ready_for_live_semiogenesis":
            action = "Prepare live semiogenesis protocol"
        elif self.blocked or phase.startswith("fix") or phase in (
                "reduce_operator_text", "improve_source_diet"):
            action = "Resolve ontogenesis blockers"
        else:
            action = "Continue live ontogenesis observation"
        return {"ontogenesis_evidence_recorded": True, "next_action": action,
                "operational_only": True}

    def scientific_claims_update(self) -> Dict[str, Any]:
        counts = self._counts()
        return {
            "born_proto_concept_count": counts["born_count"],
            "evidence_kind": "operational_feature_stability_record",
            "candidate_only_run": not (self.allow_limited_birth
                                       or self.ontogenesis_profile
                                       .allow_limited_birth),
            "inconclusive_for_consciousness": True,
            "blocks_consciousness_life_agency_interpretation": True,
        }

    def write_artifacts(self) -> Dict[str, Any]:
        from .ontogenesis_record import LiveOntogenesisRecordBuilder
        from .reports import LiveOntogenesisReportBuilder

        if self.concept_memory is None:
            self.concept_memory = LiveConceptMemory(
                state_dir=self.state_dir).load()
        self._write_state()
        if not self.dry_run:
            self.concept_memory.write()
        self.record = LiveOntogenesisRecordBuilder(self).write()
        self.reports = LiveOntogenesisReportBuilder(self).write()
        return {"record": self.record, "reports": self.reports}

    def _write_state(self) -> None:
        base = os.path.join(self.state_dir, "ontogenesis")

        def dump(subdir: str, name: str, obj: Any) -> None:
            path = os.path.join(base, subdir, name)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(obj, fh, indent=2, default=str)

        dump("recurrence", f"{self.run_id}.json", self.recurrence_summary)
        dump("stability", f"{self.run_id}.json", self.stability_scores)
        dump("contamination", f"{self.run_id}.json",
             {"results": self.contamination_results})
        for cand in self.candidates:
            dump("candidates", f"{cand.candidate_id}.json", cand.to_dict())
        dump("index", f"{self.run_id}.json", self.ontogenesis_status())
