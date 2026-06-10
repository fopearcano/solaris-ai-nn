"""Latent cognition: bounded offline processing when input goes quiet.

Sleep/wake modes, a scheduler that respects governance and health, sleep
(consolidation) and dream (sandboxed replay + counterfactual) cycles, an
offline replay engine, anticipation tracking, Mysterium (numeric unknown
pressure), complexity pressure, durable latent memory, latent safety, and a
ClaimGuard-scanned latent report. None of this is consciousness or human
dreaming: it is controlled replay/consolidation inspired by sleep cycles,
and latent modes can never execute external actions.
"""

from .anticipation import (  # noqa: F401
    AnticipationPrediction,
    AnticipationTracker,
    valence_bucket,
)
from .complexity_pressure import (  # noqa: F401
    ComplexityDecision,
    ComplexityPressureMonitor,
    ComplexityReading,
)
from .coordinator import LatentCognition  # noqa: F401
from .counterfactual import (  # noqa: F401
    COUNTERFACTUAL_KINDS,
    CounterfactualGenerator,
)
from .dream_cycle import DreamCycle, DreamCycleResult  # noqa: F401
from .latent_memory import (  # noqa: F401
    ConsolidatedSchema,
    DreamTrace,
    LatentMemoryRecord,
    LatentMemoryStore,
    ReplayTrace,
)
from .latent_report import LATENT_LIMITATIONS, LatentReportBuilder  # noqa: F401
from .modes import (  # noqa: F401
    VALID_TRANSITIONS,
    LatentMode,
    LatentModeState,
    LatentTransition,
    SleepWakeController,
)
from .mysterium import MysteriumState, MysteriumTracker  # noqa: F401
from .offline_replay import (  # noqa: F401
    REPLAY_STRATEGIES,
    OfflineReplayEngine,
    make_sandbox_bridge,
)
from .scheduler import (  # noqa: F401
    LatentDecision,
    LatentScheduleDecision,
    LatentScheduler,
)
from .safety import (  # noqa: F401
    MAX_LATENT_CYCLE_STEPS,
    LatentSafetyReport,
    LatentSafetyValidator,
)
from .sleep_cycle import SleepCycle, SleepCycleResult  # noqa: F401

__all__ = [
    "LatentMode", "LatentModeState", "LatentTransition",
    "SleepWakeController", "VALID_TRANSITIONS",
    "LatentScheduler", "LatentScheduleDecision", "LatentDecision",
    "SleepCycle", "SleepCycleResult",
    "DreamCycle", "DreamCycleResult",
    "OfflineReplayEngine", "REPLAY_STRATEGIES", "make_sandbox_bridge",
    "CounterfactualGenerator", "COUNTERFACTUAL_KINDS",
    "AnticipationTracker", "AnticipationPrediction", "valence_bucket",
    "MysteriumTracker", "MysteriumState",
    "ComplexityPressureMonitor", "ComplexityReading", "ComplexityDecision",
    "LatentMemoryRecord", "LatentMemoryStore", "DreamTrace", "ReplayTrace",
    "ConsolidatedSchema",
    "LatentSafetyValidator", "LatentSafetyReport", "MAX_LATENT_CYCLE_STEPS",
    "LatentReportBuilder", "LATENT_LIMITATIONS",
    "LatentCognition",
]
