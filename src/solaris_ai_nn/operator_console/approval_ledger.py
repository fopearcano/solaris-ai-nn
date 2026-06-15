"""Approval ledger -- a record of permission, never a grant of authority.

:class:`ApprovalLedger` appends operator approval records to a local JSONL file.
An approval is a *planning/governance artifact*: it can record that a bounded
fixture run, a plan generation, or an export was approved, but it can never
approve forbidden real-world actuation and can never disable safety checks,
emergency stop, ClaimGuard, or the motor firewall.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ApprovalScope:
    BOUNDED_FIXTURE_RUN = "bounded_fixture_run"
    BOUNDED_SIMULATION_RUN = "bounded_simulation_run"
    READ_ONLY_SOURCE_PREFLIGHT = "read_only_source_preflight"
    PILOT_PLAN_GENERATION = "pilot_plan_generation"
    RESEARCH_ABLATION_RUN = "research_ablation_run"
    ARCHITECTURE_REVIEW_GENERATION = "architecture_review_generation"
    EXPORT_BUNDLE_GENERATION = "export_bundle_generation"
    LONG_RUN_PLANNING = "long_run_planning"
    FORBIDDEN_REAL_WORLD_ACTUATION = "forbidden_real_world_actuation"

    ALL = (BOUNDED_FIXTURE_RUN, BOUNDED_SIMULATION_RUN,
           READ_ONLY_SOURCE_PREFLIGHT, PILOT_PLAN_GENERATION,
           RESEARCH_ABLATION_RUN, ARCHITECTURE_REVIEW_GENERATION,
           EXPORT_BUNDLE_GENERATION, LONG_RUN_PLANNING,
           FORBIDDEN_REAL_WORLD_ACTUATION)
    # Scopes that can never be approved, no matter what the operator types.
    FORBIDDEN = frozenset({FORBIDDEN_REAL_WORLD_ACTUATION})


class ApprovalStatus:
    RECORDED = "recorded"
    BLOCKED = "blocked"

    ALL = (RECORDED, BLOCKED)


_LIMITATIONS = (
    "an approval is a local record, not an execution",
    "no approval can enable forbidden real-world actuation",
    "no approval can disable safety checks, emergency stop, ClaimGuard, or the "
    "motor firewall",
)


@dataclass
class ApprovalRecord:
    """One operator approval (or a blocked attempt)."""

    approval_id: str
    scope: str
    status: str
    operator_note: str
    timestamp: float = field(default_factory=time.time)
    limitations: List[str] = field(default_factory=lambda: list(_LIMITATIONS))
    block_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def recorded(self) -> bool:
        return self.status == ApprovalStatus.RECORDED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "scope": self.scope,
            "status": self.status,
            "operator_note": self.operator_note,
            "timestamp": self.timestamp,
            "limitations": list(self.limitations),
            "block_reason": self.block_reason,
            "metadata": dict(self.metadata),
        }


@dataclass
class ApprovalLedger:
    """Append-only ledger of operator approvals; forbidden scopes are blocked."""

    state_dir: str = ".solaris_ai_nn_operator"
    _records: List[ApprovalRecord] = field(default_factory=list, init=False)

    @property
    def path(self) -> str:
        return os.path.join(self.state_dir, "approval_ledger.jsonl")

    def record(self, scope: str, operator_note: str,
               metadata: Optional[Dict[str, Any]] = None) -> ApprovalRecord:
        """Record an approval, or block it if the scope is forbidden."""
        approval_id = f"APR_{uuid.uuid4().hex[:10]}"
        if scope in ApprovalScope.FORBIDDEN \
                or scope not in ApprovalScope.ALL:
            reason = (
                "forbidden real-world actuation cannot be approved"
                if scope in ApprovalScope.FORBIDDEN else
                f"unknown approval scope {scope!r}")
            record = ApprovalRecord(
                approval_id=approval_id, scope=scope,
                status=ApprovalStatus.BLOCKED, operator_note=operator_note,
                block_reason=reason, metadata=dict(metadata or {}))
        else:
            record = ApprovalRecord(
                approval_id=approval_id, scope=scope,
                status=ApprovalStatus.RECORDED, operator_note=operator_note,
                metadata=dict(metadata or {}))
        self._records.append(record)
        self._append(record)
        return record

    def _append(self, record: ApprovalRecord) -> None:
        os.makedirs(self.state_dir, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record.to_dict(), default=str) + "\n")

    def records(self) -> List[ApprovalRecord]:
        return list(self._records)

    def recorded_count(self) -> int:
        return sum(1 for r in self._records if r.recorded)

    def blocked_count(self) -> int:
        return sum(1 for r in self._records if not r.recorded)

    def latest(self) -> Optional[ApprovalRecord]:
        return self._records[-1] if self._records else None

    def snapshot(self) -> Dict[str, Any]:
        latest = self.latest()
        return {
            "approval_count": len(self._records),
            "recorded_count": self.recorded_count(),
            "blocked_count": self.blocked_count(),
            "latest": latest.to_dict() if latest else None,
            "ledger_path": self.path,
        }
