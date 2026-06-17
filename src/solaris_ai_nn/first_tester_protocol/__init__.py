"""First tester protocol, session script, acceptance criteria, and handoff (P81).

This package generates the first trusted-tester protocol: the session script, acceptance
criteria, stop conditions, task sheet, artifact handoff guide, and post-test review
template. It is the final operational layer before the first human tester touches the RC.

It is local and documentation-only. It never runs the tester session, publishes, uploads,
creates GitHub issues/releases/tags, installs packages, starts/controls feeders, controls
hardware, accesses the network/shell/Git/GitHub/browser/OS, opens a browser, executes
artifact contents, trains on tester feedback, allows raw-event or membrane bypass, or
makes a claim of consciousness, sentience, biological life, personhood, agency, free will,
emotion, feeling, understanding, self-awareness, autonomous self-improvement, autonomous
intent, autonomous desire, or real-world autonomy.
"""

from __future__ import annotations

from .acceptance_criteria import (
    AcceptanceCategory,
    AcceptanceCriterion,
    AcceptanceResult,
    FirstTesterAcceptanceCriteria,
)
from .artifact_handoff import (
    FirstTesterArtifactHandoff,
    HandoffArtifact,
    HandoffBundleGuide,
    HandoffPrivacyLevel,
)
from .post_test_review import (
    FirstTesterPostTestReview,
    PostTestReviewQuestion,
    PostTestReviewSummary,
)
from .protocol_profile import (
    DEFAULT_PROFILE_ID,
    FirstTesterProtocolConstraint,
    FirstTesterProtocolMode,
    FirstTesterProtocolProfile,
    available_profiles,
    default_protocol_profile,
    get_protocol_profile,
)
from .reports import FirstTesterProtocolReportBuilder
from .safety import HARD_RULES, FirstTesterProtocolSafetyValidator
from .session_script import (
    FirstTesterSessionScript,
    SessionPhase,
    SessionStep,
    SessionStepStatus,
)
from .stop_conditions import (
    FirstTesterStopConditions,
    StopCondition,
    StopSeverity,
)
from .tester_protocol_runtime import FirstTesterProtocolRuntime, SessionStatus
from .tester_task_sheet import (
    FirstTesterTaskSheet,
    TesterTask,
    TesterTaskStatus,
)

__all__ = [
    "HARD_RULES", "FirstTesterProtocolSafetyValidator",
    "FirstTesterProtocolProfile", "FirstTesterProtocolMode",
    "FirstTesterProtocolConstraint", "default_protocol_profile",
    "get_protocol_profile", "available_profiles", "DEFAULT_PROFILE_ID",
    "FirstTesterSessionScript", "SessionStep", "SessionStepStatus",
    "SessionPhase",
    "FirstTesterAcceptanceCriteria", "AcceptanceCriterion", "AcceptanceResult",
    "AcceptanceCategory",
    "FirstTesterStopConditions", "StopCondition", "StopSeverity",
    "FirstTesterArtifactHandoff", "HandoffArtifact", "HandoffBundleGuide",
    "HandoffPrivacyLevel",
    "FirstTesterTaskSheet", "TesterTask", "TesterTaskStatus",
    "FirstTesterPostTestReview", "PostTestReviewQuestion",
    "PostTestReviewSummary",
    "FirstTesterProtocolRuntime", "SessionStatus",
    "FirstTesterProtocolReportBuilder",
]
