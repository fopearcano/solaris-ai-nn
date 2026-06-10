"""Evaluation layer: benchmarks, metrics, scoring, reproducibility, baselines.

The measurement layer. Every run has a manifest; every claim has a metric;
every score has an explanation (or a None with a reason); there is no
consciousness score and never will be.
"""

from .artifacts import ArtifactCollector  # noqa: F401
from .baselines import ALL_BASELINES, run_all_baselines  # noqa: F401
from .benchmark import (  # noqa: F401
    BenchmarkRun,
    BenchmarkSuite,
    ExperimentManifest,
    ExperimentResult,
)
from .comparison import (  # noqa: F401
    compare_embodied_vs_observe_only,
    compare_language_enabled_vs_disabled,
    compare_plasticity_modes,
    compare_substrates,
)
from .experiment_registry import ExperimentRegistry  # noqa: F401
from .failure_analysis import FailureAnalyzer, Finding  # noqa: F401
from .protocols import PROTOCOLS  # noqa: F401
from .reproducibility import (  # noqa: F401
    ReproducibilityReport,
    check_seed_stability,
    compare_runs,
    compute_reproducibility_hash,
)
from .runner import BenchmarkRunner  # noqa: F401
from .scoring import EvaluationScore, score_from_metrics  # noqa: F401

__all__ = [
    "ExperimentManifest", "ExperimentResult", "BenchmarkRun", "BenchmarkSuite",
    "ExperimentRegistry", "BenchmarkRunner", "PROTOCOLS",
    "EvaluationScore", "score_from_metrics",
    "compute_reproducibility_hash", "compare_runs", "check_seed_stability",
    "ReproducibilityReport",
    "compare_substrates", "compare_plasticity_modes",
    "compare_embodied_vs_observe_only", "compare_language_enabled_vs_disabled",
    "ALL_BASELINES", "run_all_baselines",
    "FailureAnalyzer", "Finding", "ArtifactCollector",
]
