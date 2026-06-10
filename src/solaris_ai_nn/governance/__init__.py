"""Governance layer: what is allowed, who approved it, and how it stops.

This is the control layer, deliberately separate from cognition: policy
(what may run), permissions (deny-by-default scopes), approvals (a local
human ledger), operator sessions, risk assessment, a JSONL governance audit,
an always-available emergency stop (with a sentinel-file path), runbooks,
checklists, ClaimGuard (no unsupported claims in reports), and post-run
reviews. Nothing in this package bypasses human approval, and nothing here
escalates automatically -- it evaluates, records, and recommends.
"""

from .approval import (  # noqa: F401
    APPROVAL_STATUSES,
    ApprovalRecord,
    ApprovalRegistry,
    ApprovalRequest,
)
from .audit import (  # noqa: F401
    DEFAULT_GOVERNANCE_DIR,
    GOVERNANCE_AUDIT_EVENTS,
    GovernanceAuditLog,
)
from .checklists import (  # noqa: F401
    ALL_CHECKLISTS,
    Checklist,
    ChecklistItem,
    ChecklistResult,
    long_soak_checklist,
    plasticity_checklist,
    post_run_checklist,
    pre_run_checklist,
    sidecar_checklist,
)
from .compliance import (  # noqa: F401
    SAFE_PHRASES,
    ClaimGuard,
    ClaimGuardFinding,
    ClaimGuardReport,
)
from .emergency import (  # noqa: F401
    SENTINEL_NAME,
    EmergencyStop,
    EmergencyStopResult,
    sentinel_path,
    sentinel_present,
)
from .operator import OperatorProfile, OperatorSession  # noqa: F401
from .permissions import (  # noqa: F401
    Permission,
    PermissionScope,
    PermissionSet,
)
from .policy import (  # noqa: F401
    RUN_CONTINUOUS_PERMISSION,
    GovernancePolicy,
    PolicyDecision,
    PolicyRule,
    PolicyViolation,
)
from .review import (  # noqa: F401
    NextRunRecommendation,
    PostRunReview,
    ReviewRecord,
)
from .risk import (  # noqa: F401
    RiskAssessment,
    RiskItem,
    RiskLevel,
    assess_current_state,
    assess_manifest,
)
from .runbook import RUNBOOK_TYPES, Runbook, RunbookBuilder  # noqa: F401

__all__ = [
    "GovernancePolicy", "PolicyRule", "PolicyDecision", "PolicyViolation",
    "RUN_CONTINUOUS_PERMISSION",
    "Permission", "PermissionSet", "PermissionScope",
    "ApprovalRequest", "ApprovalRecord", "ApprovalRegistry",
    "APPROVAL_STATUSES",
    "OperatorProfile", "OperatorSession",
    "RiskLevel", "RiskItem", "RiskAssessment",
    "assess_manifest", "assess_current_state",
    "GovernanceAuditLog", "GOVERNANCE_AUDIT_EVENTS",
    "DEFAULT_GOVERNANCE_DIR",
    "EmergencyStop", "EmergencyStopResult", "SENTINEL_NAME",
    "sentinel_path", "sentinel_present",
    "Runbook", "RunbookBuilder", "RUNBOOK_TYPES",
    "Checklist", "ChecklistItem", "ChecklistResult", "ALL_CHECKLISTS",
    "pre_run_checklist", "long_soak_checklist", "plasticity_checklist",
    "sidecar_checklist", "post_run_checklist",
    "ClaimGuard", "ClaimGuardReport", "ClaimGuardFinding", "SAFE_PHRASES",
    "ReviewRecord", "PostRunReview", "NextRunRecommendation",
]
