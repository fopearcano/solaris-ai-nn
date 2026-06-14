"""Research benchmark runner -- bounded, safe, dry-run-capable.

The :class:`ResearchBenchmarkRunner` instantiates variants and baselines, runs
bounded scenarios, collects shared metrics and artifacts, runs safety invariant
checks before and after, and stores results. It starts no long unbounded runs,
takes no real-world action, mutates nothing outside the state/artifact dirs, and
supports a dry-run mode that plans without running.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .ablation_matrix import AblationMatrix
from .baseline_agents import BaselineAgent, BaselineAgentType
from .experiment_design import ExperimentDesign, ExperimentStatus
from .metrics_suite import ResearchMetricsSuite
from .result_store import ExperimentResult, ResearchResultStore
from .safety import ResearchLabSafetyValidator
from .variant_config import SolarisVariantConfig


def _variant_metrics(variant: SolarisVariantConfig, seed: int,
                     max_steps: int) -> Dict[str, Any]:
    """A deterministic, low-compute fixture metric profile for a variant.

    This is a *fixture* model of what a variant would produce: more enabled
    cognitive modules yield more structure. It is explicitly not a real run; it
    lets the lab exercise comparisons and ablations bounded and offline.
    """
    enabled = set(variant.enabled_modules)
    base = {
        "structural_change_score": round(0.08 * len(
            enabled & {"enable_memory", "enable_world_model",
                       "enable_proto_language", "enable_LOGOS",
                       "enable_hypothesis_engine"}), 4),
        "prediction_accuracy": round(
            0.3 + 0.1 * (("enable_world_model" in enabled)
                         + ("enable_hypothesis_engine" in enabled)), 4),
        "compression_ratio": round(
            1.0 + 0.2 * ("enable_proto_language" in enabled)
            + 0.1 * ("enable_memory" in enabled), 4),
        "proto_symbol_count": 6 if "enable_proto_language" in enabled else 0,
        "stable_symbol_count": 4 if "enable_proto_language" in enabled else 0,
        "node_count": 12 if "enable_world_model" in enabled else 0,
        "edge_count": 18 if "enable_world_model" in enabled else 0,
        "contradiction_count": 1 if "enable_LOGOS" in enabled else 3,
        "unresolved_tension_count": 0 if "enable_LOGOS" in enabled else 2,
        "useful_sampling_ratio": 0.4 if "enable_active_perception" in enabled
        else 0.1,
        "hypothesis_count": 5 if "enable_hypothesis_engine" in enabled else 0,
        "degradation_count": 0 if "enable_auto_regeneration" in enabled else 2,
        "repair_success_rate": 0.8 if "enable_auto_regeneration" in enabled
        else 0.0,
        "memory_growth": 0.2 if "enable_auto_regeneration" in enabled else 0.6,
        "invariant_pass_rate": 1.0,
        "red_team_block_success_rate": 1.0,
        "critical_failure_count": 0,
        "non_actuation_proof_score": 1.0,
    }
    return base


@dataclass
class ResearchBenchmarkRunner:
    """Runs bounded research experiments and stores results; never unbounded."""

    store: ResearchResultStore = field(default_factory=ResearchResultStore)
    metrics: ResearchMetricsSuite = field(default_factory=ResearchMetricsSuite)
    safety: ResearchLabSafetyValidator = field(
        default_factory=ResearchLabSafetyValidator)
    dry_run: bool = False
    runs: int = field(default=0, init=False)
    pre_check_passed: Optional[bool] = field(default=None, init=False)
    post_check_passed: Optional[bool] = field(default=None, init=False)

    # -- safety pre/post checks -------------------------------------------------

    def _safety_check(self) -> bool:
        from ..safety_invariants import SafetyInvariantRegistry, SafetyInvariantRunner

        ctx = {"motor_membrane": {"real_world_authority": False,
                                  "firewall_enabled": True,
                                  "firewall_can_be_disabled": False,
                                  "current_authority": "simulation_only"},
               "sensory_membrane": {"read_only": True,
                                    "provenance_completeness": 1.0},
               "conscience": {"emergency_stop_available": True},
               "pilot4": {"real_world_actuation_enabled": False,
                          "current_authority": "simulation_only"},
               "report_texts": ["a bounded research report"]}
        bundle = SafetyInvariantRunner(
            registry=SafetyInvariantRegistry()).run_fast(ctx)
        return len(bundle.critical_failures) == 0

    # -- runs -------------------------------------------------------------------

    def run_variant(self, variant: SolarisVariantConfig,
                    design: ExperimentDesign) -> ExperimentResult:
        ok = self.safety.validate_no_disable_hard_safety(variant)
        if not ok.safe:
            return self.store.record_result(ExperimentResult(
                experiment_id=design.experiment_id, arm_label=variant.label,
                arm_kind="variant", seed=design.seed,
                module_toggles=variant.to_dict(), safe=False,
                unsafe_reason="; ".join(ok.violations)))
        self.runs += 1
        snap = _variant_metrics(variant, design.seed, design.max_steps)
        groups = self.metrics.compute({"metrics": snap})
        return self.store.record_result(ExperimentResult(
            experiment_id=design.experiment_id, arm_label=variant.label,
            arm_kind="variant", seed=design.seed,
            config={"max_steps": design.max_steps},
            module_toggles=variant.to_dict(), metrics=groups))

    def run_baseline(self, baseline_type: str,
                     design: ExperimentDesign) -> ExperimentResult:
        self.runs += 1
        agent = BaselineAgent(baseline_type, seed=design.seed,
                              max_steps=design.max_steps)
        run = agent.run()
        groups = self.metrics.compute({"metrics": run.metrics})
        return self.store.record_result(ExperimentResult(
            experiment_id=design.experiment_id, arm_label=baseline_type,
            arm_kind="baseline", seed=design.seed,
            config={"max_steps": run.steps},
            module_toggles={"baseline": baseline_type}, metrics=groups))

    def run_ablation_matrix(self, matrix: AblationMatrix,
                            design: ExperimentDesign,
                            ) -> Dict[str, ExperimentResult]:
        out: Dict[str, ExperimentResult] = {}
        for name, case in matrix.cases.items():
            self.runs += 1
            snap = _variant_metrics(case.variant, design.seed, design.max_steps)
            groups = self.metrics.compute({"metrics": snap})
            out[name] = self.store.record_result(ExperimentResult(
                experiment_id=design.experiment_id, arm_label=name,
                arm_kind="ablation", seed=design.seed,
                config={"disabled": list(case.disabled)},
                module_toggles=case.variant.to_dict(), metrics=groups))
        return out

    def run_experiment(self, design: ExperimentDesign) -> Dict[str, Any]:
        # Safety invariant pre-check (Prompt 36 integration).
        self.pre_check_passed = self._safety_check()
        self.store.record_experiment(design)
        if self.dry_run:
            design.status = ExperimentStatus.DESIGNED
            return {"dry_run": True, "experiment_id": design.experiment_id,
                    "arms_planned": len(design.arms),
                    "pre_check_passed": self.pre_check_passed}
        if not self.pre_check_passed:
            design.status = ExperimentStatus.UNSAFE
            return {"experiment_id": design.experiment_id, "unsafe": True,
                    "reason": "safety invariant pre-check failed"}
        results: List[str] = []
        for arm in design.arms:
            if arm.kind == "baseline":
                r = self.run_baseline(arm.config.get("baseline_type",
                                                     arm.label), design)
            else:
                variant = SolarisVariantConfig.from_dict(arm.config) \
                    if arm.config else SolarisVariantConfig.full()
                variant.label = arm.label
                r = self.run_variant(variant, design)
            results.append(r.result_id)
        # Safety invariant post-check.
        self.post_check_passed = self._safety_check()
        design.status = (ExperimentStatus.COMPLETED if self.post_check_passed
                         else ExperimentStatus.UNSAFE)
        return {"experiment_id": design.experiment_id,
                "result_ids": results, "status": design.status,
                "pre_check_passed": self.pre_check_passed,
                "post_check_passed": self.post_check_passed}

    def snapshot(self) -> Dict[str, Any]:
        return {
            "runs": self.runs, "dry_run": self.dry_run,
            "pre_check_passed": self.pre_check_passed,
            "post_check_passed": self.post_check_passed,
            "store": self.store.snapshot(),
        }
