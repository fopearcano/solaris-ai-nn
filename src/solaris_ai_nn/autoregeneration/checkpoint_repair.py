"""Checkpoint repair -- continuity without rewriting identity history.

The :class:`CheckpointRepairManager` inspects checkpoint lineage for missing
parents, impossible timestamp order, incomplete checkpoints, and mismatched
identity anchors. It marks a checkpoint suspect and restores last-known-good
*metadata* only; when identity continuity is unclear it requests
operator/governance review. It never silently rewrites identity history and
never rolls back source code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .repair_actions import RepairAction, RepairActionType, make_repair


@dataclass
class CheckpointRepairManager:
    """Inspects checkpoint lineage and proposes metadata-only repairs."""

    suspect_checkpoints: List[str] = field(default_factory=list)
    review_requests: List[str] = field(default_factory=list)

    def inspect(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return detected lineage issues (non-mutating)."""
        cp = (context or {}).get("checkpoints") or {}
        lineage = cp.get("lineage") or []
        issues: List[str] = list(cp.get("issues") or [])
        last_ts = None
        seen_ids = set()
        for entry in lineage:
            cid = entry.get("checkpoint_id")
            parent = entry.get("parent_id")
            ts = entry.get("timestamp")
            if parent and parent not in seen_ids and seen_ids:
                issues.append(f"missing_parent:{cid}")
            if ts is not None and last_ts is not None and ts < last_ts:
                issues.append(f"impossible_timestamp_order:{cid}")
            if entry.get("incomplete"):
                issues.append(f"incomplete:{cid}")
            if entry.get("identity_mismatch"):
                issues.append(f"identity_mismatch:{cid}")
            if cid:
                seen_ids.add(cid)
            last_ts = ts if ts is not None else last_ts
        return {"issues": sorted(set(issues)), "lineage_length": len(lineage)}

    def propose(self, context: Dict[str, Any]) -> List[RepairAction]:
        report = self.inspect(context)
        actions: List[RepairAction] = []
        for issue in report["issues"]:
            if issue.startswith("identity_mismatch"):
                cid = issue.split(":", 1)[-1]
                self.review_requests.append(cid)
                actions.append(make_repair(
                    RepairActionType.GENERATE_OPERATOR_REVIEW_REQUEST,
                    target_ref=cid,
                    reason="identity continuity unclear; do not rewrite "
                           "history silently",
                    expected_benefit="human review of identity continuity"))
            else:
                cid = issue.split(":", 1)[-1]
                self.suspect_checkpoints.append(cid)
                actions.append(make_repair(
                    RepairActionType.RESTORE_FROM_CHECKPOINT,
                    target_ref=cid,
                    reason=f"checkpoint lineage issue: {issue}",
                    expected_benefit="restore last-known-good checkpoint "
                                     "metadata"))
        return actions

    def mark_suspect(self, checkpoint_id: str) -> None:
        if checkpoint_id not in self.suspect_checkpoints:
            self.suspect_checkpoints.append(checkpoint_id)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "suspect_checkpoints": list(self.suspect_checkpoints),
            "review_requests": list(self.review_requests),
        }
