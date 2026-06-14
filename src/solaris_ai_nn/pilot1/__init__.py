"""Pilot-1 -- the month-scale soak protocol, observability, and runbook.

This package is the *operational framework* for Solaris-AI-NN's first serious
long-horizon test window. It can plan a pilot, run preflight checks, estimate
and budget resources, collect a low-overhead observability stream, render a
health dashboard, write daily/weekly reviews, rehearse restart drills, detect
failure modes, evaluate exit criteria, generate an operator runbook, and build
a claim-guarded pilot report.

It deliberately does **not** start a real month-long run automatically, does
not confuse simulated time with real time, and never treats operational
success as proof of consciousness. Real long-scale runs require explicit
governance approval; the emergency stop, ClaimGuard, safety, governance, and
auto-regeneration safety are never bypassed.
"""

from __future__ import annotations

from .daily_review import DailyRecommendation, DailyReview, DailyReviewBuilder
from .exit_criteria import (
    ExitCriterion,
    ExitDecision,
    ExitDecisionType,
    PilotExitCriteria,
)
from .failure_modes import (
    FailureMode,
    FailureModeDetector,
    FailureModeThresholds,
    FailureModeType,
    FailureSeverity,
    RecommendedAction,
)
from .health_dashboard import PilotHealthDashboard, PilotHealthState
from .observability import (
    METRIC_KEYS,
    ObservationEvent,
    ObservationStream,
    PilotObservabilityCollector,
)
from .operator_runbook import WARNINGS, OperatorRunbookBuilder
from .pilot_config import (
    DEFAULT_PILOT_DIR,
    PilotAuthority,
    PilotConfig,
    PilotEnvironment,
    PilotMode,
)
from .pilot_protocol import (
    PilotPhase,
    PilotPhaseRecord,
    PilotPhaseStatus,
    PilotProtocol,
    PilotProtocolState,
)
from .pilot_report import PilotReport, PilotReportBuilder
from .resource_budget import (
    ResourceBudget,
    ResourceBudgetEstimate,
    ResourceBudgetMonitor,
)
from .restart_drills import (
    DrillOutcome,
    RestartDrill,
    RestartDrillResult,
    RestartDrillRunner,
    RestartDrillType,
)
from .retention_policy import RetentionCategory, RetentionDecision, RetentionPolicy
from .safety import HARD_RULES, PilotSafetyReport, PilotSafetyValidator
from .weekly_review import WeeklyReview, WeeklyReviewBuilder

__all__ = [
    # config / safety
    "PilotConfig", "PilotMode", "PilotAuthority", "PilotEnvironment",
    "DEFAULT_PILOT_DIR", "PilotSafetyValidator", "PilotSafetyReport",
    "HARD_RULES",
    # protocol
    "PilotProtocol", "PilotPhase", "PilotPhaseStatus", "PilotProtocolState",
    "PilotPhaseRecord",
    # observability / dashboard
    "PilotObservabilityCollector", "ObservationEvent", "ObservationStream",
    "METRIC_KEYS", "PilotHealthDashboard", "PilotHealthState",
    # resources / retention
    "ResourceBudget", "ResourceBudgetEstimate", "ResourceBudgetMonitor",
    "RetentionPolicy", "RetentionDecision", "RetentionCategory",
    # reviews
    "DailyReview", "DailyReviewBuilder", "DailyRecommendation",
    "WeeklyReview", "WeeklyReviewBuilder",
    # drills / failures / exit
    "RestartDrill", "RestartDrillResult", "RestartDrillRunner",
    "RestartDrillType", "DrillOutcome",
    "FailureMode", "FailureModeDetector", "FailureModeType",
    "FailureModeThresholds", "FailureSeverity", "RecommendedAction",
    "PilotExitCriteria", "ExitCriterion", "ExitDecision", "ExitDecisionType",
    # runbook / report
    "OperatorRunbookBuilder", "WARNINGS",
    "PilotReportBuilder", "PilotReport",
]
