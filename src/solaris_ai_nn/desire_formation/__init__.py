"""Desire formation -- operational pressure toward internal action readiness.

Prompts 41-50 gave Solaris perception, metabolism, proto-concepts, signs,
cognition, and a self/world boundary. This layer adds *desire formation*, where
"desire" means an operational pressure toward an internal action tendency --

    sensory field -> perceptual metabolism -> cognitive pressure -> self-boundary
    state -> valence gradient -> push formation -> desire candidate -> internal
    action readiness -> safe arbitration -> internal action / attention shift /
    simulation / consolidation / no-op -> result becomes new trace

This connects sensorium-native cognition back to the Solaris spine (Stimulus ->
Push -> Desire -> ActionCandidate -> Reaction/Trace). Desire here is NOT emotion,
NOT human wanting, NOT conscious intention, and NOT free will. Valence is
operational priority, not feeling. Internal actions affect only internal state:
nothing here controls hardware, feeders, the network, a shell, a source, or the
real world; safety and governance have veto power; and no claim of emotion, free
will, agency, consciousness, sentience, life, or subjective experience is made.
"""

from __future__ import annotations

from .arbitration import (
    ArbitrationOutcome,
    ArbitrationPolicy,
    ArbitrationResult,
    DesireArbitrator,
)
from .conflict import ConflictDetector, ConflictType, DesireConflict
from .desire import (
    DesireCandidate,
    DesireFormationEngine,
    DesireKind,
    DesireStatus,
)
from .desire_memory import (
    DesireMemoryRecord,
    DesireMemoryStore,
    DesireTraceIndex,
)
from .desire_runtime import DesireFormationRuntime, DesireMilestone
from .internal_actions import (
    InternalAction,
    InternalActionExecutor,
    InternalActionKind,
)
from .motivation_field import (
    MotivationField,
    MotivationFieldState,
    MotivationVector,
)
from .outcome_trace import DesireOutcome, DesireOutcomeTrace, OutcomeType
from .push import (
    PushFormationEngine,
    PushIntensity,
    PushSource,
    SensoriumPush,
)
from .readiness import ActionReadiness, ReadinessGate, ReadinessState
from .reports import DesireFormationReportBuilder
from .safety import HARD_RULES, DesireFormationSafetyValidator
from .valence import (
    SensoriumValence,
    ValenceAssessment,
    ValenceDirection,
    ValenceGradient,
    ValenceSource,
)

__all__ = [
    "ArbitrationOutcome", "ArbitrationPolicy", "ArbitrationResult",
    "DesireArbitrator",
    "ConflictDetector", "ConflictType", "DesireConflict",
    "DesireCandidate", "DesireFormationEngine", "DesireKind", "DesireStatus",
    "DesireMemoryRecord", "DesireMemoryStore", "DesireTraceIndex",
    "DesireFormationRuntime", "DesireMilestone",
    "InternalAction", "InternalActionExecutor", "InternalActionKind",
    "MotivationField", "MotivationFieldState", "MotivationVector",
    "DesireOutcome", "DesireOutcomeTrace", "OutcomeType",
    "PushFormationEngine", "PushIntensity", "PushSource", "SensoriumPush",
    "ActionReadiness", "ReadinessGate", "ReadinessState",
    "DesireFormationReportBuilder",
    "HARD_RULES", "DesireFormationSafetyValidator",
    "SensoriumValence", "ValenceAssessment", "ValenceDirection",
    "ValenceGradient", "ValenceSource",
]
