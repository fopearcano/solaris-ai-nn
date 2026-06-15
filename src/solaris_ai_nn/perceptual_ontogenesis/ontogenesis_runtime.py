"""Perceptual ontogenesis runtime -- birth an internal world from perception.

:class:`PerceptualOntogenesisRuntime` reads the plural-sensorium traces (and, if
available, perceptual-metabolism state, live-field source health, and feeder-SDK
metadata), extracts :class:`PerceptualAtom`s, conservatively proposes
:class:`ProtoConcept`s, stabilizes/decays them, clusters them into families, grows
relations, and summarizes the observable structural world. Every output is
*internal*: the runtime polls no hardware, controls no feeder, modifies no source,
actuates nothing, treats no human label as ground truth, and is strictly bounded
against concept explosion.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .concept_birth import ConceptBirthEngine
from .concept_family import ConceptFamilyBuilder
from .concept_memory import ConceptMemoryStore
from .contamination import ConceptContaminationAnalyzer
from .decay import ConceptDecayEngine
from .perceptual_atoms import (
    PerceptualAtom,
    PerceptualAtomKind,
    PerceptualAtomSource,
)
from .proto_concepts import ProtoConcept, ProtoConceptStatus
from .relation_growth import ConceptRelationGrowthEngine
from .reports import PerceptualOntogenesisReportBuilder
from .safety import PerceptualOntogenesisSafetyValidator
from .stabilization import ConceptStabilizationEngine
from .world_formation import WorldFormationBuilder


class OntogenesisMilestone:
    FIRST_ATOM = "first_perceptual_atom"
    FIRST_CANDIDATE = "first_proto_concept_candidate"
    FIRST_STABLE = "first_stable_proto_concept"
    FIRST_DECAY = "first_concept_decay"
    FIRST_FAMILY = "first_concept_family"
    FIRST_RELATION = "first_concept_relation"
    FIRST_CROSS_MODAL_CONCEPT = "first_cross_modal_concept"
    FIRST_ABSENCE_CONCEPT = "first_absence_based_concept"
    FIRST_CONTAMINATION = "first_human_label_contamination"
    FIRST_WORLD_FORMATION = "first_world_formation_state"

    ALL = (FIRST_ATOM, FIRST_CANDIDATE, FIRST_STABLE, FIRST_DECAY,
           FIRST_FAMILY, FIRST_RELATION, FIRST_CROSS_MODAL_CONCEPT,
           FIRST_ABSENCE_CONCEPT, FIRST_CONTAMINATION, FIRST_WORLD_FORMATION)


@dataclass
class PerceptualOntogenesisRuntime:
    """The bounded ontogenesis loop (internal-only concept formation)."""

    state_dir: str = ".solaris_ai_nn_ontogenesis"
    sensorium: Any = None
    metabolism: Any = None
    live_field: Any = None
    feeder_metadata: Optional[Dict[str, Any]] = None
    world_signature: Any = None
    max_atoms_per_tick: int = 200
    max_concepts_per_tick: int = 50
    max_concepts_total: int = 2000
    max_runtime_s: float = 30.0
    max_ticks: int = 120
    fixture_mode: bool = True
    live_read_only_mode: bool = False
    require_governance_for_live: bool = True
    dry_run: bool = False

    birth: ConceptBirthEngine = field(default=None, init=False)
    stabilizer: ConceptStabilizationEngine = field(
        default_factory=ConceptStabilizationEngine)
    decayer: ConceptDecayEngine = field(default_factory=ConceptDecayEngine)
    family_builder: ConceptFamilyBuilder = field(
        default_factory=ConceptFamilyBuilder)
    relation_engine: ConceptRelationGrowthEngine = field(
        default_factory=ConceptRelationGrowthEngine)
    contamination: ConceptContaminationAnalyzer = field(
        default_factory=ConceptContaminationAnalyzer)
    world_builder: WorldFormationBuilder = field(
        default_factory=WorldFormationBuilder)
    memory: ConceptMemoryStore = field(default=None, init=False)
    safety: PerceptualOntogenesisSafetyValidator = field(
        default_factory=PerceptualOntogenesisSafetyValidator)

    atoms: Dict[str, PerceptualAtom] = field(default_factory=dict, init=False)
    concepts: Dict[str, ProtoConcept] = field(default_factory=dict, init=False)
    _concept_by_signature: Dict[str, str] = field(default_factory=dict,
                                                   init=False)
    milestones: List[str] = field(default_factory=list, init=False)
    explosion_warnings: int = field(default=0, init=False)
    ticks_run: int = field(default=0, init=False)
    world: Any = field(default=None, init=False)
    _last: Dict[str, Any] = field(default_factory=dict, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.birth = ConceptBirthEngine(live_mode=not self.fixture_mode)
        self.memory = ConceptMemoryStore(state_dir=self.state_dir,
                                         persist=not self.dry_run)
        bounded = self.safety.validate_bounded(self.max_ticks,
                                               self.max_runtime_s)
        self._refused = not bounded.safe

    def _milestone(self, name: str) -> None:
        if name not in self.milestones:
            self.milestones.append(name)

    # -- atom extraction ------------------------------------------------------

    def _origin(self) -> str:
        if self.live_field is not None and self.live_read_only_mode:
            return PerceptualAtomSource.LIVE_FIELD
        return PerceptualAtomSource.FIXTURE

    def _add_atom(self, atom: PerceptualAtom) -> None:
        existing_id = None
        for aid, a in self.atoms.items():
            if a.signature == atom.signature:
                existing_id = aid
                break
        if existing_id is not None:
            self.atoms[existing_id].observe_again(atom.timestamp_last_seen)
        else:
            if len(self.atoms) >= self.max_atoms_per_tick * max(1,
                                                                self.ticks_run):
                return
            self.atoms[atom.atom_id] = atom
            self._milestone(OntogenesisMilestone.FIRST_ATOM)

    def _extract_atoms(self) -> List[PerceptualAtom]:
        s = self.sensorium
        origin = self._origin()
        new_atoms: List[PerceptualAtom] = []
        if s is None:
            return new_atoms

        def mk(**kw) -> PerceptualAtom:
            kw.setdefault("origin", origin)
            return PerceptualAtom(**kw)

        # Invariants -> invariant atoms (recurrence == support).
        for cand in getattr(getattr(s, "invariants", None), "candidates",
                            {}).values():
            new_atoms.append(mk(
                kind=PerceptualAtomKind.INVARIANT, modality=cand.modality,
                source_id=cand.source_id, recurrence_count=max(1, cand.support),
                novelty=0.6, stability_score=min(1.0, 0.2 * cand.support),
                prediction_score=min(1.0, 0.18 * cand.support),
                compression_score=min(1.0, 0.2 * cand.support),
                provenance_refs=[f"invariant:{cand.candidate_id}"],
                metadata={"signature": cand.signature}))
        # Rhythms -> rhythm atoms.
        for sig in getattr(getattr(s, "rhythm", None), "signatures",
                          {}).values():
            new_atoms.append(mk(
                kind=PerceptualAtomKind.RHYTHM, modality=sig.modality,
                source_id=sig.source_id, recurrence_count=max(1, sig.cycles),
                novelty=0.4, stability_score=sig.regularity,
                prediction_score=sig.regularity,
                provenance_refs=[f"rhythm:{sig.source_id}"],
                metadata={"signature": f"rhythm:{sig.modality}:{sig.source_id}",
                          "period": sig.period}))
        # Absence events -> absence atoms.
        for ev in getattr(getattr(s, "absence", None), "events", []):
            new_atoms.append(mk(
                kind=PerceptualAtomKind.ABSENCE, modality=ev.modality,
                source_id=ev.source_id, novelty=0.7,
                prediction_score=0.5,
                provenance_refs=[f"absence:{ev.absence_id}"],
                metadata={"signature":
                          f"absence:{ev.modality}:{ev.source_id}"}))
        # Cross-modal relations -> cross-modal atoms.
        cross = getattr(s, "cross_modal", None)
        for rel in (cross.all_relations() if cross is not None else []):
            new_atoms.append(mk(
                kind=PerceptualAtomKind.CROSS_MODAL,
                modality=f"{rel.modality_a}+{rel.modality_b}",
                source_id=rel.source_a, novelty=0.6, stability_score=0.3,
                provenance_refs=[f"cross_modal:{rel.modality_a}:"
                                 f"{rel.modality_b}"],
                metadata={"signature":
                          f"xmodal:{rel.modality_a}:{rel.modality_b}"}))
        # Receptor states -> receptor/source-health atoms (fatigue/unreliable).
        for r in getattr(s, "receptors", {}).values():
            if getattr(r, "reliability", 1.0) < 0.8:
                new_atoms.append(mk(
                    kind=PerceptualAtomKind.SOURCE_HEALTH, modality=r.modality,
                    source_id=r.source_id, receptor_id=r.receptor_id,
                    intensity=1.0 - r.reliability, novelty=0.3,
                    provenance_refs=[f"receptor:{r.receptor_id}"],
                    metadata={"signature":
                              f"source_health:{r.source_id}"}))
            elif getattr(r, "fatigue", 0.0) >= 0.6:
                new_atoms.append(mk(
                    kind=PerceptualAtomKind.RECEPTOR_STATE, modality=r.modality,
                    source_id=r.source_id, receptor_id=r.receptor_id,
                    intensity=r.fatigue, novelty=0.2,
                    provenance_refs=[f"receptor:{r.receptor_id}"],
                    metadata={"signature":
                              f"receptor_state:{r.receptor_id}"}))
        # Baseline shifts -> baseline-shift atoms.
        for shift in getattr(s, "baseline_shifts", []):
            new_atoms.append(mk(
                kind=PerceptualAtomKind.BASELINE_SHIFT,
                modality=shift.get("modality", "unknown"),
                source_id=shift.get("receptor_id", ""), novelty=0.5,
                intensity=float(shift.get("magnitude", 0.0)),
                provenance_refs=[f"baseline:{shift.get('receptor_id', '')}"],
                metadata={"signature":
                          f"baseline:{shift.get('receptor_id', '')}:"
                          f"{shift.get('field_name', '')}"}))
        # Metabolism state -> overload/deprivation atoms.
        new_atoms += self._metabolism_atoms(mk)
        return new_atoms

    def _metabolism_atoms(self, mk) -> List[PerceptualAtom]:
        out: List[PerceptualAtom] = []
        status = self._metabolism_status()
        if not status:
            return out
        if status.get("overload_state"):
            out.append(mk(
                kind=PerceptualAtomKind.OVERLOAD, modality="metabolic",
                source_id="perceptual_metabolism", novelty=0.4,
                intensity=1.0, origin=PerceptualAtomSource.METABOLISM,
                provenance_refs=["metabolism:overload"],
                metadata={"signature": "metabolic:overload"}))
        if status.get("deprivation_state"):
            out.append(mk(
                kind=PerceptualAtomKind.DEPRIVATION, modality="metabolic",
                source_id="perceptual_metabolism", novelty=0.7,
                origin=PerceptualAtomSource.METABOLISM,
                provenance_refs=["metabolism:deprivation"],
                metadata={"signature": "metabolic:deprivation"}))
        return out

    def _metabolism_status(self) -> Dict[str, Any]:
        m = self.metabolism
        if m is None:
            return {}
        if isinstance(m, dict):
            return m
        if hasattr(m, "metabolism_status"):
            return m.metabolism_status()
        if hasattr(m, "snapshot"):
            return m.snapshot()
        return {}

    # -- tick -----------------------------------------------------------------

    def update(self, *, tick: int = 0) -> Dict[str, Any]:
        """Run one bounded ontogenesis tick over the current sensorium state."""
        if self._refused:
            return {"refused": True, "reason": "unbounded concept creation"}
        self.ticks_run += 1

        for atom in self._extract_atoms():
            self._add_atom(atom)
            self.memory.record_atom(atom.to_dict())

        # Metabolism modulates birth priority (overload throttles birth).
        status = self._metabolism_status()
        overloaded = bool(status.get("overload_state"))
        priority_boost = 0.0
        if status:
            priority_boost = float(status.get("novelty_appetite_pressure",
                                              0.0) or 0.0)
        atom_list = list(self.atoms.values())
        born_this_tick = 0
        candidates = self.birth.propose(atom_list, metabolism=status or None,
                                        priority_boost=priority_boost)
        for cand in candidates:
            if overloaded and born_this_tick >= max(1,
                                                    self.max_concepts_per_tick
                                                    // 4):
                # Overload throttles concept birth (never deletes evidence).
                break
            if born_this_tick >= self.max_concepts_per_tick:
                self.explosion_warnings += 1
                break
            if len(self.concepts) >= self.max_concepts_total:
                self.explosion_warnings += 1
                break
            self._absorb(cand)
            born_this_tick += 1

        concept_list = list(self.concepts.values())
        # Stabilize / decay / contamination.
        for concept in concept_list:
            self.contamination.analyze(concept)
            if concept.is_contaminated:
                self._milestone(OntogenesisMilestone.FIRST_CONTAMINATION)
            result = self.stabilizer.stabilize(concept)
            if result.status == ProtoConceptStatus.STABLE:
                self._milestone(OntogenesisMilestone.FIRST_STABLE)
            decay = self.decayer.evaluate(
                concept, seen_this_tick=True,
                source_corrupted=False)
            if decay.decayed:
                self._milestone(OntogenesisMilestone.FIRST_DECAY)
                self.memory.record_concept_state(
                    concept.concept_id, decay.new_status,
                    {"reasons": decay.reasons})
            if concept.is_cross_modal:
                self._milestone(OntogenesisMilestone.FIRST_CROSS_MODAL_CONCEPT)
            if concept.is_absence_based:
                self._milestone(OntogenesisMilestone.FIRST_ABSENCE_CONCEPT)
            self.memory.record_concept(concept.to_dict())

        # Families.
        families = self.family_builder.build(concept_list)
        if families:
            self._milestone(OntogenesisMilestone.FIRST_FAMILY)
        # Relations.
        relations = self.relation_engine.grow(concept_list)
        for rel in relations:
            self.memory.record_relation(rel.to_dict())
        if self.relation_engine.relations:
            self._milestone(OntogenesisMilestone.FIRST_RELATION)
        for concept in concept_list:
            concept.relation_count = sum(
                1 for r in self.relation_engine.relations.values()
                if concept.concept_id in (r.source_concept, r.target_concept))
        # World formation.
        density = self.relation_engine.graph_density(len(concept_list))
        self.world = self.world_builder.build(
            concept_list,
            family_distribution=self.family_builder.distribution(),
            relation_density=density)
        self._milestone(OntogenesisMilestone.FIRST_WORLD_FORMATION)

        self.memory.write_index()
        self._last = {
            "tick": tick,
            "atom_count": len(self.atoms),
            "concept_count": len(self.concepts),
            "born_this_tick": born_this_tick,
            "family_count": len(families),
            "relation_count": len(self.relation_engine.relations),
            "world_formation": self.world.to_dict(),
        }
        return self._last

    def _absorb(self, cand: Any) -> None:
        """Add a new concept, or grow an existing one with the same signature."""
        signature = cand.concept.metadata.get("atom_signature", "")
        existing_id = self._concept_by_signature.get(signature)
        if existing_id is not None and existing_id in self.concepts:
            concept = self.concepts[existing_id]
            concept.recurrence_count += 1
            concept.last_seen = cand.concept.last_seen
            concept.stability_score = min(
                1.0, concept.stability_score + 0.1)
            concept.grounding_score = min(
                1.0, concept.grounding_score + 0.1)
            return
        self.concepts[cand.concept.concept_id] = cand.concept
        if signature:
            self._concept_by_signature[signature] = cand.concept.concept_id
        self._milestone(OntogenesisMilestone.FIRST_CANDIDATE)

    def run_bounded(self, max_ticks: Optional[int] = None) -> Dict[str, Any]:
        if self._refused:
            return {"refused": True}
        started = time.time()
        n = min(self.max_ticks, max_ticks or self.max_ticks)
        for tick in range(n):
            if time.time() - started > self.max_runtime_s:
                break
            self.update(tick=tick)
        return {"refused": False, "ticks_run": self.ticks_run,
                "last": self._last}

    # -- views / integration --------------------------------------------------

    def latent_replay_recommendations(self) -> List[str]:
        """A bounded list of concepts worth consolidating (recommendation only)."""
        recs: List[str] = []
        for c in self.concepts.values():
            if c.status in (ProtoConceptStatus.STABLE,
                            ProtoConceptStatus.AMBIGUOUS,
                            ProtoConceptStatus.DECAYING):
                recs.append(f"consolidate:{c.concept_id}:{c.status}")
            if len(recs) >= 6:
                break
        return recs

    def proto_language_signs(self) -> List[Dict[str, Any]]:
        """Optional internal signs for stable concepts (not human words)."""
        signs: List[Dict[str, Any]] = []
        for c in self.concepts.values():
            if c.status != ProtoConceptStatus.STABLE:
                continue
            sign_kind = ("human_label_contaminated" if c.is_contaminated
                         else "cross_modal" if c.is_cross_modal
                         else "modality_native")
            signs.append({"concept_id": c.concept_id,
                          "sign": c.operational_name, "sign_kind": sign_kind,
                          "note": "internal shorthand, not a human word"})
        return signs

    def world_model_nodes(self) -> List[Dict[str, Any]]:
        """Proto-concepts/families/relations as world-model node/edge dicts.

        Modality-native ontology is preserved: concepts become PROTO_SYMBOL /
        STIMULUS_PATTERN nodes, never human object/person/place nodes by default.
        """
        from ..world_model.nodes import NodeType, node_id_for

        nodes: List[Dict[str, Any]] = []
        for c in self.concepts.values():
            node_type = (NodeType.BOUNDARY
                         if c.kind == "boundary_based"
                         else NodeType.PROTO_SYMBOL)
            nodes.append({
                "node_id": node_id_for(node_type, c.operational_name),
                "type": node_type,
                "label": c.operational_name,
                "confidence": c.stability_score,
                "attributes": {
                    "concept_id": c.concept_id, "concept_kind": c.kind,
                    "status": c.status, "grounding": c.grounding,
                    "modality_distribution": dict(c.modality_distribution),
                    "is_cross_modal": c.is_cross_modal,
                    "human_label_contaminated": c.is_contaminated,
                    "note": "sensorium-native structure, not a human object "
                            "category"},
            })
        return nodes

    def world_model_edges(self) -> List[Dict[str, Any]]:
        """Concept relations as world-model edge dicts."""
        return [{"source_concept": r.source_concept,
                 "target_concept": r.target_concept,
                 "relation_type": r.relation_type, "strength": r.strength}
                for r in self.relation_engine.relations.values()]

    def hypothesis_seeds(self) -> List[Any]:
        """Seed hypotheses from proto-concepts (concept A predicts/precedes B)."""
        from ..hypothesis.sources import HypothesisSeed

        seeds: List[HypothesisSeed] = []
        # Absence-based concepts seed "X predicts absence" hypotheses.
        for c in self.concepts.values():
            if c.is_absence_based and c.status == ProtoConceptStatus.STABLE:
                seeds.append(HypothesisSeed(
                    source="perceptual_ontogenesis",
                    hypothesis_type="prediction",
                    target_ref=c.concept_id,
                    observation=f"{c.operational_name} predicts a recurring "
                                "absence/silence",
                    intensity=c.stability_score,
                    evidence_refs=list(c.provenance_refs),
                    metadata={"concept_kind": c.kind}))
            if c.status == ProtoConceptStatus.UNSTABLE:
                seeds.append(HypothesisSeed(
                    source="perceptual_ontogenesis",
                    hypothesis_type="anomaly",
                    target_ref=c.concept_id,
                    observation=f"{c.operational_name} may be a false pattern "
                                "(unstable)",
                    intensity=0.4, evidence_refs=list(c.provenance_refs)))
        # Strong source-shared relations seed "A precedes B" hypotheses.
        for r in self.relation_engine.relations.values():
            if r.strength >= 0.6:
                seeds.append(HypothesisSeed(
                    source="perceptual_ontogenesis",
                    hypothesis_type="relation",
                    target_ref=r.relation_id,
                    observation=f"{r.source_concept} {r.relation_type} "
                                f"{r.target_concept}",
                    intensity=r.strength, evidence_refs=list(r.evidence_refs)))
        return seeds

    def logos_tensions(self) -> List[Any]:
        """Ontogenesis tensions expressed as LOGOS tensions (valid types only)."""
        from ..logos_complexity.tension import (
            LogosTension,
            TensionPolarity,
            TensionType,
        )

        tensions: List[LogosTension] = []
        emerging = [c for c in self.concepts.values()
                    if c.status in (ProtoConceptStatus.EMERGING,
                                    ProtoConceptStatus.CANDIDATE)]
        decaying = self.decaying_concepts()
        if emerging and decaying:
            tensions.append(LogosTension(
                tension_type=TensionType.GROWTH_STAGNATION,
                polarity_a=TensionPolarity.EXPLORE,
                polarity_b=TensionPolarity.STABILIZE,
                source_modules=["perceptual_ontogenesis"],
                metadata={"ontogenesis_tension":
                          "emerging_concept_vs_decaying_concept"}))
        if self.contaminated_concepts():
            tensions.append(LogosTension(
                tension_type=TensionType.SYMBOL_AMBIGUITY,
                polarity_a="feature_grounded", polarity_b="label_grounded",
                source_modules=["perceptual_ontogenesis"],
                metadata={"ontogenesis_tension":
                          "feature_grounded_vs_label_grounded"}))
        # concept-birth pressure vs overload.
        if bool(self._metabolism_status().get("overload_state")):
            tensions.append(LogosTension(
                tension_type=TensionType.COMPLEXITY_OVERLOAD,
                polarity_a=TensionPolarity.NOVELTY,
                polarity_b=TensionPolarity.STABILIZE,
                source_modules=["perceptual_ontogenesis"],
                metadata={"ontogenesis_tension":
                          "concept_birth_pressure_vs_overload"}))
        # world formation vs unknown.
        if self.world is not None and self.concepts:
            tensions.append(LogosTension(
                tension_type=TensionType.KNOWN_UNKNOWN,
                polarity_a=TensionPolarity.KNOWN,
                polarity_b=TensionPolarity.UNKNOWN,
                source_modules=["perceptual_ontogenesis"],
                metadata={"ontogenesis_tension": "world_formation_vs_unknown"}))
        return tensions

    def contaminated_concepts(self) -> List[ProtoConcept]:
        return [c for c in self.concepts.values() if c.is_contaminated]

    def stable_concepts(self) -> List[ProtoConcept]:
        return [c for c in self.concepts.values()
                if c.status == ProtoConceptStatus.STABLE]

    def decaying_concepts(self) -> List[ProtoConcept]:
        return [c for c in self.concepts.values()
                if c.status in (ProtoConceptStatus.DECAYING,
                                ProtoConceptStatus.REJECTED)]

    def ontogenesis_status(self) -> Dict[str, Any]:
        concepts = list(self.concepts.values())
        n = max(1, len(concepts))
        modality_native = sum(
            1 for c in concepts if c.kind == "modality_native")
        cross_modal = sum(1 for c in concepts if c.is_cross_modal)
        absence = sum(1 for c in concepts if c.is_absence_based)
        contaminated = sum(1 for c in concepts if c.is_contaminated)
        contamination = (sum(c.human_label_contamination_score for c in concepts)
                         / n)
        pred_mean = sum(c.prediction_utility for c in concepts) / n
        comp_mean = sum(c.compression_utility for c in concepts) / n
        attn_mean = sum(c.attention_utility for c in concepts) / n
        world = self.world.to_dict() if self.world is not None else {}
        return {
            "perceptual_ontogenesis_enabled": True,
            "concept_prediction_utility_mean": round(pred_mean, 4),
            "concept_compression_utility_mean": round(comp_mean, 4),
            "concept_attention_utility_mean": round(attn_mean, 4),
            "perceptual_atom_count": len(self.atoms),
            "proto_concept_count": len(concepts),
            "stable_concept_count": len(self.stable_concepts()),
            "decaying_concept_count": len(self.decaying_concepts()),
            "rejected_concept_count": sum(
                1 for c in concepts
                if c.status == ProtoConceptStatus.REJECTED),
            "concept_family_count": len(self.family_builder.families),
            "dominant_concept_family": self.family_builder.dominant_family(),
            "concept_relation_count": len(self.relation_engine.relations),
            "modality_native_concept_ratio": round(modality_native / n, 4),
            "cross_modal_concept_ratio": round(cross_modal / n, 4),
            "absence_based_concept_ratio": round(absence / n, 4),
            "contaminated_concept_count": contaminated,
            "contaminated_concept_ratio": round(contaminated / n, 4),
            "human_label_contamination_score": round(contamination, 4),
            "concept_explosion_warning_count": self.explosion_warnings,
            "world_formation_density": (world.get("formation_density", 0.0)
                                        if world else 0.0),
            "world_formation_summary": world.get("state", {}),
            "latest_ontogenesis_report_path": self._report_path(),
        }

    def _report_path(self) -> Optional[str]:
        import os

        path = os.path.join(self.state_dir,
                            "PERCEPTUAL_ONTOGENESIS_REPORT.md")
        return path if os.path.isfile(path) else None

    def snapshot(self) -> Dict[str, Any]:
        return self.ontogenesis_status()

    def write_artifacts(self) -> Dict[str, Any]:
        return PerceptualOntogenesisReportBuilder(self).write()
