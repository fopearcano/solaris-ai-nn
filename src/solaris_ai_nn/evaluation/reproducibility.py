"""Reproducibility: hashing, run comparison, seed stability checks.

An adaptive system that cannot be re-run is folklore. The hash pins what was
configured; `compare_runs` measures whether two runs with the same seed produced
the same numbers within tolerance; `check_seed_stability` does it end to end.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .benchmark import ExperimentManifest, ExperimentResult

DEFAULT_TOLERANCE = 1e-6

# Metric keys compared numerically between same-seed runs (dotted paths).
_COMPARED = [
    "continuity.heartbeat_count",
    "reactivity.stimulus_count",
    "reactivity.reaction_count",
    "adaptation.prediction_error_end",
    "substrate.state_norm",
]


def _dig(data: Dict[str, Any], path: str) -> Any:
    node: Any = data
    for part in path.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node


def compute_reproducibility_hash(manifest: ExperimentManifest,
                                 trace_summary: Optional[Dict[str, Any]] = None,
                                 config: Optional[Dict[str, Any]] = None) -> str:
    """Stable sha256 over the reproduction-relevant facts of a run."""
    payload = {
        "name": manifest.name,
        "seed": manifest.seed,
        "substrate": manifest.substrate,
        "substrate_config": manifest.substrate_config,
        "run_config": manifest.run_config,
        "enabled_features": manifest.enabled_features,
        "max_steps": manifest.max_steps,
        "trace_summary": trace_summary or {},
        "config": config or {},
    }
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


@dataclass
class ReproducibilityReport:
    """Outcome of comparing two runs of the same experiment."""

    same_seed: bool
    match: bool
    metric_deltas: Dict[str, Optional[float]] = field(default_factory=dict)
    trace_length_delta: Optional[int] = None
    action_count_delta: Optional[int] = None
    state_norm_delta: Optional[float] = None
    warnings: List[str] = field(default_factory=list)
    tolerance: float = DEFAULT_TOLERANCE

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


def compare_runs(result_a: ExperimentResult,
                 result_b: ExperimentResult,
                 tolerance: float = DEFAULT_TOLERANCE) -> ReproducibilityReport:
    """Numeric comparison of two results (same experiment expected)."""
    same_seed = result_a.manifest.seed == result_b.manifest.seed
    deltas: Dict[str, Optional[float]] = {}
    mismatched: List[str] = []
    for path in _COMPARED:
        va, vb = _dig(result_a.metrics, path), _dig(result_b.metrics, path)
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            delta = abs(float(va) - float(vb))
            deltas[path] = round(delta, 9)
            if delta > tolerance:
                mismatched.append(f"{path}: {va} vs {vb}")
        else:
            deltas[path] = None

    trace_a = _dig(result_a.metrics, "continuity.trace_continuity_ratio")
    trace_b = _dig(result_b.metrics, "continuity.trace_continuity_ratio")
    trace_delta = (abs(trace_a - trace_b)
                   if isinstance(trace_a, (int, float))
                   and isinstance(trace_b, (int, float)) else None)
    norm_delta = deltas.get("substrate.state_norm")
    actions_a = _dig(result_a.metrics, "reactivity.executed_action_count")
    actions_b = _dig(result_b.metrics, "reactivity.executed_action_count")
    action_delta = (abs(int(actions_a) - int(actions_b))
                    if actions_a is not None and actions_b is not None else None)

    warnings = []
    if not same_seed:
        warnings.append("runs used different seeds; mismatch is expected")
    if same_seed and mismatched:
        warnings.append("nondeterminism exceeds tolerance: "
                        + "; ".join(mismatched))
    return ReproducibilityReport(
        same_seed=same_seed,
        match=same_seed and not mismatched,
        metric_deltas=deltas,
        trace_length_delta=None if trace_delta is None else int(trace_delta * 1e6),
        action_count_delta=action_delta,
        state_norm_delta=norm_delta,
        warnings=warnings,
        tolerance=tolerance,
    )


def check_seed_stability(experiment_name: str, seed: int, repeats: int = 2,
                         steps: int = 60, runner: Any = None) -> ReproducibilityReport:
    """Run an experiment ``repeats`` times with one seed; compare the runs."""
    if runner is None:
        from .runner import BenchmarkRunner

        runner = BenchmarkRunner()
    results = [runner.run_experiment(experiment_name,
                                     {"seed": seed, "steps": steps})
               for _ in range(max(2, repeats))]
    report = compare_runs(results[0], results[1])
    for extra in results[2:]:
        follow = compare_runs(results[0], extra)
        report.warnings.extend(follow.warnings)
        report.match = report.match and follow.match
    return report
