"""Approvals -- a local, human-readable research approval ledger.

This is NOT an authentication or security system. It is a plain JSON ledger
that records that a named human deliberately approved a specific risky
capability (active plasticity, long soaks, outward suggestions) for a specific
reason -- so a later reviewer can see who allowed what, and why.

Statuses: ``pending`` -> ``approved`` / ``rejected``; time-limited approvals
become ``expired`` once ``expires_at`` passes.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from . import audit as A

PENDING = "pending"
APPROVED = "approved"
REJECTED = "rejected"
EXPIRED = "expired"

APPROVAL_STATUSES = (PENDING, APPROVED, REJECTED, EXPIRED)


@dataclass
class ApprovalRequest:
    """One request for a risky capability, awaiting a human decision."""

    requested_permission: str
    reason: str = ""
    run_id: str = ""
    risk_level: str = "high"
    required_confirmations: int = 1
    operator_name: str = ""
    status: str = PENDING
    expires_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: float = field(default_factory=time.time)
    confirmations: List[Dict[str, Any]] = field(default_factory=list)
    decided_by: str = ""
    decided_at: Optional[float] = None
    decision_note: str = ""

    def is_expired(self, now: Optional[float] = None) -> bool:
        if self.expires_at is None:
            return False
        return (now if now is not None else time.time()) >= self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApprovalRequest":
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})


@dataclass
class ApprovalRecord:
    """One human decision applied to a request (kept for the ledger)."""

    request_id: str
    action: str  # "approved" | "rejected"
    operator_name: str
    note: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ApprovalRegistry:
    """The ledger of approval requests and decisions; saves to JSON."""

    path: Optional[Union[str, Path]] = None
    audit: Optional[A.GovernanceAuditLog] = None
    requests: Dict[str, ApprovalRequest] = field(default_factory=dict)
    records: List[ApprovalRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.path is not None:
            self.path = Path(self.path)
            if self.path.exists():
                self.load(self.path)

    # -- requests --------------------------------------------------------------

    def request_approval(self, requested_permission: str, reason: str = "",
                         run_id: str = "", risk_level: str = "high",
                         operator_name: str = "",
                         required_confirmations: int = 1,
                         expires_in_s: Optional[float] = None,
                         metadata: Optional[Dict[str, Any]] = None,
                         ) -> ApprovalRequest:
        request = ApprovalRequest(
            requested_permission=requested_permission, reason=reason,
            run_id=run_id, risk_level=risk_level,
            operator_name=operator_name,
            required_confirmations=max(1, required_confirmations),
            expires_at=(time.time() + expires_in_s
                        if expires_in_s is not None else None),
            metadata=metadata or {})
        self.requests[request.request_id] = request
        if self.audit is not None:
            self.audit.record(A.APPROVAL_REQUESTED, decision="pending",
                              reason=reason, operator=operator_name,
                              metadata={"request_id": request.request_id,
                                        "permission": requested_permission,
                                        "risk_level": risk_level})
        return request

    # -- decisions ---------------------------------------------------------------

    def approve(self, request_id: str, operator_name: str,
                note: str = "") -> ApprovalRequest:
        request = self._pending(request_id)
        request.confirmations.append({
            "operator": operator_name, "note": note, "timestamp": time.time()})
        if len(request.confirmations) >= request.required_confirmations:
            request.status = APPROVED
            request.decided_by = operator_name
            request.decided_at = time.time()
            request.decision_note = note
        self.records.append(ApprovalRecord(
            request_id=request_id, action="approved",
            operator_name=operator_name, note=note))
        if self.audit is not None:
            self.audit.record(A.APPROVAL_GRANTED, decision=request.status,
                              reason=note, operator=operator_name,
                              metadata={"request_id": request_id,
                                        "permission":
                                            request.requested_permission})
        return request

    def reject(self, request_id: str, operator_name: str,
               reason: str = "") -> ApprovalRequest:
        request = self._pending(request_id)
        request.status = REJECTED
        request.decided_by = operator_name
        request.decided_at = time.time()
        request.decision_note = reason
        self.records.append(ApprovalRecord(
            request_id=request_id, action="rejected",
            operator_name=operator_name, note=reason))
        if self.audit is not None:
            self.audit.record(A.APPROVAL_REJECTED, decision=REJECTED,
                              reason=reason, operator=operator_name,
                              metadata={"request_id": request_id,
                                        "permission":
                                            request.requested_permission})
        return request

    def _pending(self, request_id: str) -> ApprovalRequest:
        request = self.requests.get(request_id)
        if request is None:
            raise KeyError(f"unknown approval request {request_id!r}")
        self.expire_stale()
        if request.status != PENDING:
            raise ValueError(
                f"request {request_id!r} is {request.status}, not pending")
        return request

    # -- queries ------------------------------------------------------------------

    def expire_stale(self, now: Optional[float] = None) -> int:
        """Mark time-limited requests past their deadline as expired."""
        expired = 0
        for request in self.requests.values():
            if request.status in (PENDING, APPROVED) \
                    and request.is_expired(now):
                request.status = EXPIRED
                expired += 1
        return expired

    def is_approved(self, permission: str,
                    context: Optional[Dict[str, Any]] = None) -> bool:
        """Is there a valid (approved, unexpired) record for ``permission``?"""
        self.expire_stale()
        ctx = context or {}
        run_id = ctx.get("run_id")
        for request in self.requests.values():
            if request.requested_permission != permission:
                continue
            if request.status != APPROVED:
                continue
            if request.run_id and run_id and request.run_id != run_id:
                continue  # approval was pinned to a different run
            return True
        return False

    def list_pending(self) -> List[ApprovalRequest]:
        self.expire_stale()
        return [r for r in self.requests.values() if r.status == PENDING]

    def list_by_status(self, status: str) -> List[ApprovalRequest]:
        self.expire_stale()
        return [r for r in self.requests.values() if r.status == status]

    def expired_count(self) -> int:
        self.expire_stale()
        return sum(1 for r in self.requests.values() if r.status == EXPIRED)

    # -- persistence -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requests": {rid: r.to_dict()
                         for rid, r in self.requests.items()},
            "records": [r.to_dict() for r in self.records],
        }

    def save(self, path: Optional[Union[str, Path]] = None) -> Path:
        target = Path(path or self.path or "approvals.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2, default=str)
        return target

    def load(self, path: Optional[Union[str, Path]] = None) -> int:
        source = Path(path or self.path or "approvals.json")
        if not source.exists():
            return 0
        with open(source, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        self.requests = {rid: ApprovalRequest.from_dict(row)
                         for rid, row in (data.get("requests") or {}).items()}
        self.records = [
            ApprovalRecord(**{k: v for k, v in row.items()
                              if k in ApprovalRecord.__dataclass_fields__})  # type: ignore[attr-defined]
            for row in (data.get("records") or [])]
        return len(self.requests)
