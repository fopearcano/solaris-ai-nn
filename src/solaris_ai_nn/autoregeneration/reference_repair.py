"""Reference repair -- fix broken links between records, never invent them.

The :class:`ReferenceRepairManager` finds broken references between memory
records, world-model nodes, proto-symbols, hypothesis records, exploration
records, milestones, fossil memory, and reports. It repairs only
deterministic references, marks ambiguous ones ambiguous, and quarantines
dangling references it cannot safely repair. It never invents missing
objects or fabricates evidence refs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .repair_actions import RepairAction, RepairActionType, make_repair


@dataclass
class ReferenceRepairManager:
    """Repairs deterministic references; leaves ambiguous ones ambiguous."""

    repaired: List[str] = field(default_factory=list)
    ambiguous: List[str] = field(default_factory=list)
    quarantined: List[str] = field(default_factory=list)

    def find_broken(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """References whose target is absent (non-mutating)."""
        refs = (context or {}).get("references") or {}
        return list(refs.get("broken_detail") or [
            {"ref": b, "candidates": []} for b in (refs.get("broken") or [])])

    def propose(self, context: Dict[str, Any]) -> List[RepairAction]:
        actions: List[RepairAction] = []
        for broken in self.find_broken(context):
            ref = broken.get("ref")
            candidates = broken.get("candidates") or []
            if len(candidates) == 1:
                # Deterministic repair: exactly one valid target.
                self.repaired.append(ref)
                actions.append(make_repair(
                    RepairActionType.REPAIR_BROKEN_REFERENCE,
                    target_ref=str(ref),
                    reason="exactly one valid target; deterministic repair",
                    expected_benefit="restore a broken reference",
                    resolved_to=candidates[0]))
            elif len(candidates) > 1:
                # Ambiguous repair must stay ambiguous.
                self.ambiguous.append(ref)
                actions.append(make_repair(
                    RepairActionType.MARK_WORLD_EDGE_AMBIGUOUS,
                    target_ref=str(ref),
                    reason="multiple candidate targets; left ambiguous",
                    expected_benefit="flag an ambiguous reference"))
            else:
                # Dangling reference with no candidate: quarantine, do not
                # invent a target.
                self.quarantined.append(ref)
                actions.append(make_repair(
                    RepairActionType.QUARANTINE_CORRUPT_RECORD,
                    target_ref=str(ref),
                    reason="dangling reference with no valid target",
                    expected_benefit="quarantine a dangling reference"))
        return actions

    def snapshot(self) -> Dict[str, Any]:
        return {
            "repaired_count": len(self.repaired),
            "ambiguous_count": len(self.ambiguous),
            "quarantined_count": len(self.quarantined),
        }
