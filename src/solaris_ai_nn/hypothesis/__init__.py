"""Hypothesis engine, self-experimentation, and an internal scientific method.

Solaris-AI-NN can now form simple, grounded *hypothesis candidates* from its
own uncertainty -- Mysterium, failed predictions, weak world-model edges,
ambiguous proto-symbols, delayed consequences, anomalies, stagnation,
executive/homeostatic conflicts -- and test them through **bounded, safe**
experiments:

    uncertainty -> hypothesis -> bounded test -> evidence -> update / reject /
    preserve unknown

This is not human science, consciousness, or creativity in the human sense.
It is a low-compute internal experimental loop. No LLM generates hypotheses,
no human feedback is required, no experiment reaches the real world, and
nothing here can bypass governance, safety, executive inhibition, ego
boundaries, or the emergency stop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .evidence import (
    EvidenceLedger,
    EvidenceRecord,
    EvidenceType,
)
from .experiment_design import (
    ExperimentControl,
    ExperimentDesign,
    ExperimentOutcome,
    ExperimentScope,
    ExperimentVariable,
    design_for,
    design_to_candidate,
)
from .falsification import FalsificationEngine, FalsificationResult
from .generation import HypothesisGenerator
from .hypotheses import (
    Hypothesis,
    HypothesisConfidence,
    HypothesisScope,
    HypothesisStatus,
    HypothesisType,
)
from .hypothesis_memory import HypothesisHistoryRecord, HypothesisMemory
from .interventions import Intervention, InterventionPlan, InterventionType
from .priority import HypothesisPrioritizer
from .reports import (
    HYPOTHESIS_LIMITATIONS,
    HypothesisQueryInterface,
    HypothesisReportBuilder,
)
from .safety import HypothesisSafetyValidator
from .sources import HypothesisSeed, HypothesisSourceScanner
from .test_runner import HypothesisTestResult, HypothesisTestRunner

__all__ = [
    "EvidenceLedger", "EvidenceRecord", "EvidenceType", "ExperimentControl",
    "ExperimentDesign", "ExperimentOutcome", "ExperimentScope",
    "ExperimentVariable", "FalsificationEngine", "FalsificationResult",
    "HYPOTHESIS_LIMITATIONS", "Hypothesis", "HypothesisConfidence",
    "HypothesisEngine", "HypothesisGenerator", "HypothesisHistoryRecord",
    "HypothesisMemory", "HypothesisPrioritizer", "HypothesisQueryInterface",
    "HypothesisReportBuilder", "HypothesisSafetyValidator", "HypothesisScope",
    "HypothesisSeed", "HypothesisSourceScanner", "HypothesisStatus",
    "HypothesisTestResult", "HypothesisTestRunner", "HypothesisType",
    "Intervention", "InterventionPlan", "InterventionType", "design_for",
    "design_to_candidate",
]


@dataclass
class HypothesisEngine:
    """Coordinator: scan -> generate -> prioritize -> design -> test ->
    update. A safe, bounded internal scientific loop, never an authority."""

    state_dir: Any = None
    scanner: HypothesisSourceScanner = field(
        default_factory=HypothesisSourceScanner)
    generator: HypothesisGenerator = field(
        default_factory=HypothesisGenerator)
    prioritizer: HypothesisPrioritizer = field(
        default_factory=HypothesisPrioritizer)
    safety: HypothesisSafetyValidator = field(
        default_factory=HypothesisSafetyValidator)
    memory: Optional[HypothesisMemory] = None
    runner: Optional[HypothesisTestRunner] = None
    # Optional safe subsystems.
    nursery: Any = None
    latent: Any = None
    world_model: Any = None
    protolanguage: Any = None
    active_perception: Any = None
    governance: Any = None
    # Config.
    max_tests_per_tick: int = 2
    enable_world_model_updates: bool = False
    world_model_update_confidence: float = 0.6
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.memory is None:
            self.memory = HypothesisMemory(state_dir=self.state_dir)
        if self.runner is None:
            self.runner = HypothesisTestRunner(
                state_dir=self.state_dir, safety=self.safety,
                evidence_ledger=EvidenceLedger(state_dir=self.state_dir),
                nursery=self.nursery, latent=self.latent,
                world_model=self.world_model,
                protolanguage=self.protolanguage,
                active_perception=self.active_perception)
        self._mysterium_deltas: List[float] = []

    # -- the loop -----------------------------------------------------------------

    def tick(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """One scan -> generate -> prioritize -> bounded test cycle."""
        if not self.enabled:
            return {"enabled": False}
        ctx = dict(context or {})
        # 1. Scan + generate.
        seeds = self.scanner.rank_seeds(self.scanner.scan(ctx))
        new_hyps = self.generator.generate(seeds, ctx)
        for h in new_hyps:
            self.memory.add(h)
        # 2. Prioritize the schedulable set (testing blocked in emergency).
        candidates = [h for h in self.memory.hypotheses.values()
                      if h.status in (HypothesisStatus.PROPOSED,
                                      HypothesisStatus.INCONCLUSIVE,
                                      HypothesisStatus.WEAKENED)
                      and h.testable]
        ranked = self.prioritizer.prioritize(candidates, ctx)
        # 3. Design + run bounded tests.
        results = []
        for hypothesis in ranked[:self.max_tests_per_tick]:
            hypothesis.set_status(HypothesisStatus.SCHEDULED)
            design = design_for(hypothesis)
            result = self.runner.run_design(design, ctx, hypothesis)
            self.memory.record_status(hypothesis, detail=result.verdict)
            self._track_mysterium(result)
            if result.verdict == "supported":
                self._maybe_promote(hypothesis, result)
            results.append(result)
        self.memory.save_state()
        return {"new_hypotheses": len(new_hyps),
                "tested": len(results),
                "results": [r.to_dict() for r in results]}

    def _track_mysterium(self, result: HypothesisTestResult) -> None:
        deltas = (result.metric_deltas or {}).get("mysterium_pressure")
        if isinstance(deltas, dict) and deltas.get("delta") is not None:
            # Reduction is a positive contribution.
            self._mysterium_deltas.append(-float(deltas["delta"]))
            self._mysterium_deltas = self._mysterium_deltas[-200:]

    def _maybe_promote(self, hypothesis: Hypothesis,
                       result: HypothesisTestResult) -> None:
        """Carefully update world model / proto-language from real support."""
        evidence = result.evidence or {}
        if evidence.get("is_offline"):
            return  # offline support cannot promote
        if hypothesis.confidence < self.world_model_update_confidence:
            return
        if self.governance is not None and not self._gov_allows():
            return
        if hypothesis.type in (HypothesisType.WORLD_MODEL_EDGE,
                               HypothesisType.CAUSAL_CANDIDATE,
                               HypothesisType.PREDICTION) \
                and self.world_model is not None \
                and self.enable_world_model_updates:
            self._strengthen_world_model(hypothesis)
            self.memory.record_promotion(hypothesis.hypothesis_id,
                                         "world_model")
        elif hypothesis.type == HypothesisType.PROTO_SYMBOL_GROUNDING \
                and self.protolanguage is not None:
            self.memory.record_promotion(hypothesis.hypothesis_id,
                                         "proto_symbol")

    def _gov_allows(self) -> bool:
        try:
            from ..governance.permissions import PermissionScope

            return self.governance.permissions.allows(
                PermissionScope.ENABLE_HYPOTHESIS_WORLD_MODEL_UPDATES)
        except Exception:
            return False

    def _strengthen_world_model(self, hypothesis: Hypothesis) -> None:
        """Strengthen (or contradict) a world-model edge from evidence."""
        graph = getattr(self.world_model, "graph", None)
        if graph is None or not hypothesis.target_ref:
            return
        try:
            from ..world_model.edges import EdgeType
            from ..world_model.nodes import NodeType

            source = graph.upsert_node(
                NodeType.UNKNOWN, str(hypothesis.target_ref),
                source_module="hypothesis_engine")
            outcome = graph.upsert_node(
                NodeType.UNKNOWN,
                f"outcome:{hypothesis.hypothesis_id}",
                source_module="hypothesis_engine")
            # A supported hypothesis becomes a hedged predicts/causes
            # candidate, evidence-backed (never a proven cause).
            graph.upsert_edge(source, EdgeType.PREDICTS, outcome,
                              weight_delta=0.5, offline=False,
                              evidence=f"hypothesis:{hypothesis.hypothesis_id}")
        except Exception:  # graph updates are best-effort
            pass

    def weaken_world_model(self, hypothesis: Hypothesis) -> None:
        """A falsified hypothesis weakens / contradicts its edge."""
        graph = getattr(self.world_model, "graph", None)
        if graph is None or not hypothesis.target_ref:
            return
        try:
            from ..world_model.edges import EdgeType
            from ..world_model.nodes import NodeType

            source = graph.upsert_node(
                NodeType.UNKNOWN, str(hypothesis.target_ref),
                source_module="hypothesis_engine")
            outcome = graph.upsert_node(
                NodeType.UNKNOWN,
                f"outcome:{hypothesis.hypothesis_id}",
                source_module="hypothesis_engine")
            graph.upsert_edge(source, EdgeType.CONTRADICTS, outcome,
                              weight_delta=0.5, offline=False,
                              evidence=f"falsified:{hypothesis.hypothesis_id}")
        except Exception:
            pass

    # -- active-perception bridge -------------------------------------------------

    def sampling_target_for(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Bias an active-perception context toward this hypothesis target.

        A high-priority hypothesis defines a sampling target: the controller
        will sample the uncertain region/symbol the hypothesis names.
        """
        target = hypothesis.target_ref or "unknown"
        ctx: Dict[str, Any] = {"step": 0, "health_level": "ok",
                               "energy": 0.9}
        if hypothesis.type == HypothesisType.PROTO_SYMBOL_GROUNDING:
            ctx["proto_language"] = {"symbol_count": 6,
                                     "ambiguous_symbol_count": 4,
                                     "ambiguous_symbols": [target]}
        elif hypothesis.type in (HypothesisType.WORLD_MODEL_EDGE,
                                 HypothesisType.CAUSAL_CANDIDATE):
            ctx["world_model"] = {"graph_node_count": 10,
                                  "unknown_node_count": 4,
                                  "prediction_accuracy": 0.4,
                                  "low_confidence_nodes": [target]}
        else:
            ctx["mysterium_pressure"] = 0.6
        return ctx

    def test_via_active_perception(self, hypothesis: Hypothesis,
                                   ) -> Optional[HypothesisTestResult]:
        """Run an active-perception sampling action as a hypothesis test.

        The sampling result becomes source-scoped evidence: simulation-scope
        sampling is nursery-simulated; internal/offline sampling stays
        offline and cannot fully promote the hypothesis.
        """
        if self.active_perception is None:
            return None
        before = self.sampling_target_for(hypothesis)
        decision = self.active_perception.select(before)
        result = self.active_perception.execute_if_allowed(decision, before)
        after = dict(before, step=before.get("step", 0) + 1)
        record = self.active_perception.observe_result(result, before, after)
        gain = float(getattr(record, "observed_information_gain", 0.0) or 0.0)
        offline = decision.action.scope in ("internal_only",
                                            "sidecar_observe_only")
        if result.blocked:
            etype = EvidenceType.INCONCLUSIVE
            scope = "internal_trace_analysis"
        elif gain > 0.02:
            etype = (EvidenceType.OFFLINE_SIMULATED if offline
                     else EvidenceType.NURSERY_SIMULATED)
            scope = ("latent_replay" if offline else "nursery_simulation")
        else:
            etype = EvidenceType.INCONCLUSIVE
            scope = ("latent_replay" if offline else "nursery_simulation")
        evidence = EvidenceRecord(
            hypothesis_id=hypothesis.hypothesis_id, evidence_type=etype,
            source_scope=scope,
            observation=f"active-perception sampling "
                        f"({decision.action.action_type}) gain={gain}",
            metric_deltas={"observed_information_gain": gain},
            evidence_refs=[f"sampling:{decision.action.action_id}"])
        self.runner.evidence_ledger.record(evidence)
        verdict = self.runner.falsification.evaluate(hypothesis, evidence)
        self.runner.falsification.update_confidence(hypothesis, verdict)
        self.memory.record_status(hypothesis, detail=verdict.verdict)
        test_result = HypothesisTestResult(
            design_id=f"AP_{hypothesis.hypothesis_id}",
            hypothesis_id=hypothesis.hypothesis_id, scope=scope,
            executed=not result.blocked, blocked=result.blocked,
            status=hypothesis.status, verdict=verdict.verdict,
            evidence=evidence.to_dict())
        return test_result

    # -- views --------------------------------------------------------------------

    def mysterium_reduction_after_tests(self) -> Optional[float]:
        if not self._mysterium_deltas:
            return None
        return round(sum(self._mysterium_deltas)
                     / len(self._mysterium_deltas), 4)

    def summary(self) -> Dict[str, Any]:
        memory = self.memory.snapshot()
        counts = memory.get("counts_by_status", {})
        hyps = list(self.memory.hypotheses.values())
        top = max(hyps, key=lambda h: h.priority, default=None)
        runner = self.runner.snapshot()
        return {
            "enabled": self.enabled,
            "hypothesis_count": memory.get("hypothesis_count", 0),
            "highest_priority_hypothesis": (top.hypothesis_id if top
                                            else None),
            "current_test_scope": (runner.get("last_result") or {}).get(
                "scope"),
            "supported_count": counts.get(HypothesisStatus.SUPPORTED, 0),
            "falsified_count": counts.get(HypothesisStatus.FALSIFIED, 0),
            "inconclusive_count": counts.get(HypothesisStatus.INCONCLUSIVE, 0),
            "unsafe_to_test_count": counts.get(
                HypothesisStatus.UNSAFE_TO_TEST, 0),
            "scheduled_test_count": counts.get(HypothesisStatus.SCHEDULED, 0),
            "tests_run": runner.get("tests_run", 0),
            "long_lived_unknown_count": memory.get(
                "long_lived_unknown_count", 0),
            "last_evidence_result": (runner.get("last_result") or {}).get(
                "verdict"),
            "mysterium_reduction_after_tests":
                self.mysterium_reduction_after_tests(),
            "hypothesis_report_path": getattr(self, "report_path", None),
            "authority": False,
            "note": "internal research artifacts, not beliefs; offline "
                    "evidence is never treated as real observation",
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "scanner": self.scanner.snapshot(),
            "generator": self.generator.snapshot(),
            "prioritizer": self.prioritizer.snapshot(),
            "memory": self.memory.snapshot(),
            "test_runner": self.runner.snapshot(),
            "safety": self.safety.snapshot(),
            "mysterium_reduction_after_tests":
                self.mysterium_reduction_after_tests(),
            "summary": self.summary(),
        }
