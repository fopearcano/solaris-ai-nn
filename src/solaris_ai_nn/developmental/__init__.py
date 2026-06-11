"""Developmental long-horizon learning runtime (Prompt 21).

Solaris-AI-NN learns by remaining active across time: continuity,
repetition, prediction failure, Mysterium pressure, consolidation,
pruning, and slow structural drift over days, weeks, months -- later
years. No teacher, no RLHF, no reward button, no batch training. The
central research question: after months of runtime, is the system
structurally different for reasons traceable to its own lived history?
"""

from .autobiographical_memory import (
    AutobiographicalEvent,
    AutobiographicalMemory,
)
from .consolidation_policy import (
    CompressionReport,
    ConsolidationDecision,
    ConsolidationPolicy,
    preservation_rank,
)
from .developmental_runtime import DevelopmentalRuntime
from .drift_monitor import DriftMetric, DriftReport, LongRunDriftMonitor
from .epochs import (
    DevelopmentalEpoch,
    EpochManager,
    EpochState,
    EpochTransition,
)
from .growth_monitor import GrowthMetric, GrowthMonitor, GrowthSnapshot
from .long_horizon_metrics import (
    FORBIDDEN_METRIC_NAMES,
    long_horizon_metrics,
)
from .memory_layers import (
    LayeredMemoryState,
    MemoryItem,
    MemoryLayer,
    MemoryLayerManager,
)
from .milestones import (
    Milestone,
    MilestoneDetector,
    MilestoneRegistry,
    MilestoneType,
)
from .phase_transitions import (
    PhaseTransitionCandidate,
    PhaseTransitionDetector,
)
from .reports import (
    DEVELOPMENTAL_LIMITATIONS,
    DevelopmentalQueryInterface,
    DevelopmentalReportBuilder,
)
from .safety import DevelopmentalSafetyReport, DevelopmentalSafetyValidator
from .timescales import DevelopmentalClock, TimeScale, TimeScaleWindow

__all__ = [
    "AutobiographicalEvent", "AutobiographicalMemory",
    "CompressionReport", "ConsolidationDecision", "ConsolidationPolicy",
    "DEVELOPMENTAL_LIMITATIONS", "DevelopmentalClock",
    "DevelopmentalEpoch", "DevelopmentalQueryInterface",
    "DevelopmentalReportBuilder", "DevelopmentalRuntime",
    "DevelopmentalSafetyReport", "DevelopmentalSafetyValidator",
    "DriftMetric", "DriftReport", "EpochManager", "EpochState",
    "EpochTransition", "FORBIDDEN_METRIC_NAMES", "GrowthMetric",
    "GrowthMonitor", "GrowthSnapshot", "LayeredMemoryState",
    "LongRunDriftMonitor", "MemoryItem", "MemoryLayer",
    "MemoryLayerManager", "Milestone", "MilestoneDetector",
    "MilestoneRegistry", "MilestoneType", "PhaseTransitionCandidate",
    "PhaseTransitionDetector", "TimeScale", "TimeScaleWindow",
    "long_horizon_metrics", "preservation_rank",
]
