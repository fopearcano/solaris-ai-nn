"""Sensorium-cognition runtime -- bounded sign-based thought, internal-only.

:class:`SensoriumCognitionRuntime` reads the semiogenesis signs/patterns (and
optional ontogenesis concepts, metabolism state, and LOGOS tensions), updates a
cognitive state, executes bounded cognitive moves, generates predictions and
anticipation, derives question pressure, runs internal simulations and
counterfactuals, detects analogies, performs synthesis, writes cognitive memory,
and summarizes. Every output is *internal*: no LLM, no human-language default, no
hardware/feeder/source/action, and a strictly bounded loop.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .analogy import AnalogyEngine
from .anticipation import AnticipationEngine
from .cognitive_memory import CognitiveMemoryStore
from .cognitive_moves import CognitiveMove, CognitiveMoveType
from .cognitive_state import SensoriumCognitiveState
from .counterfactuals import CounterfactualEngine
from .internal_simulation import InternalSimulation, SimulationScope
from .prediction import PredictionEngine
from .question_pressure import QuestionPressureEngine
from .reports import SensoriumCognitionReportBuilder
from .safety import SensoriumCognitionSafetyValidator
from .sign_reasoning import SignReasoner
from .synthesis import SynthesisEngine


class CognitionMilestone:
    FIRST_MOVE = "first_cognitive_move"
    FIRST_PREDICTION = "first_prediction"
    FIRST_FAILED_PREDICTION = "first_failed_prediction"
    FIRST_QUESTION_PRESSURE = "first_question_pressure"
    FIRST_SIMULATION = "first_internal_simulation"
    FIRST_COUNTERFACTUAL = "first_counterfactual"
    FIRST_ANALOGY = "first_analogy"
    FIRST_SYNTHESIS = "first_synthesis"
    FIRST_PRESERVED_CONTRADICTION = "first_preserved_contradiction"

    ALL = (FIRST_MOVE, FIRST_PREDICTION, FIRST_FAILED_PREDICTION,
           FIRST_QUESTION_PRESSURE, FIRST_SIMULATION, FIRST_COUNTERFACTUAL,
           FIRST_ANALOGY, FIRST_SYNTHESIS, FIRST_PRESERVED_CONTRADICTION)


@dataclass
class SensoriumCognitionRuntime:
    """The bounded sign-based cognition loop (internal-only, no LLM)."""

    state_dir: str = ".solaris_ai_nn_cognition"
    semiogenesis: Any = None
    ontogenesis: Any = None
    world_model: Any = None
    hypothesis: Any = None
    metabolism: Any = None
    max_moves_per_tick: int = 60
    max_predictions_per_tick: int = 50
    max_simulations_per_tick: int = 20
    max_runtime_s: float = 30.0
    max_ticks: int = 120
    dry_run: bool = False
    fixture_mode: bool = True
    live_read_only_mode: bool = False

    reasoner: SignReasoner = field(default_factory=SignReasoner)
    predictor: PredictionEngine = field(default_factory=PredictionEngine)
    anticipator: AnticipationEngine = field(default_factory=AnticipationEngine)
    question_engine: QuestionPressureEngine = field(
        default_factory=QuestionPressureEngine)
    simulator: InternalSimulation = field(default_factory=InternalSimulation)
    counterfactual_engine: CounterfactualEngine = field(
        default_factory=CounterfactualEngine)
    analogy_engine: AnalogyEngine = field(default_factory=AnalogyEngine)
    synthesis_engine: SynthesisEngine = field(default_factory=SynthesisEngine)
    memory: CognitiveMemoryStore = field(default=None, init=False)
    safety: SensoriumCognitionSafetyValidator = field(
        default_factory=SensoriumCognitionSafetyValidator)

    state: SensoriumCognitiveState = field(
        default_factory=SensoriumCognitiveState)
    moves: List[CognitiveMove] = field(default_factory=list, init=False)
    predictions: List[Any] = field(default_factory=list, init=False)
    failed_predictions: List[Any] = field(default_factory=list, init=False)
    question_pressures: List[Any] = field(default_factory=list, init=False)
    simulations: List[Any] = field(default_factory=list, init=False)
    counterfactuals: List[Any] = field(default_factory=list, init=False)
    analogies: List[Any] = field(default_factory=list, init=False)
    synthesis_results: List[Any] = field(default_factory=list, init=False)
    milestones: List[str] = field(default_factory=list, init=False)
    overload_events: int = field(default=0, init=False)
    ticks_run: int = field(default=0, init=False)
    _last: Dict[str, Any] = field(default_factory=dict, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.memory = CognitiveMemoryStore(state_dir=self.state_dir,
                                           persist=not self.dry_run)
        bounded = self.safety.validate_bounded(self.max_ticks,
                                               self.max_runtime_s)
        self._refused = not bounded.safe

    def _milestone(self, name: str) -> None:
        if name not in self.milestones:
            self.milestones.append(name)

    def _signs(self) -> List[Any]:
        sem = self.semiogenesis
        if sem is None:
            return []
        if hasattr(sem, "signs"):
            return list(sem.signs.values())
        if isinstance(sem, (list, tuple)):
            return list(sem)
        return []

    def _patterns(self) -> List[Any]:
        sem = self.semiogenesis
        return list(getattr(sem, "patterns", []) or [])

    def _concepts(self) -> List[Any]:
        ont = self.ontogenesis
        if ont is not None and hasattr(ont, "concepts"):
            return list(ont.concepts.values())
        return []

    def _logos_tensions(self) -> List[Any]:
        sem = self.semiogenesis
        if sem is not None and hasattr(sem, "logos_tensions"):
            try:
                return sem.logos_tensions()
            except Exception:
                return []
        return []

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

    def update(self, *, tick: int = 0,
               observed_targets: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run one bounded cognitive tick over the current signs/concepts."""
        if self._refused:
            return {"refused": True, "reason": "unbounded cognitive loop"}
        self.ticks_run += 1
        observed_targets = observed_targets or []

        signs = self._signs()
        patterns = self._patterns()
        concepts = self._concepts()
        status = self._metabolism_status()
        overloaded = bool(status.get("overload_state")
                          or status.get("sign_overload"))
        if overloaded:
            self.overload_events += 1
        move_budget = (max(1, self.max_moves_per_tick // 4) if overloaded
                       else self.max_moves_per_tick)

        # 1. Sign reasoning.
        reasoning = self.reasoner.reason(signs, patterns)

        # 2. Predictions (resolve against observed targets; failures kept).
        pred_result = self.predictor.predict(
            signs, patterns, metabolism=status,
            max_predictions=self.max_predictions_per_tick)
        for p in pred_result.predictions:
            if observed_targets:
                p.resolve(observed_targets)
            self.predictions.append(p)
            self.memory.record_prediction(p.to_dict())
            self._milestone(CognitionMilestone.FIRST_PREDICTION)
        self.failed_predictions = [p for p in self.predictions
                                   if getattr(p, "outcome", "") == "failure"]
        if self.failed_predictions:
            self._milestone(CognitionMilestone.FIRST_FAILED_PREDICTION)

        # 3. Anticipation.
        ant = self.anticipator.update(pred_result.predictions)
        self.memory.record_anticipation(ant.to_dict())

        # 4. Question pressure.
        self.question_pressures = self.question_engine.generate(
            signs=signs, failed_predictions=self.failed_predictions,
            logos_tensions=self._logos_tensions(),
            anticipation_targets=ant.expected_targets(),
            observed_targets=observed_targets)
        for q in self.question_pressures:
            self.memory.record_question(q.to_dict())
        if self.question_pressures:
            self._milestone(CognitionMilestone.FIRST_QUESTION_PRESSURE)

        # 5. Internal simulations (bounded; always non-real).
        sim_signs = [s.sign_id for s in signs[:4]]
        if sim_signs:
            sim = self.simulator.simulate_sequence(
                sim_signs, SimulationScope.SIGN_SEQUENCE,
                evidence_refs=["signs"])
            self.simulations.append(sim)
            self.memory.record_simulation(sim.to_dict())
            self._milestone(CognitionMilestone.FIRST_SIMULATION)
        for s in signs:
            if len(self.simulations) >= self.max_simulations_per_tick:
                break
            if getattr(s, "is_absence", False):
                sim = self.simulator.simulate_absence(
                    s.sign_id, evidence_refs=["absence"])
                self.simulations.append(sim)
                self.memory.record_simulation(sim.to_dict())

        # 6. Counterfactuals.
        cf = self.counterfactual_engine.generate(signs)
        self.counterfactuals = cf.counterfactuals
        if self.counterfactuals:
            self._milestone(CognitionMilestone.FIRST_COUNTERFACTUAL)

        # 7. Analogies.
        self.analogies = self.analogy_engine.detect(signs)
        if self.analogies:
            self._milestone(CognitionMilestone.FIRST_ANALOGY)

        # 8. Synthesis.
        synthesis = self.synthesis_engine.synthesize(signs,
                                                     reasoning.inferences)
        self.synthesis_results = synthesis.results
        for r in self.synthesis_results:
            self.memory.record_synthesis(r.to_dict())
            if r.preserved_contradiction:
                self._milestone(
                    CognitionMilestone.FIRST_PRESERVED_CONTRADICTION)
        if self.synthesis_results:
            self._milestone(CognitionMilestone.FIRST_SYNTHESIS)

        # 9. Cognitive moves (bounded; recommendations/markers only).
        self.moves = self._build_moves(signs, reasoning.inferences,
                                       pred_result.predictions, move_budget)
        for mv in self.moves:
            self.memory.record_move(mv.to_dict())
        if self.moves:
            self._milestone(CognitionMilestone.FIRST_MOVE)

        # 10. Update cognitive state.
        self._update_state(signs, concepts, tick, status)

        self.memory.write_index()
        self._last = {
            "tick": tick,
            "move_count": len(self.moves),
            "prediction_count": len(self.predictions),
            "failed_prediction_count": len(self.failed_predictions),
            "question_pressure_count": len(self.question_pressures),
            "simulation_count": len(self.simulations),
            "counterfactual_count": len(self.counterfactuals),
            "analogy_count": len(self.analogies),
            "synthesis_count": len(self.synthesis_results),
        }
        return self._last

    def _build_moves(self, signs: List[Any], inferences: List[Any],
                     predictions: List[Any], budget: int) -> List[CognitiveMove]:
        moves: List[CognitiveMove] = []

        def add(mv: CognitiveMove) -> None:
            if len(moves) < budget:
                moves.append(mv)

        for p in predictions:
            add(CognitiveMove(
                move_type=CognitiveMoveType.PREDICT_NEXT_SIGN,
                input_sign_refs=[getattr(p, "predicted_target", "")],
                result_refs=[getattr(p, "prediction_id", "")],
                confidence=getattr(p, "confidence", 0.0),
                uncertainty=getattr(p, "uncertainty", 0.0),
                evidence_refs=list(getattr(p, "evidence_refs", []))))
        for inf in inferences:
            add(CognitiveMove(
                move_type=CognitiveMoveType.TEST_RELATION,
                input_sign_refs=list(getattr(inf, "sign_refs", [])),
                result_refs=[getattr(inf, "inference_id", "")],
                confidence=getattr(inf, "confidence", 0.0),
                uncertainty=getattr(inf, "uncertainty", 0.0)))
        for q in self.question_pressures:
            add(CognitiveMove(
                move_type=CognitiveMoveType.GENERATE_QUESTION_PRESSURE,
                input_sign_refs=list(getattr(q, "target_refs", [])),
                result_refs=[getattr(q, "pressure_id", "")],
                metadata={"recommended_response":
                          getattr(q, "recommended_response", "")}))
        for s in signs:
            if getattr(s, "is_ambiguous", False):
                add(CognitiveMove(
                    move_type=CognitiveMoveType.DEFER_AS_AMBIGUOUS,
                    input_sign_refs=[s.sign_id]))
        # Always at least one attention-target recommendation if anything active.
        if signs:
            add(CognitiveMove(
                move_type=CognitiveMoveType.SELECT_ATTENTION_TARGET,
                input_sign_refs=[signs[0].sign_id],
                metadata={"attention": "highest-question-pressure target"}))
        return moves

    def _update_state(self, signs: List[Any], concepts: List[Any], tick: int,
                      status: Dict[str, Any]) -> None:
        st = self.state
        st.focus.active_signs = [s.sign_id for s in signs[:20]]
        st.focus.active_proto_concepts = [
            getattr(c, "concept_id", "") for c in concepts[:20]]
        st.focus.active_perceptual_needs = (
            [status.get("dominant_perceptual_need")]
            if status.get("dominant_perceptual_need") else [])
        st.focus.attention_recommendation = (
            "inspect highest question-pressure target"
            if self.question_pressures else "maintain")
        st.pressure.uncertainty = round(
            sum(getattr(q, "intensity", 0.0) for q in self.question_pressures)
            / max(1, len(self.question_pressures)), 4)
        st.pressure.question_pressure = self.question_engine.pressure_score()
        st.pressure.anticipation = round(min(
            1.0, 0.1 * len(self.anticipator.state.events)), 4)
        st.pressure.simulation_pressure = round(min(
            1.0, 0.1 * len(self.simulations)), 4)
        st.pressure.synthesis_pressure = round(min(
            1.0, 0.2 * len(self.synthesis_results)), 4)
        st.unresolved_contradictions = [
            r.synthesis_id for r in self.synthesis_results
            if getattr(r, "preserved_contradiction", False)]
        st.continuity.continuity_tick = tick
        st.continuity.cognitive_saturation = round(min(
            1.0, len(self.moves) / max(1, self.max_moves_per_tick)), 4)
        st.continuity.cognitive_fatigue = round(min(
            1.0, 0.05 * self.overload_events), 4)

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

    # -- integration views ----------------------------------------------------

    def latent_replay_recommendations(self) -> List[str]:
        recs: List[str] = []
        for p in self.failed_predictions:
            recs.append(f"replay_failed_prediction:{p.prediction_id}")
            if len(recs) >= 6:
                return recs
        for q in self.question_pressures:
            recs.append(f"replay_question:{q.pressure_id}")
            if len(recs) >= 6:
                break
        return recs

    def world_model_nodes(self) -> List[Dict[str, Any]]:
        """Predictions/simulations/synthesis as world-model trace nodes.

        Simulated/counterfactual items are marked separately and never mixed
        with observation.
        """
        from ..world_model.nodes import NodeType, node_id_for

        nodes: List[Dict[str, Any]] = []
        for p in self.predictions:
            nodes.append({
                "node_id": node_id_for(NodeType.STATE, p.prediction_id),
                "type": NodeType.STATE, "label": p.prediction_id,
                "confidence": p.confidence,
                "attributes": {"role": "prediction", "outcome": p.outcome,
                               "simulated": False,
                               "note": "cognitive prediction trace"}})
        for sim in self.simulations:
            nodes.append({
                "node_id": node_id_for(NodeType.LATENT_SCHEMA,
                                       sim.simulation_id),
                "type": NodeType.LATENT_SCHEMA, "label": sim.simulation_id,
                "confidence": sim.usefulness,
                "attributes": {"role": "simulation", "simulated": True,
                               "is_real_observation": False,
                               "note": "internal simulation, NOT observation"}})
        return nodes

    def hypothesis_seeds(self) -> List[Any]:
        """Seed hypotheses from failed predictions, counterfactuals, analogies."""
        from ..hypothesis.sources import HypothesisSeed

        seeds: List[HypothesisSeed] = []
        for p in self.failed_predictions:
            seeds.append(HypothesisSeed(
                source="sensorium_cognition", hypothesis_type="anomaly",
                target_ref=p.prediction_id,
                observation=f"prediction {p.predicted_target} failed",
                intensity=0.5, evidence_refs=list(p.evidence_refs)))
        for cf in self.counterfactuals[:10]:
            seeds.append(HypothesisSeed(
                source="sensorium_cognition", hypothesis_type="counterfactual",
                target_ref=cf.counterfactual_id,
                observation=f"{cf.form} on {cf.target_ref}", intensity=0.3,
                offline=True))
        return seeds

    def logos_tensions(self) -> List[Any]:
        """Cognition tensions expressed as LOGOS tensions (valid types only)."""
        from ..logos_complexity.tension import (
            LogosTension,
            TensionPolarity,
            TensionType,
        )

        tensions: List[LogosTension] = []
        if self.failed_predictions:
            tensions.append(LogosTension(
                tension_type=TensionType.PREDICTION_FAILURE,
                polarity_a="prediction", polarity_b="failure",
                source_modules=["sensorium_cognition"],
                metadata={"cognition_tension": "prediction_vs_failure"}))
        if self.simulations:
            tensions.append(LogosTension(
                tension_type=TensionType.OFFLINE_REAL_BOUNDARY,
                polarity_a="simulation", polarity_b="observation",
                source_modules=["sensorium_cognition"],
                metadata={"cognition_tension": "simulation_vs_observation"}))
        if self.analogy_engine.contradicted_count:
            tensions.append(LogosTension(
                tension_type=TensionType.HYPOTHESIS_CONFLICT,
                polarity_a="analogy", polarity_b="difference",
                source_modules=["sensorium_cognition"],
                metadata={"cognition_tension": "analogy_vs_difference"}))
        if self.question_pressures:
            tensions.append(LogosTension(
                tension_type=TensionType.KNOWN_UNKNOWN,
                polarity_a=TensionPolarity.KNOWN,
                polarity_b=TensionPolarity.UNKNOWN,
                source_modules=["sensorium_cognition"],
                metadata={"cognition_tension": "question_pressure_vs_no_data"}))
        return tensions

    def metabolism_signals(self) -> Dict[str, Any]:
        return {
            "cognitive_overload": self.overload_events > 0,
            "prediction_overload": len(self.predictions)
            >= self.max_predictions_per_tick,
            "question_pressure_overload": len(self.question_pressures) > 20,
            "simulation_fatigue": len(self.simulations)
            >= self.max_simulations_per_tick,
            "synthesis_pressure": round(self.state.pressure.synthesis_pressure,
                                        4),
            "consolidation_pressure": round(min(
                1.0, 0.1 * len(self.failed_predictions)), 4),
        }

    def cognition_status(self) -> Dict[str, Any]:
        preds = self.predictions
        resolved = [p for p in preds if getattr(p, "outcome", "") != "unknown"]
        ok = sum(1 for p in resolved if getattr(p, "outcome", "") == "success")
        success_rate = round(ok / len(resolved), 4) if resolved else 0.0
        q_resolved = sum(1 for q in self.question_pressures
                         if getattr(q, "resolved", False))
        return {
            "sensorium_cognition_enabled": True,
            "cognitive_move_count": len(self.moves),
            "prediction_count": len(preds),
            "prediction_success_rate": success_rate,
            "failed_prediction_count": len(self.failed_predictions),
            "question_pressure_count": len(self.question_pressures),
            "question_pressure_resolution_rate": round(
                q_resolved / len(self.question_pressures), 4)
            if self.question_pressures else 0.0,
            "internal_simulation_count": len(self.simulations),
            "counterfactual_count": len(self.counterfactuals),
            "analogy_count": len(self.analogies),
            "analogy_failure_count": self.analogy_engine.contradicted_count,
            "synthesis_count": len(self.synthesis_results),
            "unresolved_tension_count": len(
                self.state.unresolved_contradictions),
            "cognition_overload_event_count": self.overload_events,
            "cognitive_state": self.state.to_dict(),
            "latest_cognition_report_path": self._report_path(),
        }

    def _report_path(self) -> Optional[str]:
        import os

        path = os.path.join(self.state_dir, "SENSORIUM_COGNITION_REPORT.md")
        return path if os.path.isfile(path) else None

    def snapshot(self) -> Dict[str, Any]:
        return self.cognition_status()

    def write_artifacts(self) -> Dict[str, Any]:
        return SensoriumCognitionReportBuilder(self).write()
