"""Architecture snapshots and diffs -- a versioned record of the shape.

The :class:`ArchitectureSnapshotBuilder` captures the module inventory, lifecycle
classifications, safety-critical modules, deprecated modules, the ADR index, the
roadmap hash, and known design debt at a point in time. :class:`ArchitectureDiff`
compares two snapshots for status changes, new/resolved debt, new ADRs, and
roadmap/safety changes. Snapshots are records; they change nothing.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ArchitectureSnapshot:
    snapshot_id: str
    module_inventory: Dict[str, Any] = field(default_factory=dict)
    lifecycle_classifications: Dict[str, str] = field(default_factory=dict)
    active_profiles: List[str] = field(default_factory=list)
    safety_critical_modules: List[str] = field(default_factory=list)
    deprecated_modules: List[str] = field(default_factory=list)
    adr_index: List[str] = field(default_factory=list)
    roadmap_hash: str = ""
    design_debt: Dict[str, Any] = field(default_factory=dict)
    research_evidence_refs: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ArchitectureDiff:
    """The differences between a previous and a current snapshot."""

    module_status_changes: Dict[str, Dict[str, str]] = field(
        default_factory=dict)
    new_debt: int = 0
    resolved_debt: int = 0
    new_adrs: List[str] = field(default_factory=list)
    roadmap_changed: bool = False
    safety_status_changed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ArchitectureSnapshotBuilder:
    base_dir: str = ".solaris_ai_nn_architecture"

    def build(self, *, inventory: Any = None,
              lifecycle_assessments: Optional[Dict[str, Any]] = None,
              active_profiles: Optional[List[str]] = None,
              adr_ids: Optional[List[str]] = None,
              roadmap_items: Optional[List[Any]] = None,
              design_debt: Any = None) -> ArchitectureSnapshot:
        inv = inventory.snapshot() if hasattr(inventory, "snapshot") else \
            (inventory or {})
        classifications = {}
        for name, a in (lifecycle_assessments or {}).items():
            classifications[name] = (a.get("lifecycle_class")
                                     if isinstance(a, dict)
                                     else getattr(a, "lifecycle_class",
                                                  "unknown"))
        roadmap_blob = json.dumps([
            (i.to_dict() if hasattr(i, "to_dict") else i)
            for i in (roadmap_items or [])], sort_keys=True, default=str)
        roadmap_hash = hashlib.sha256(roadmap_blob.encode()).hexdigest()[:16]
        debt_snap = design_debt.snapshot() if hasattr(design_debt, "snapshot") \
            else (design_debt or {})
        sid = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        return ArchitectureSnapshot(
            snapshot_id=sid, module_inventory=inv,
            lifecycle_classifications=classifications,
            active_profiles=list(active_profiles or []),
            safety_critical_modules=inv.get("safety_critical", []),
            deprecated_modules=[n for n, c in classifications.items()
                                if "deprecated" in str(c)],
            adr_index=list(adr_ids or []), roadmap_hash=roadmap_hash,
            design_debt=debt_snap)

    def write(self, snapshot: ArchitectureSnapshot) -> Dict[str, str]:
        directory = os.path.join(self.base_dir, "snapshots")
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory,
                            f"architecture_snapshot_{snapshot.snapshot_id}.json")
        latest = os.path.join(directory, "latest.json")
        for p in (path, latest):
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(snapshot.to_dict(), fh, indent=2, default=str)
        return {"snapshot": path, "latest": latest}

    def load_latest(self) -> Optional[ArchitectureSnapshot]:
        latest = os.path.join(self.base_dir, "snapshots", "latest.json")
        if not os.path.exists(latest):
            return None
        try:
            with open(latest, encoding="utf-8") as fh:
                data = json.load(fh)
            return ArchitectureSnapshot(**{
                k: v for k, v in data.items()
                if k in ArchitectureSnapshot.__dataclass_fields__})
        except Exception:
            return None

    def diff(self, previous: Optional[ArchitectureSnapshot],
             current: ArchitectureSnapshot) -> ArchitectureDiff:
        if previous is None:
            return ArchitectureDiff(
                new_debt=current.design_debt.get("debt_count", 0),
                new_adrs=list(current.adr_index),
                roadmap_changed=True, safety_status_changed=True)
        changes: Dict[str, Dict[str, str]] = {}
        for name, cur in current.lifecycle_classifications.items():
            prev = previous.lifecycle_classifications.get(name)
            if prev != cur:
                changes[name] = {"from": prev or "unknown", "to": cur}
        prev_debt = previous.design_debt.get("debt_count", 0)
        cur_debt = current.design_debt.get("debt_count", 0)
        return ArchitectureDiff(
            module_status_changes=changes,
            new_debt=max(0, cur_debt - prev_debt),
            resolved_debt=max(0, prev_debt - cur_debt),
            new_adrs=[a for a in current.adr_index
                      if a not in previous.adr_index],
            roadmap_changed=current.roadmap_hash != previous.roadmap_hash,
            safety_status_changed=(current.safety_critical_modules
                                   != previous.safety_critical_modules))
