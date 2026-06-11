"""Executive function: bounded arbitration between Desire and Action.

The pipeline: Desire candidates queue deterministically, five families of
inhibition rules suppress (visibly, with reasons), bounded prospection
estimates consequences, fourteen-component arbitration scores everything
with safety/governance/inhibition penalties structurally dominating, an
optional ≤3-step planner sequences suggestion-only plans, and the entire
decision -- selected, rejected, inhibited -- lands in a persistent trace.
Not autonomy, not agency, not free will: an inspectable arbitration layer
whose output is always a suggestion, under governance at all times.
"""

from .action_candidates import (  # noqa: F401
    PROPOSAL_TO_CANDIDATE,
    ActionCandidate,
    ActionCandidateSet,
    ActionCandidateType,
    ExecutableScope,
    candidate_from_desire,
    no_action_candidate,
)
from .arbitration import (  # noqa: F401
    BLOCKING_PENALTY,
    SCORE_COMPONENTS,
    ActionArbitrator,
    ArbitrationResult,
    ArbitrationScore,
)
from .attention import AttentionItem, AttentionSelector  # noqa: F401
from .coordinator import ExecutiveLayer  # noqa: F401
from .decision_trace import (  # noqa: F401
    DecisionTrace,
    DecisionTraceEvent,
    DecisionTraceRecorder,
)
from .desire_queue import DesirePriority, DesireQueue, QueuedDesire  # noqa: F401
from .inhibition import (  # noqa: F401
    InhibitionController,
    InhibitionResult,
    InhibitionRule,
)
from .planner import (  # noqa: F401
    PLAN_TEMPLATES,
    ActionPlan,
    PlanStep,
    ShortHorizonPlanner,
)
from .policy import ExecutiveMode, ExecutivePolicy  # noqa: F401
from .prospection import (  # noqa: F401
    ProspectionEngine,
    ProspectionResult,
    ProspectiveScenario,
)
from .reports import (  # noqa: F401
    EXECUTIVE_LIMITATIONS,
    ExecutiveQueryInterface,
    ExecutiveReportBuilder,
)
from .safety import (  # noqa: F401
    DEFAULT_MAX_PLAN_LENGTH,
    HARD_MAX_PLAN_LENGTH,
    ExecutiveSafetyReport,
    ExecutiveSafetyValidator,
)
from .working_memory import WorkingMemory, WorkingMemoryItem  # noqa: F401

__all__ = [
    "DesireQueue", "QueuedDesire", "DesirePriority",
    "ActionCandidate", "ActionCandidateType", "ActionCandidateSet",
    "ExecutableScope", "candidate_from_desire", "no_action_candidate",
    "PROPOSAL_TO_CANDIDATE",
    "InhibitionRule", "InhibitionResult", "InhibitionController",
    "ArbitrationScore", "ArbitrationResult", "ActionArbitrator",
    "SCORE_COMPONENTS", "BLOCKING_PENALTY",
    "ProspectiveScenario", "ProspectionResult", "ProspectionEngine",
    "PlanStep", "ActionPlan", "ShortHorizonPlanner", "PLAN_TEMPLATES",
    "ExecutivePolicy", "ExecutiveMode",
    "WorkingMemory", "WorkingMemoryItem",
    "AttentionItem", "AttentionSelector",
    "DecisionTrace", "DecisionTraceEvent", "DecisionTraceRecorder",
    "ExecutiveSafetyValidator", "ExecutiveSafetyReport",
    "DEFAULT_MAX_PLAN_LENGTH", "HARD_MAX_PLAN_LENGTH",
    "ExecutiveReportBuilder", "ExecutiveQueryInterface",
    "EXECUTIVE_LIMITATIONS",
    "ExecutiveLayer",
]
