"""Action ledger -- append-only audit of every proposed and blocked action.

The :class:`ActionLedger` records every motor action proposal, the decisions
at each gate (executive / firewall / safety / governance / ego), the final
status, and the result -- always with ``real_world_authority = False``. No
action may execute without a pre-execution ledger record; every blocked action
is logged too.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ActionLedgerRecord:
    """One ledger entry for a motor action's lifecycle."""

    action_id: str
    action_type: str
    proposal_source: str = ""
    executive_decision: str = "unchecked"
    firewall_decision: str = "unchecked"
    safety_decision: str = "unchecked"
    governance_decision: str = "unchecked"
    ego_boundary_decision: str = "unchecked"
    final_status: str = "proposed"
    result_summary: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    real_world_authority: bool = False
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ActionLedger:
    """Append-only ledger persisted to JSONL under the state directory."""

    state_dir: Optional[str] = None
    write_log: bool = True
    records: List[ActionLedgerRecord] = field(default_factory=list, init=False)
    proposed_count: int = field(default=0, init=False)
    blocked_count: int = field(default=0, init=False)
    executed_count: int = field(default=0, init=False)
    write_failures: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.actions_path = self._p("motor_actions.jsonl")
        self.results_path = self._p("motor_action_results.jsonl")
        self.firewall_path = self._p("actuation_firewall.jsonl")

    def _p(self, name: str) -> Optional[str]:
        return os.path.join(self.state_dir, name) if self.state_dir else None

    def _append(self, path: Optional[str], obj: Dict[str, Any]) -> None:
        if not (self.write_log and path):
            return
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(obj, default=str) + "\n")
        except OSError:
            # Append-only ledger persistence failed; count it so Ops can warn.
            # The in-memory record is still authoritative for this run.
            self.write_failures += 1

    def record_proposal(self, action: Any, proposal_source: str = "",
                        ) -> ActionLedgerRecord:
        """Log a proposed action *before* any gate runs (mandatory)."""
        rec = ActionLedgerRecord(
            action_id=action.action_id, action_type=action.action_type,
            proposal_source=proposal_source, final_status=action.status)
        self.records.append(rec)
        self.proposed_count += 1
        self._append(self.actions_path, rec.to_dict())
        return rec

    def update_decisions(self, record: ActionLedgerRecord, *,
                         executive: Optional[str] = None,
                         firewall: Optional[str] = None,
                         safety: Optional[str] = None,
                         governance: Optional[str] = None,
                         ego: Optional[str] = None,
                         final_status: Optional[str] = None,
                         result_summary: Optional[str] = None,
                         evidence_refs: Optional[List[str]] = None) -> None:
        if executive is not None:
            record.executive_decision = executive
        if firewall is not None:
            record.firewall_decision = firewall
            self._append(self.firewall_path,
                         {"action_id": record.action_id, "decision": firewall,
                          "timestamp": time.time()})
        if safety is not None:
            record.safety_decision = safety
        if governance is not None:
            record.governance_decision = governance
        if ego is not None:
            record.ego_boundary_decision = ego
        if final_status is not None:
            record.final_status = final_status
            from .actions import MotorActionStatus

            if final_status in MotorActionStatus.BLOCKED:
                self.blocked_count += 1
            elif final_status == MotorActionStatus.EXECUTED_IN_SIMULATION:
                self.executed_count += 1
        if result_summary is not None:
            record.result_summary = result_summary
        if evidence_refs is not None:
            record.evidence_refs = list(evidence_refs)

    def record_result(self, result: Any) -> None:
        """Log a (simulated/dry-run) action result."""
        self._append(self.results_path, result.to_dict()
                     if hasattr(result, "to_dict") else dict(result))

    def snapshot(self) -> Dict[str, Any]:
        return {
            "proposed_count": self.proposed_count,
            "blocked_count": self.blocked_count,
            "executed_count": self.executed_count,
            "record_count": len(self.records),
            "write_failures": self.write_failures,
            "actions_path": self.actions_path,
            "results_path": self.results_path,
            "firewall_path": self.firewall_path,
            "recent": [r.to_dict() for r in self.records[-8:]],
        }
