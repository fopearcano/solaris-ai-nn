"""Research lab -- baselines, ablations, and evidence-based architecture validation.

Solaris-AI-NN has accumulated many modules and safety layers. This package asks,
scientifically and conservatively, *which of them actually matter*: it runs
bounded baseline agents (random, fixed-policy, single-module), configures
architecture variants, executes an ablation matrix, computes a shared metric
suite, runs null models (could the "growth" be noise or accumulation?), compares
the full system against simpler references, estimates each module's provisional
effect (positive / neutral / harmful / inconclusive), builds reproducibility
packages, and compiles a research report.

The lab is a measurement instrument, not a runtime: it starts no long unbounded
runs, takes no real-world action, holds no external authority, keeps every hard
safety boundary enabled, preserves negative and inconclusive results, and emits
no consciousness/sentience/life score. Benchmark success is operational
evidence, never proof of consciousness, agency, or real-world competence.
"""

from __future__ import annotations

from .ablation_matrix import AblationCase, AblationMatrix, AblationResult
from .baseline_agents import (
    BaselineAgent,
    BaselineAgentType,
    BaselineRunResult,
)
from .benchmark_runner import ResearchBenchmarkRunner
from .comparison import (
    ComparisonConfidence,
    ComparisonEngine,
    ComparisonResult,
    EffectDirection,
    MetricDelta,
)
from .effect_analysis import (
    EffectAnalysis,
    EffectAnalyzer,
    ModuleEffect,
    ModuleValue,
)
from .experiment_design import (
    ExperimentArm,
    ExperimentCondition,
    ExperimentDesign,
    ExperimentProtocol,
    ExperimentStatus,
)
from .leaderboard import (
    LEADERBOARD_DIMENSIONS,
    LeaderboardEntry,
    ResearchLeaderboard,
)
from .metrics_suite import METRIC_GROUPS, ResearchMetricsSuite
from .null_models import NullModel, NullModelResult, NullModelType
from .reproducibility import (
    ResearchReproducibilityBuilder,
    ResearchReproducibilityPackage,
)
from .research_report import ResearchReport, ResearchReportBuilder
from .result_store import (
    ExperimentResult,
    ResearchResultStore,
    RunArtifactIndex,
)
from .safety import HARD_RULES, ResearchLabSafetyValidator, ResearchSafetyReport
from .variant_config import (
    COGNITIVE_TOGGLES,
    SolarisVariantConfig,
    VariantAuthority,
    VariantModuleToggle,
)

__all__ = [
    # design / variant / baseline / ablation
    "ExperimentDesign", "ExperimentCondition", "ExperimentArm",
    "ExperimentProtocol", "ExperimentStatus", "SolarisVariantConfig",
    "VariantAuthority", "VariantModuleToggle", "COGNITIVE_TOGGLES",
    "BaselineAgent", "BaselineAgentType", "BaselineRunResult",
    "AblationMatrix", "AblationCase", "AblationResult",
    # runner / store / metrics
    "ResearchBenchmarkRunner", "ResearchResultStore", "ExperimentResult",
    "RunArtifactIndex", "ResearchMetricsSuite", "METRIC_GROUPS",
    # null / comparison / effect
    "NullModel", "NullModelType", "NullModelResult", "ComparisonEngine",
    "ComparisonResult", "MetricDelta", "EffectDirection", "ComparisonConfidence",
    "EffectAnalyzer", "EffectAnalysis", "ModuleEffect", "ModuleValue",
    # reproducibility / leaderboard / report / safety
    "ResearchReproducibilityBuilder", "ResearchReproducibilityPackage",
    "ResearchLeaderboard", "LeaderboardEntry", "LEADERBOARD_DIMENSIONS",
    "ResearchReportBuilder", "ResearchReport", "ResearchLabSafetyValidator",
    "ResearchSafetyReport", "HARD_RULES",
]
