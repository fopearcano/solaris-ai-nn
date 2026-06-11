"""Homeostasis: the need economy between Stimulus and Desire.

Solaris_Ai treats Will as Need. This package implements the missing internal
calculus as bounded, inspectable machinery: normalized homeostatic variables
become need pressures, needs aggregate into ten drive channels, feedback
becomes valence (polarity, not emotion), continuity facts become operational
Being/Not-Being tension, conflicts resolve on a fixed safety-first ladder,
and what survives is synthesized into formal Desire candidates that bias --
never command -- the neural bridge. No will, no feelings, no free agency:
pressure numbers with receipts, under governance at all times.
"""

from .auto_determination import (  # noqa: F401
    ActionImplication,
    AutoDeterminationEngine,
    AutoDeterminationState,
    BeingNotBeingTension,
)
from .conflict import (  # noqa: F401
    RESOLUTION_PRIORITY,
    ConflictResolver,
    NeedConflict,
)
from .desire_synthesis import (  # noqa: F401
    DESIRE_PROPOSALS,
    DesireCandidate,
    DesireSynthesisEngine,
)
from .drives import (  # noqa: F401
    DRIVE_CATEGORIES,
    Drive,
    DriveResolver,
    DriveState,
)
from .need_memory import NeedMemory, NeedTrace  # noqa: F401
from .needs import (  # noqa: F401
    NEED_TO_DESIRES,
    Need,
    NeedEstimator,
    NeedState,
    NeedType,
)
from .regulation import (  # noqa: F401
    HomeostaticRegulationResult,
    HomeostaticRegulator,
)
from .reports import (  # noqa: F401
    HOMEOSTASIS_LIMITATIONS,
    HomeostasisQueryInterface,
    HomeostasisReportBuilder,
)
from .safety import (  # noqa: F401
    ALLOWED_PROPOSALS,
    HomeostasisSafetyReport,
    HomeostasisSafetyValidator,
)
from .valence import ValenceEstimator, ValenceState  # noqa: F401
from .variables import (  # noqa: F401
    VARIABLE_GROUPS,
    HomeostaticState,
    HomeostaticVariable,
    VariableRange,
    VariableTrend,
    clamp01,
    normalize,
)

__all__ = [
    "HomeostaticVariable", "HomeostaticState", "VariableRange",
    "VariableTrend", "VARIABLE_GROUPS", "clamp01", "normalize",
    "Need", "NeedState", "NeedType", "NeedEstimator", "NEED_TO_DESIRES",
    "Drive", "DriveState", "DriveResolver", "DRIVE_CATEGORIES",
    "ValenceEstimator", "ValenceState",
    "HomeostaticRegulator", "HomeostaticRegulationResult",
    "AutoDeterminationEngine", "AutoDeterminationState",
    "BeingNotBeingTension", "ActionImplication",
    "NeedConflict", "ConflictResolver", "RESOLUTION_PRIORITY",
    "DesireCandidate", "DesireSynthesisEngine", "DESIRE_PROPOSALS",
    "NeedTrace", "NeedMemory",
    "HomeostasisSafetyValidator", "HomeostasisSafetyReport",
    "ALLOWED_PROPOSALS",
    "HomeostasisReportBuilder", "HomeostasisQueryInterface",
    "HOMEOSTASIS_LIMITATIONS",
]
