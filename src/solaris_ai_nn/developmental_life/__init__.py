"""Long-horizon developmental runtime -- structural change over time, not life.

Prompts 41-52 gave Solaris a complete internal loop (stimulus -> push -> desire ->
internal action -> reaction -> consequence -> memory -> habit -> changed future
perception). This layer stretches that loop across long time:

    bounded developmental cycles -> life-cycle phases -> epochs -> growth state ->
    maturation markers -> phase transitions -> plateaus -> regressions ->
    growth-vs-accumulation -> persistent life history -> changed future perception

It is a long-duration developmental *substrate*, not a product release, an
intelligence benchmark, or a consciousness test. "Life cycle", "maturation", and
"life history" are operational runtime language. Growth means *structural change*
(which may include pruning, decay, inhibition, and no-op learning), not an
intelligence score; negative, plateau, regression, and inconclusive results are
preserved. Nothing here uses a human teaching loop, controls hardware/feeders/the
network/a shell/an OS device, modifies a source, or actuates the real world, and no
claim of biological life, consciousness, sentience, personhood, agency, free will,
emotion, feeling, understanding, or subjective experience is made.
"""

from __future__ import annotations

from .developmental_epoch import (
    DevelopmentalEpoch,
    EpochBoundary,
    EpochSummary,
    EpochTransitionReason,
)
from .developmental_memory import (
    DevelopmentalIndex,
    DevelopmentalMemoryRecord,
    DevelopmentalMemoryStore,
)
from .developmental_runtime import LongHorizonDevelopmentalRuntime
from .growth_state import (
    DevelopmentalGrowthState,
    GrowthDimension,
    GrowthSignal,
)
from .life_cycle import (
    LifeCycleClock,
    LifeCycleEvent,
    LifeCyclePhase,
    LifeCycleState,
)
from .life_history import (
    LifeHistoryBuilder,
    LifeHistoryEvent,
    LifeHistoryEventKind,
    OperationalLifeHistory,
)
from .maturation import (
    MaturationDetector,
    MaturationMarker,
    MaturationMarkerType,
)
from .phase_transition import (
    DevelopmentalPhaseTransition,
    PhaseTransitionDetector,
    PhaseTransitionEvidence,
)
from .plateau import DevelopmentalPlateau, PlateauDetector, PlateauReason
from .regression import (
    DevelopmentalRegression,
    RegressionDetector,
    RegressionReason,
)
from .reports import DevelopmentalLifeReportBuilder
from .safety import HARD_RULES, DevelopmentalLifeSafetyValidator
from .structural_growth import (
    GrowthVerdict,
    GrowthVsAccumulationResult,
    StructuralGrowthAnalyzer,
    StructuralGrowthReport,
)

__all__ = [
    "DevelopmentalEpoch", "EpochBoundary", "EpochSummary",
    "EpochTransitionReason",
    "DevelopmentalIndex", "DevelopmentalMemoryRecord",
    "DevelopmentalMemoryStore",
    "LongHorizonDevelopmentalRuntime",
    "DevelopmentalGrowthState", "GrowthDimension", "GrowthSignal",
    "LifeCycleClock", "LifeCycleEvent", "LifeCyclePhase", "LifeCycleState",
    "LifeHistoryBuilder", "LifeHistoryEvent", "LifeHistoryEventKind",
    "OperationalLifeHistory",
    "MaturationDetector", "MaturationMarker", "MaturationMarkerType",
    "DevelopmentalPhaseTransition", "PhaseTransitionDetector",
    "PhaseTransitionEvidence",
    "DevelopmentalPlateau", "PlateauDetector", "PlateauReason",
    "DevelopmentalRegression", "RegressionDetector", "RegressionReason",
    "DevelopmentalLifeReportBuilder",
    "HARD_RULES", "DevelopmentalLifeSafetyValidator",
    "GrowthVerdict", "GrowthVsAccumulationResult", "StructuralGrowthAnalyzer",
    "StructuralGrowthReport",
]
