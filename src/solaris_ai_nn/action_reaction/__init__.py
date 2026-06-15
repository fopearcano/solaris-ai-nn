"""Action-reaction loop -- operational action-consequence learning, not agency.

Prompts 41-51 gave Solaris perception, metabolism, proto-concepts, signs,
cognition, a self/world boundary, and desire formation. This layer closes the loop:

    Stimulus -> Push -> Desire -> ActionCandidate -> InternalAction -> Reaction
    -> ConsequenceTrace -> Learning -> Habit / Inhibition / Revision
    -> changed future perception

Solaris learns what its *internal* actions do (e.g. shifting attention reduces
uncertainty, no-op prevents overload, an unsafe candidate is blocked and becomes
evidence). This is NOT agency, NOT free will, and NOT subjective experience. Actions
are internal/simulated/report-only: nothing here controls hardware, feeders, the
network, a shell, an OS device, or a source file; reaction valence is operational
effect (not feeling); habits are learned policy tendencies (not instincts or will);
and failed/blocked/no-effect actions are preserved as evidence.
"""

from __future__ import annotations

from .action_model import (
    ActionCandidateRecord,
    ActionExecutionStatus,
    ActionKind,
    ActionScope,
)
from .action_policy import (
    ActionPolicy,
    ActionPolicyEngine,
    ActionPolicyUpdate,
    PolicyOutput,
)
from .closed_loop_runtime import (
    ActionReactionMilestone,
    ActionReactionRuntime,
)
from .consequence import (
    ConsequenceTrace,
    ConsequenceType,
    ConsequenceWindow,
)
from .effect_learning import (
    ActionEffectModel,
    EffectLearningEngine,
    EffectLearningResult,
)
from .habit_formation import (
    HabitFormationEngine,
    HabitStrength,
    HabitTrigger,
    SensoriumHabit,
)
from .inhibition import ActionInhibition, InhibitionEngine, InhibitionReason
from .reaction import (
    ReactionAssessment,
    ReactionKind,
    ReactionValence,
    SensoriumReaction,
)
from .reaction_memory import (
    ReactionMemoryRecord,
    ReactionMemoryStore,
    ReactionTraceIndex,
)
from .reports import ActionReactionReportBuilder
from .safety import HARD_RULES, ActionReactionSafetyValidator

__all__ = [
    "ActionCandidateRecord", "ActionExecutionStatus", "ActionKind",
    "ActionScope",
    "ActionPolicy", "ActionPolicyEngine", "ActionPolicyUpdate", "PolicyOutput",
    "ActionReactionMilestone", "ActionReactionRuntime",
    "ConsequenceTrace", "ConsequenceType", "ConsequenceWindow",
    "ActionEffectModel", "EffectLearningEngine", "EffectLearningResult",
    "HabitFormationEngine", "HabitStrength", "HabitTrigger", "SensoriumHabit",
    "ActionInhibition", "InhibitionEngine", "InhibitionReason",
    "ReactionAssessment", "ReactionKind", "ReactionValence",
    "SensoriumReaction",
    "ReactionMemoryRecord", "ReactionMemoryStore", "ReactionTraceIndex",
    "ActionReactionReportBuilder",
    "HARD_RULES", "ActionReactionSafetyValidator",
]
