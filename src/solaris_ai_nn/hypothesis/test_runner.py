"""Hypothesis test runner -- bounded, safe execution of an experiment design.

The runner validates a design with the safety validator, refuses to test in
an emergency, routes the design to its bounded scope (latent replay, nursery
simulation, internal trace analysis, read-only / sidecar observation),
collects before/after metrics, produces a source-scoped
:class:`EvidenceRecord`, asks the :class:`FalsificationEngine` for a verdict,
updates the hypothesis confidence/status, and persists the test. Nothing here
acts in the real world or runs unbounded.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .evidence import (
    EvidenceLedger,
    EvidenceRecord,
    EvidenceType,
    scope_to_evidence_type,
)
from .experiment_design import ExperimentDesign, ExperimentScope
from .falsification import FalsificationEngine
from .hypotheses import Hypothesis, HypothesisStatus
from .safety import HypothesisSafetyValidator


def _num(d: Optional[Dict[str, Any]], key: str, default: float = 0.0) -> float:
    try:
        return float((d or {}).get(key, default) or 0.0)
    except (TypeError, ValueError):
        return default


# Per-metric expected direction: +1 means "expected to rise supports",
# -1 means "expected to fall supports".
_METRIC_DIRECTION = {
    "prediction_accuracy": +1,
    "edge_weight": +1,
    "structural_change_score": +1,
    "habit_value": +1,
    "delay_steps": +1,
    "inhibition_rate": +1,
    "anomaly_rate": +1,  # recurrence (a detectable rate) supports recurrence
    "rule_validated": +1,
    "mysterium_pressure": -1,
    "ambiguity_score": -1,
    "conflict_count": -1,
}

_EPS = 0.02


@dataclass
class HypothesisTestResult:
    """The outcome of running one experiment design."""

    design_id: str
    hypothesis_id: str
    scope: str
    executed: bool = False
    blocked: bool = False
    blocked_reason: str = ""
    status: str = HypothesisStatus.INCONCLUSIVE
    verdict: str = "inconclusive"
    evidence: Optional[Dict[str, Any]] = None
    metric_deltas: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class HypothesisTestRunner:
    """Runs bounded experiments and turns them into evidence + verdicts."""

    safety: HypothesisSafetyValidator = field(
        default_factory=HypothesisSafetyValidator)
    evidence_ledger: EvidenceLedger = field(default_factory=EvidenceLedger)
    falsification: FalsificationEngine = field(
        default_factory=FalsificationEngine)
    state_dir: Optional[Union[str, Path]] = None
    write_log: bool = True
    # Optional safe subsystems (all duck-typed; any may be None).
    nursery: Any = None
    latent: Any = None
    world_model: Any = None
    protolanguage: Any = None
    active_perception: Any = None
    tests_run: int = field(default=0, init=False)
    unsafe_count: int = field(default=0, init=False)
    inconclusive_count: int = field(default=0, init=False)
    last_result: Optional[HypothesisTestResult] = field(default=None,
                                                        init=False)

    def __post_init__(self) -> None:
        self.tests_path = (Path(self.state_dir) / "hypothesis_tests.jsonl"
                           if self.state_dir else None)

    # -- single design ------------------------------------------------------------

    def run_design(self, design: ExperimentDesign,
                   context: Dict[str, Any],
                   hypothesis: Optional[Hypothesis] = None,
                   ) -> HypothesisTestResult:
        ctx = dict(context or {})
        result = HypothesisTestResult(
            design_id=design.design_id, hypothesis_id=design.hypothesis_id,
            scope=design.scope)

        # 1. Refuse to test in an emergency / critical state.
        run_report = self.safety.validate_run_context(ctx)
        if not run_report.safe:
            return self._block(design, result, hypothesis,
                               "; ".join(run_report.violations))
        # 2. Validate the design.
        design_report = self.safety.validate_design(design)
        if not design_report.safe:
            self.unsafe_count += 1
            if hypothesis is not None:
                hypothesis.set_status(HypothesisStatus.UNSAFE_TO_TEST)
            return self._block(design, result, hypothesis,
                               "; ".join(design_report.violations),
                               unsafe=True)
        # 3. Validate every intervention.
        if design.intervention_plan is not None:
            for intervention in design.intervention_plan.interventions:
                rep = self.safety.validate_intervention(intervention)
                if not rep.safe:
                    self.unsafe_count += 1
                    if hypothesis is not None:
                        hypothesis.set_status(HypothesisStatus.UNSAFE_TO_TEST)
                    return self._block(design, result, hypothesis,
                                       "; ".join(rep.violations), unsafe=True)

        if hypothesis is not None:
            hypothesis.set_status(HypothesisStatus.TESTING)

        # 4. Observe within the bounded scope.
        observation, deltas, evidence_type, conf = self._observe(design, ctx)
        result.metric_deltas = deltas
        result.executed = True

        # 5. Record source-scoped evidence.
        evidence = EvidenceRecord(
            hypothesis_id=design.hypothesis_id, evidence_type=evidence_type,
            source_scope=design.scope, observation=observation,
            metric_deltas=deltas, confidence=conf,
            evidence_refs=[f"design:{design.design_id}"])
        self.evidence_ledger.record(evidence)

        # 6. Verdict + bounded confidence update.
        if hypothesis is not None:
            verdict = self.falsification.evaluate(hypothesis, evidence)
            self.falsification.update_confidence(hypothesis, verdict)
            result.verdict = verdict.verdict
            result.status = hypothesis.status
            if hypothesis.evidence_refs is not None:
                hypothesis.evidence_refs.append(evidence.evidence_id)
        else:
            result.verdict = "inconclusive"
            result.status = HypothesisStatus.INCONCLUSIVE
        if result.status == HypothesisStatus.INCONCLUSIVE:
            self.inconclusive_count += 1

        result.evidence = evidence.to_dict()
        self.tests_run += 1
        self.last_result = result
        self._persist(result)
        return result

    def run_batch(self, designs: List[ExperimentDesign],
                  context: Dict[str, Any], max_tests: int = 4,
                  hypotheses: Optional[Dict[str, Hypothesis]] = None,
                  ) -> List[HypothesisTestResult]:
        batch_report = self.safety.validate_batch(len(designs[:max_tests]))
        capped = designs[:max_tests] if batch_report.safe \
            else designs[:max_tests]
        hyp_map = hypotheses or {}
        results = []
        for design in capped:
            results.append(self.run_design(
                design, context, hyp_map.get(design.hypothesis_id)))
        return results

    # -- observation by scope -----------------------------------------------------

    def _observe(self, design: ExperimentDesign, ctx: Dict[str, Any],
                 ) -> "tuple[str, Dict[str, Any], str, float]":
        """Returns (observation text, metric deltas, evidence type, conf)."""
        metric = design.metrics[0] if design.metrics else "metric"
        before = dict(ctx.get("before") or ctx)
        after = dict(ctx.get("after") or {})

        # Scope-specific bounded interaction (best-effort; falls back to the
        # provided before/after context for deterministic internal analysis).
        if design.scope == ExperimentScope.NURSERY_SIMULATION \
                and self.nursery is not None and not after:
            after = self._run_nursery(design, before)
        elif design.scope == ExperimentScope.LATENT_REPLAY \
                and self.latent is not None and not after:
            after = dict(before)  # offline replay leaves production untouched

        before_v = self._metric_value(metric, before)
        after_v = self._metric_value(metric, after) if after else None
        evidence_type = scope_to_evidence_type(design.scope)

        if after_v is None or before_v is None:
            return ("insufficient evidence within the bound to decide",
                    {metric: {"before": before_v, "after": after_v}},
                    EvidenceType.INCONCLUSIVE, 0.3)

        delta = round(after_v - before_v, 6)
        direction = _METRIC_DIRECTION.get(metric, +1)
        supports = (delta > _EPS) if direction > 0 else (delta < -_EPS)
        falsifies = (delta < -_EPS) if direction > 0 else (delta > _EPS)
        deltas = {metric: {"before": before_v, "after": after_v,
                           "delta": delta}}
        # Offline scopes never yield "real" supporting verdicts.
        if supports:
            base_type = (evidence_type
                         if evidence_type not in (EvidenceType.INCONCLUSIVE,)
                         else EvidenceType.SUPPORTING)
            etype = (EvidenceType.LATENT_REPLAY
                     if design.scope == ExperimentScope.LATENT_REPLAY
                     else EvidenceType.OFFLINE_SIMULATED
                     if design.scope == ExperimentScope.INTERNAL_TRACE_ANALYSIS
                     else EvidenceType.SUPPORTING
                     if design.scope == ExperimentScope.READ_ONLY_STREAM_OBSERVATION
                     else EvidenceType.NURSERY_SIMULATED)
            return (f"{metric} moved as expected ({delta:+})",
                    deltas, etype, 0.6)
        if falsifies:
            return (f"{metric} moved opposite to the expectation ({delta:+})",
                    deltas, EvidenceType.FALSIFYING, 0.55)
        return (f"{metric} did not move decisively ({delta:+})",
                deltas, EvidenceType.INCONCLUSIVE, 0.4)

    def _run_nursery(self, design: ExperimentDesign,
                     before: Dict[str, Any]) -> Dict[str, Any]:
        """Run a bounded nursery interaction; observe the relevant metric."""
        nursery = self.nursery
        steps = min(design.max_steps, 60)
        base_step = int(before.get("step", 0) or 0)
        for i in range(steps):
            nursery.stimulus_provider(base_step + i)
        # The nursery's own sampling hook is the bounded intervention surface.
        if design.intervention_plan and design.intervention_plan.interventions:
            itype = design.intervention_plan.interventions[0].intervention_type
            mapped = {"introduce_novelty": "seek_novelty",
                      "trigger_delayed_consequence": "focus_delayed_"
                                                     "consequence",
                      "repeat_pattern": "sample_known_pattern",
                      "withhold_signal": "seek_absence"}.get(itype, "look")
            try:
                nursery.sample(mapped)
            except Exception:  # sampling is best-effort, never fatal
                pass
        summary = nursery.summary()
        after = dict(before)
        after["mysterium_pressure"] = before.get("mysterium_pressure", 0.0)
        after["structural_change_score"] = before.get(
            "structural_change_score", 0.0)
        after["anomaly_rate"] = summary.get("anomaly_rate", 0.0)
        after["delay_steps"] = float(
            summary.get("delayed_consequence_group_count", 0))
        return after

    @staticmethod
    def _metric_value(metric: str, ctx: Dict[str, Any]) -> Optional[float]:
        if metric in ctx:
            try:
                return float(ctx[metric])
            except (TypeError, ValueError):
                return None
        wm = ctx.get("world_model") or {}
        proto = ctx.get("proto_language") or {}
        if metric == "prediction_accuracy" and "prediction_accuracy" in wm:
            return _num(wm, "prediction_accuracy")
        if metric == "edge_weight" and "edge_weight" in wm:
            return _num(wm, "edge_weight")
        if metric == "ambiguity_score" and "ambiguity_score" in proto:
            return _num(proto, "ambiguity_score")
        return None

    # -- helpers ------------------------------------------------------------------

    def _block(self, design: ExperimentDesign,
               result: HypothesisTestResult,
               hypothesis: Optional[Hypothesis], reason: str,
               unsafe: bool = False) -> HypothesisTestResult:
        result.blocked = True
        result.executed = False
        result.blocked_reason = reason
        result.status = (HypothesisStatus.UNSAFE_TO_TEST if unsafe
                         else HypothesisStatus.SCHEDULED)
        if hypothesis is not None and unsafe:
            hypothesis.set_status(HypothesisStatus.UNSAFE_TO_TEST)
        self.last_result = result
        self._persist(result)
        return result

    def _persist(self, result: HypothesisTestResult) -> None:
        if self.write_log and self.tests_path is not None:
            self.tests_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.tests_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(result.to_dict(), default=str) + "\n")

    def snapshot(self) -> Dict[str, Any]:
        return {
            "tests_run": self.tests_run,
            "unsafe_count": self.unsafe_count,
            "inconclusive_count": self.inconclusive_count,
            "evidence": self.evidence_ledger.snapshot(),
            "falsification": self.falsification.snapshot(),
            "safety": self.safety.snapshot(),
            "last_result": (self.last_result.to_dict()
                            if self.last_result else None),
        }
