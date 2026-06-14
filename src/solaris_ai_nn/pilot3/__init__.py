"""Pilot-3 -- simulated embodiment soak, action grounding, and firewall audit.

Pilot-3 tests whether *simulated* action/reaction loops in a GridWorld sandbox
body produce stronger grounding than perception-only exposure. It is the
outbound mirror of Pilot-2's read-only sensory soak: the system may act inside
the sandbox, write dry-run action traces, record action ledgers, compare
predicted vs observed simulated consequences, and use simulated outcomes as
simulation-scoped evidence -- but it may never act on the real world. An
always-on actuation firewall is audited to prove non-actuation, action grounding
is graded (including sandbox-overfit detection), simulated action is compared
against the read-only baseline, daily/weekly embodied reviews and a Pilot-3 soak
report are written, and the decision gate chooses whether to extend simulation,
reduce complexity, revise the firewall, return to read-only, or prepare Pilot-4
as planning-only. Pilot-3 is sandboxed action grounding, not real embodiment.
"""

from __future__ import annotations

from .action_grounding import (
    ActionGroundingAnalyzer,
    ActionGroundingEvidence,
    ActionGroundingQuality,
)
from .comparative_design import (
    Pilot3ComparativeDesign,
    Pilot3ComparisonArm,
    Pilot3ComparisonMetric,
    Pilot3ComparisonResult,
)
from .embodied_daily_review import (
    Pilot3DailyRecommendation,
    Pilot3DailyReview,
    Pilot3DailyReviewBuilder,
)
from .embodied_post_analysis import (
    EmbodiedPostAnalysis,
    EmbodiedPostAnalyzer,
    EmbodiedPostClassification,
)
from .embodied_weekly_review import (
    Pilot3WeeklyReview,
    Pilot3WeeklyReviewBuilder,
)
from .embodiment_preflight import (
    EmbodimentPreflightCheck,
    EmbodimentPreflightResult,
    EmbodimentPreflightRunner,
)
from .firewall_audit import (
    FirewallAudit,
    FirewallAuditFinding,
    FirewallAuditResult,
    FirewallAuditSeverity,
)
from .operator_runbook import Pilot3SoakRunbookBuilder
from .pilot3_config import (
    DEFAULT_PILOT3_DIR,
    EmbodimentCondition,
    Pilot3Authority,
    Pilot3Config,
    Pilot3Mode,
)
from .pilot3_decision_gate import (
    Pilot3SoakDecisionGate,
    Pilot3SoakDecisionOption,
    Pilot3SoakDecisionResult,
)
from .pilot3_soak_report import Pilot3SoakReport, Pilot3SoakReportBuilder
from .safety import (
    HARD_RULES,
    Pilot3SoakSafetyReport,
    Pilot3SoakSafetyValidator,
)
from .soak_protocol import (
    Pilot3SoakPhase,
    Pilot3SoakPhaseRecord,
    Pilot3SoakPhaseStatus,
    Pilot3SoakProtocol,
    Pilot3SoakState,
)

__all__ = [
    # config / safety / protocol
    "Pilot3Config", "Pilot3Mode", "Pilot3Authority", "EmbodimentCondition",
    "DEFAULT_PILOT3_DIR", "Pilot3SoakSafetyValidator", "Pilot3SoakSafetyReport",
    "HARD_RULES", "Pilot3SoakProtocol", "Pilot3SoakPhase",
    "Pilot3SoakPhaseStatus", "Pilot3SoakState", "Pilot3SoakPhaseRecord",
    # preflight / comparative / grounding / firewall audit
    "EmbodimentPreflightRunner", "EmbodimentPreflightResult",
    "EmbodimentPreflightCheck", "Pilot3ComparativeDesign",
    "Pilot3ComparisonArm", "Pilot3ComparisonMetric", "Pilot3ComparisonResult",
    "ActionGroundingAnalyzer", "ActionGroundingEvidence",
    "ActionGroundingQuality", "FirewallAudit", "FirewallAuditFinding",
    "FirewallAuditResult", "FirewallAuditSeverity",
    # reviews / post-analysis / report / decision / runbook
    "Pilot3DailyReview", "Pilot3DailyReviewBuilder", "Pilot3DailyRecommendation",
    "Pilot3WeeklyReview", "Pilot3WeeklyReviewBuilder",
    "EmbodiedPostAnalysis", "EmbodiedPostAnalyzer", "EmbodiedPostClassification",
    "Pilot3SoakReport", "Pilot3SoakReportBuilder",
    "Pilot3SoakDecisionGate", "Pilot3SoakDecisionResult",
    "Pilot3SoakDecisionOption", "Pilot3SoakRunbookBuilder",
]
