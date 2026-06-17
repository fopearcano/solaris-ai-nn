"""First live semiogenesis runtime -- bounded, read-only, conservative, no cognition.

:class:`FirstLiveSemiogenesisRuntime` runs the first live semiogenesis phase: it
loads governance, the birth certificate, the post-birth observation reports, and the
live ontogenesis report + concept memory; selects eligible (born/stable,
uncontaminated) proto-concepts; generates private sign candidates; assesses sign
utility; builds private-syntax relations; filters contamination; gates sign birth;
updates append-only sign memory; and writes a semiogenesis record and reports.

It is bounded and local-only. It does not enable full cognition, action-reaction
learning, or developmental autonomy; it does not start/stop/configure feeders,
control hardware, access the network/shell/browser/OS/camera/microphone, call
Git/GitHub, execute commands, or modify source; it does not treat sensory text as a
command, human labels / debug gloss as ground truth, or the operator pulse as
teaching; and it makes no claim of language understanding, consciousness, sentience,
life, personhood, agency, free will, emotion, feeling, self-awareness, or subjective
experience.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..live_birth.governance import GovernanceValidator
from .concept_input import ConceptInputLoader
from .private_syntax import PrivateSyntaxBuilder
from .semiogenesis_profile import get_semiogenesis_profile
from .sign_birth_gate import LiveSignBirthGate, SignBirthGateStatus
from .sign_candidate import SignCandidateStatus
from .sign_contamination_filter import LiveSignContaminationFilter
from .sign_generator import LivePrivateSignGenerator
from .sign_memory import LiveSignMemory, LiveSignRecord
from .sign_utility import LiveSignUtilityAssessment
from .safety import LiveSemiogenesisSafetyValidator

_SUBDIRS = ("candidates", "signs", "syntax", "utility", "contamination",
            "reports", "index")

_STATUS_MAP = {
    SignBirthGateStatus.BORN: SignCandidateStatus.BORN,
    SignBirthGateStatus.STABLE_CANDIDATE: SignCandidateStatus.STABLE_CANDIDATE,
    SignBirthGateStatus.DEFER: SignCandidateStatus.STABILIZING,
    SignBirthGateStatus.REJECT: SignCandidateStatus.REJECTED,
    SignBirthGateStatus.CONTAMINATED: SignCandidateStatus.CONTAMINATED,
    SignBirthGateStatus.BLOCKED_BY_LABEL_DEPENDENCE:
        SignCandidateStatus.LABEL_DEPENDENT,
    SignBirthGateStatus.BLOCKED_BY_DEBUG_GLOSS_DEPENDENCE:
        SignCandidateStatus.GLOSS_DEPENDENT,
    SignBirthGateStatus.BLOCKED_BY_OPERATOR_DEPENDENCE:
        SignCandidateStatus.OPERATOR_DEPENDENT,
    SignBirthGateStatus.BLOCKED_BY_SAFETY: SignCandidateStatus.CONTAMINATED,
    SignBirthGateStatus.BLOCKED_BY_FORBIDDEN_SOURCE:
        SignCandidateStatus.CONTAMINATED,
    SignBirthGateStatus.BLOCKED_BY_SOURCE_ARTIFACT:
        SignCandidateStatus.SOURCE_ARTIFACT,
    SignBirthGateStatus.BLOCKED_BY_LOW_UTILITY: SignCandidateStatus.WEAK,
    SignBirthGateStatus.INCONCLUSIVE: SignCandidateStatus.INCONCLUSIVE,
}


@dataclass
class FirstLiveSemiogenesisRuntime:
    """Bounded, local, read-only first live semiogenesis runtime (no cognition)."""

    state_dir: str = ".solaris_ai_nn_live"
    alpha_state_dir: str = ".solaris_ai_nn_alpha"
    profile: Optional[str] = None
    max_runtime_s: float = 180.0
    max_concepts: int = 200
    max_signs: int = 200
    min_utility: float = 0.6
    report_only: bool = False
    dry_run: bool = False
    strict: bool = False
    require_governance: bool = True
    require_birth_certificate: bool = True
    require_observation_stability: bool = True
    require_live_concepts: bool = True
    allow_candidate_only: bool = True
    allow_limited_birth: bool = False
    require_claimguard: bool = False
    operator_note: str = ""

    safety: LiveSemiogenesisSafetyValidator = field(
        default_factory=LiveSemiogenesisSafetyValidator, init=False)
    semiogenesis_profile: Any = field(default=None, init=False)
    governance: Any = field(default=None, init=False)
    governance_result: Dict[str, Any] = field(default_factory=dict, init=False)
    birth_certificate_present: bool = field(default=False, init=False)
    observation: Dict[str, Any] = field(default_factory=dict, init=False)
    concept_input: Dict[str, Any] = field(default_factory=dict, init=False)
    run_id: str = field(default="", init=False)
    blocked: bool = field(default=False, init=False)
    blockers: List[str] = field(default_factory=list, init=False)
    warnings: List[str] = field(default_factory=list, init=False)

    eligible_concepts: List[Any] = field(default_factory=list, init=False)
    candidates: List[Any] = field(default_factory=list, init=False)
    utility_scores: Dict[str, Dict[str, Any]] = field(default_factory=dict,
                                                      init=False)
    contamination_results: List[Dict[str, Any]] = field(default_factory=list,
                                                        init=False)
    birth_gate_results: List[Dict[str, Any]] = field(default_factory=list,
                                                     init=False)
    syntax_graph: Dict[str, Any] = field(default_factory=dict, init=False)
    sign_memory: Any = field(default=None, init=False)
    record: Dict[str, Any] = field(default_factory=dict, init=False)
    reports: Dict[str, Any] = field(default_factory=dict, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.state_dir == self.alpha_state_dir:
            self.state_dir = ".solaris_ai_nn_live"
        self.semiogenesis_profile = get_semiogenesis_profile(self.profile)
        self.min_utility = self.min_utility \
            or self.semiogenesis_profile.min_utility
        self.run_id = f"semio_{int(time.time())}"
        if not self.max_runtime_s:
            self._refused = True

    # -- state layout -------------------------------------------------------

    def initialize(self) -> Dict[str, Any]:
        base = os.path.join(self.state_dir, "semiogenesis")
        os.makedirs(base, exist_ok=True)
        created = []
        for name in _SUBDIRS:
            path = os.path.join(base, name)
            existed = os.path.isdir(path)
            os.makedirs(path, exist_ok=True)
            created.append({"name": name, "existed": existed})
        return {"semiogenesis_dir": base, "directories": created,
                "deletes_state": False}

    # -- doctor -------------------------------------------------------------

    def run_doctor(self) -> Dict[str, Any]:
        self.initialize()
        self.governance = GovernanceValidator().load(self.state_dir)
        self.governance_result = GovernanceValidator().validate(self.governance)
        cert = self._find_birth_certificate()
        observation = self._load_observation()
        concept_input = ConceptInputLoader().load(self.state_dir).to_dict()
        bounded = self.safety.validate_bounded(self.max_runtime_s).safe
        blockers = list(self.governance_result.get("blockers", []))
        if self.require_birth_certificate and not cert:
            blockers.append("birth certificate required but not present")
        if self.require_observation_stability and observation.get("blocked"):
            blockers.append("observation stability gate is blocked")
        if self.require_live_concepts and not concept_input.get(
                "live_eligible_concept_count"):
            blockers.append("no eligible live proto-concepts present")
        if not bounded:
            blockers.append("runtime is unbounded")
        return {
            "governance_status": self.governance_result.get("governance_status"),
            "governance_passed": self.governance_result.get("governance_passed"),
            "birth_certificate_present": bool(cert),
            "observation_stability_blocked": observation.get("blocked"),
            "eligible_concept_count": concept_input.get(
                "live_eligible_concept_count", 0),
            "bounded": bounded, "blockers": blockers, "passed": not blockers,
            "note": "live semiogenesis doctor validates governance, birth "
                    "certificate, observation stability, live concepts, and "
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
        concept_result = ConceptInputLoader().load(self.state_dir)
        self.concept_input = concept_result.to_dict()
        self.eligible_concepts = concept_result.eligible

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
        if self.require_live_concepts and not self.eligible_concepts:
            self.blocked = True
            self.blockers.append("no eligible live proto-concepts present")

        if not self.blocked:
            self._analyze(self.eligible_concepts)
        else:
            self.sign_memory = LiveSignMemory(state_dir=self.state_dir).load()

        if not self.dry_run:
            self.write_artifacts()
        return self._result()

    def analyze_concepts(self, concepts: List[Any], *,
                         observation: Optional[Dict[str, Any]] = None,
                         requested_tokens: Optional[Dict[str, str]] = None,
                         ) -> "FirstLiveSemiogenesisRuntime":
        """Run the pipeline directly on concept inputs (component demos / tests)."""
        self.eligible_concepts = list(concepts)
        self.observation = observation or {
            "present": True, "blocked": False, "stability": {}, "load": {},
            "source_diet": {}}
        if not self.governance_result:
            self.governance_result = {"governance_passed": True}
        self.birth_certificate_present = True
        # The caller supplied already-loaded concept inputs, so ontogenesis is
        # treated as present for the gate (the full run path checks the file).
        if not self.concept_input:
            self.concept_input = {"concept_input_status": "synthetic",
                                  "live_eligible_concept_count": len(concepts)}
        self._analyze(concepts, requested_tokens=requested_tokens)
        return self

    def _find_birth_certificate(self) -> str:
        cert_dir = os.path.join(self.state_dir, "certificates")
        if not os.path.isdir(cert_dir):
            return ""
        for name in sorted(os.listdir(cert_dir)):
            if name.endswith(".md") or name.endswith(".json"):
                return os.path.join(cert_dir, name)
        return ""

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
        }

    def _ontogenesis_report_present(self) -> bool:
        return os.path.isfile(os.path.join(
            self.state_dir, "ontogenesis", "reports",
            "LIVE_ONTOGENESIS_REPORT.json")) or bool(self.concept_input)

    def _analyze(self, concepts: List[Any],
                 requested_tokens: Optional[Dict[str, str]] = None) -> None:
        obs = self.observation
        load = obs.get("load", {})
        load_status = load.get("load_status", "")

        # Generate private sign candidates for eligible proto-concepts.
        generator = LivePrivateSignGenerator()
        gen = generator.generate_for_concepts(
            concepts[:self.max_concepts], max_signs=self.max_signs,
            requested_tokens=requested_tokens)
        self.candidates = gen.candidates
        concept_by_id = {getattr(c, "concept_id", ""): c for c in concepts}

        utility = LiveSignUtilityAssessment()
        cfilter = LiveSignContaminationFilter()
        allow_birth = (self.allow_limited_birth
                       or self.semiogenesis_profile.allow_limited_birth)
        gate = LiveSignBirthGate(min_utility=self.min_utility,
                                 allow_birth=allow_birth)
        onto_present = self._ontogenesis_report_present()
        self.sign_memory = LiveSignMemory(state_dir=self.state_dir).load()

        for cand in self.candidates:
            concept = concept_by_id.get(
                cand.linked_concept_ids[0] if cand.linked_concept_ids else "")
            stability = float(getattr(concept, "stability_score", 0.0) or 0.0)
            recurrence = int(getattr(concept, "recurrence_count", 0) or 0)
            concept_contaminated = bool(getattr(concept,
                                                "contamination_findings", []))
            concept_eligible = bool(getattr(concept, "eligible", True))

            score = utility.assess(candidate=cand, concept_stability=stability,
                                   concept_recurrence=recurrence,
                                   load_status=load_status)
            cand.utility_score = score.score
            self.utility_scores[cand.sign_id] = score.to_dict()

            contamination = cfilter.evaluate(
                candidate=cand, concept_contaminated=concept_contaminated)
            for f in contamination.findings:
                if f.contamination_type not in cand.contamination_findings:
                    cand.contamination_findings.append(f.contamination_type)
            self.contamination_results.append(contamination.to_dict())

            gate_result = gate.evaluate(
                candidate=cand, utility_score=score.score,
                contamination=contamination,
                governance_passed=self.governance_result.get(
                    "governance_passed", False),
                birth_certificate_present=self.birth_certificate_present,
                observation_stability_blocked=obs.get("blocked", False),
                ontogenesis_report_present=onto_present,
                linked_concept_eligible=concept_eligible,
                linked_concept_contaminated=concept_contaminated, load=load)
            cand.birth_gate_result = gate_result.to_dict()
            self.birth_gate_results.append(gate_result.to_dict())
            self._apply_status(cand, contamination, gate_result)

            self.safety.validate_sign_birth(
                linked_stable_concept=concept_eligible,
                label_only="human_label_copy" in cand.contamination_findings,
                gloss_only="debug_gloss_copy" in cand.contamination_findings,
                operator_only="operator_phrase_copy"
                in cand.contamination_findings,
                contaminated=contamination.contaminated,
                stores_secret="secret_marker" in cand.contamination_findings)

            self.sign_memory.add(self._to_record(cand))

        # Private syntax over the (non-contaminated) candidates.
        self.syntax_graph = PrivateSyntaxBuilder().build(self.candidates).to_dict()

    def _apply_status(self, cand, contamination, gate_result) -> None:
        if contamination.is_source_artifact and not gate_result.born \
                and not contamination.contaminated:
            cand.status = SignCandidateStatus.SOURCE_ARTIFACT
        elif gate_result.status.startswith("blocked_by_"):
            cand.status = _STATUS_MAP.get(gate_result.status,
                                          SignCandidateStatus.SUSPENDED)
        else:
            cand.status = _STATUS_MAP.get(gate_result.status,
                                          SignCandidateStatus.INCONCLUSIVE)
        if cand.status in (SignCandidateStatus.STABILIZING,
                           SignCandidateStatus.INCONCLUSIVE) \
                and cand.utility_score < 0.35:
            cand.status = SignCandidateStatus.WEAK

    def _to_record(self, cand) -> LiveSignRecord:
        return LiveSignRecord(
            sign_id=cand.sign_id, private_token=cand.private_token,
            status=cand.status, run_id=self.run_id,
            linked_concept_ids=list(cand.linked_concept_ids),
            utility_score=cand.utility_score,
            source_distribution=dict(cand.source_distribution),
            supporting_refs=[e.ref for e in cand.supporting_events],
            contradicting_refs=[e.ref for e in cand.contradicting_events],
            contamination_findings=list(cand.contamination_findings),
            birth_gate_status=cand.birth_gate_result.get(
                "sign_birth_gate_status", ""),
            debug_alias=cand.debug_alias)

    # -- result + integration views -----------------------------------------

    def _counts(self) -> Dict[str, int]:
        def n(status):
            return sum(1 for c in self.candidates if c.status == status)
        return {
            "candidate_count": len(self.candidates),
            "stable_candidate_count": n(SignCandidateStatus.STABLE_CANDIDATE),
            "born_count": n(SignCandidateStatus.BORN),
            "rejected_count": n(SignCandidateStatus.REJECTED),
            "contaminated_count": n(SignCandidateStatus.CONTAMINATED),
            "label_dependent_count": n(SignCandidateStatus.LABEL_DEPENDENT),
            "source_artifact_count": n(SignCandidateStatus.SOURCE_ARTIFACT),
            "suspended_count": n(SignCandidateStatus.SUSPENDED),
            "weak_count": n(SignCandidateStatus.WEAK),
        }

    def _utility_mean(self) -> float:
        scores = [s.get("utility_score", 0.0)
                  for s in self.utility_scores.values()]
        return round(sum(scores) / len(scores), 3) if scores else 0.0

    def recommended_next_phase(self) -> str:
        if self.blocked:
            if any("concept" in b for b in self.blockers):
                return "collect_more_concepts"
            return "fix_sign_contamination" if any(
                "contam" in b for b in self.blockers) \
                else "resolve_semiogenesis_blockers"
        counts = self._counts()
        contaminated = sum(1 for r in self.contamination_results
                           if r.get("contaminated"))
        diet = self.observation.get("source_diet", {})
        if diet.get("balance") in ("operator_pulse_dominant",
                                   "human_text_dominant"):
            return "reduce_operator_text"
        if contaminated:
            return "fix_sign_contamination"
        if counts["born_count"] >= 2:
            return "ready_for_live_cognition_candidate"
        if counts["stable_candidate_count"] >= 1 or counts["born_count"] >= 1:
            return "continue_live_semiogenesis"
        if not self.eligible_concepts:
            return "collect_more_concepts"
        return "continue_live_semiogenesis"

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

    def _result(self) -> Dict[str, Any]:
        counts = self._counts()
        return {
            "refused": False, "run_id": self.run_id, "blocked": self.blocked,
            "blockers": list(self.blockers),
            "eligible_concept_count": len(self.eligible_concepts),
            "sign_candidate_count": counts["candidate_count"],
            "born_sign_count": counts["born_count"],
            "stable_sign_candidate_count": counts["stable_candidate_count"],
            "private_syntax_relation_count": self.syntax_graph.get(
                "live_private_syntax_relation_count", 0),
            "recommended_next_phase": self.recommended_next_phase(),
            "record": self.record.get("markdown"),
            "report": self.reports.get("markdown"),
            "sign_memory": (self.sign_memory.memory_path
                            if self.sign_memory else None),
        }

    def semiogenesis_status(self) -> Dict[str, Any]:
        counts = self._counts()
        return {
            "live_semiogenesis_enabled": True,
            "semiogenesis_run_id": self.run_id,
            "live_semiogenesis_blocked": self.blocked,
            "live_eligible_concept_count": len(self.eligible_concepts),
            "live_sign_candidate_count": counts["candidate_count"],
            "live_stable_sign_candidate_count": counts["stable_candidate_count"],
            "live_born_sign_count": counts["born_count"],
            "live_rejected_sign_count": counts["rejected_count"],
            "live_contaminated_sign_count": counts["contaminated_count"],
            "live_label_dependent_sign_count": counts["label_dependent_count"],
            "live_source_artifact_sign_count": counts["source_artifact_count"],
            "live_private_syntax_relation_count": self.syntax_graph.get(
                "live_private_syntax_relation_count", 0),
            "live_sign_utility_score_mean": self._utility_mean(),
            "live_sign_birth_gate_status": self._overall_gate_status(),
            "latest_sign_memory_path": (self.sign_memory.memory_path
                                        if self.sign_memory else None),
            "latest_semiogenesis_report_path": self.reports.get("markdown"),
            "recommended_next_phase": self.recommended_next_phase(),
            "live_semiogenesis_safety_block_count": self.safety.rejected_count,
            "enables_cognition": False, "enables_action_reaction": False,
            "enables_developmental_autonomy": False,
            "signs_are_language_understanding": False,
            "starts_feeders": False, "controls_hardware": False,
            "accesses_network": False, "runs_git": False,
        }

    def snapshot(self) -> Dict[str, Any]:
        return self.semiogenesis_status()

    def next_phase_recommendations(self) -> List[Dict[str, str]]:
        return [{"phase": self.recommended_next_phase(),
                 "detail": "advisory next phase from the semiogenesis run; never "
                           "started automatically"}]

    # -- integrations (optional; read-only / record-only) -------------------

    def research_cycle_update(self) -> Dict[str, Any]:
        phase = self.recommended_next_phase()
        if phase == "ready_for_live_cognition_candidate":
            action = "Prepare live cognition candidate protocol"
        elif self.blocked or phase.startswith(("fix", "resolve")) or phase in (
                "reduce_operator_text", "improve_source_diet",
                "collect_more_concepts"):
            action = "Resolve semiogenesis blockers"
        else:
            action = "Continue live semiogenesis observation"
        return {"semiogenesis_evidence_recorded": True, "next_action": action,
                "operational_only": True}

    def scientific_claims_update(self) -> Dict[str, Any]:
        counts = self._counts()
        return {
            "born_sign_count": counts["born_count"],
            "evidence_kind": "operational_internal_reference_structure",
            "candidate_only_run": not (self.allow_limited_birth
                                       or self.semiogenesis_profile
                                       .allow_limited_birth),
            "inconclusive_for_consciousness": True,
            "blocks_language_understanding_interpretation": True,
            "blocks_consciousness_life_agency_interpretation": True,
        }

    def write_artifacts(self) -> Dict[str, Any]:
        from .reports import LiveSemiogenesisReportBuilder
        from .semiogenesis_record import LiveSemiogenesisRecordBuilder

        if self.sign_memory is None:
            self.sign_memory = LiveSignMemory(state_dir=self.state_dir).load()
        self._write_state()
        if not self.dry_run:
            self.sign_memory.write()
        self.record = LiveSemiogenesisRecordBuilder(self).write()
        self.reports = LiveSemiogenesisReportBuilder(self).write()
        return {"record": self.record, "reports": self.reports}

    def _write_state(self) -> None:
        base = os.path.join(self.state_dir, "semiogenesis")

        def dump(subdir: str, name: str, obj: Any) -> None:
            path = os.path.join(base, subdir, name)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(obj, fh, indent=2, default=str)

        dump("utility", f"{self.run_id}.json", self.utility_scores)
        dump("contamination", f"{self.run_id}.json",
             {"results": self.contamination_results})
        dump("syntax", f"{self.run_id}.json", self.syntax_graph)
        for cand in self.candidates:
            dump("candidates", f"{cand.sign_id}.json", cand.to_dict())
        dump("index", f"{self.run_id}.json", self.semiogenesis_status())
