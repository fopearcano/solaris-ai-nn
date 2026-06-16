"""Research cycle manifest -- local provenance of one experimental cycle.

:class:`ResearchCycleManifest` records the refs (paths/ids) that constitute one
research cycle: the baseline it started from, the roadmap, architecture-evolution
/ experiment-compiler / implementation-intake / post-merge / research-baseline /
soak / replication / falsification / safety / operator-decision refs, and the
current cycle state. It is local metadata: it creates no branches, runs no
experiments, and modifies no source. Parent/child cycles are experimental
provenance only.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ResearchCycleScope:
    SINGLE_CYCLE = "single_cycle"
    LINEAGE = "lineage"
    UNKNOWN = "unknown"

    ALL = (SINGLE_CYCLE, LINEAGE, UNKNOWN)


@dataclass
class ResearchCycleIdentity:
    """The identity + provenance of one cycle (experimental, not biological)."""

    cycle_id: str = "cycle_1"
    parent_cycle_id: str = ""
    baseline_id: str = ""
    baseline_version_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"cycle_id": self.cycle_id, "parent_cycle_id": self.parent_cycle_id,
                "baseline_id": self.baseline_id,
                "baseline_version_id": self.baseline_version_id,
                "biological_lineage": False}


@dataclass
class ResearchCycleArtifact:
    """One referenced artifact for the cycle (ref/path only; not copied)."""

    kind: str
    ref: str = ""
    present: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "ref": self.ref, "present": self.present}


@dataclass
class ResearchCycleManifest:
    """The local manifest of one research cycle's refs + current state."""

    identity: ResearchCycleIdentity = field(
        default_factory=ResearchCycleIdentity)
    scope: str = ResearchCycleScope.SINGLE_CYCLE
    roadmap_refs: List[str] = field(default_factory=list)
    architecture_evolution_refs: List[str] = field(default_factory=list)
    experiment_compiler_refs: List[str] = field(default_factory=list)
    implementation_intake_refs: List[str] = field(default_factory=list)
    post_merge_assimilation_refs: List[str] = field(default_factory=list)
    research_baseline_refs: List[str] = field(default_factory=list)
    soak_refs: List[str] = field(default_factory=list)
    replication_refs: List[str] = field(default_factory=list)
    falsification_refs: List[str] = field(default_factory=list)
    safety_refs: List[str] = field(default_factory=list)
    operator_decision_refs: List[str] = field(default_factory=list)
    current_cycle_state: str = "baseline_selected"
    limitations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_ts: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "scope": self.scope,
            "roadmap_refs": list(self.roadmap_refs),
            "architecture_evolution_refs":
                list(self.architecture_evolution_refs),
            "experiment_compiler_refs": list(self.experiment_compiler_refs),
            "implementation_intake_refs": list(self.implementation_intake_refs),
            "post_merge_assimilation_refs":
                list(self.post_merge_assimilation_refs),
            "research_baseline_refs": list(self.research_baseline_refs),
            "soak_refs": list(self.soak_refs),
            "replication_refs": list(self.replication_refs),
            "falsification_refs": list(self.falsification_refs),
            "safety_refs": list(self.safety_refs),
            "operator_decision_refs": list(self.operator_decision_refs),
            "current_cycle_state": self.current_cycle_state,
            "limitations": list(self.limitations),
            "metadata": dict(self.metadata),
            "created_ts": self.created_ts,
            "creates_branches": False, "runs_experiments": False,
            "modifies_source": False,
            "note": ("local cycle metadata only; parent/child cycles are "
                     "experimental provenance, not biological lineage; nothing "
                     "here creates a branch, runs an experiment, or modifies "
                     "source"),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchCycleManifest":
        data = dict(data or {})
        ident = data.pop("identity", {}) or {}
        return cls(
            identity=ResearchCycleIdentity(
                cycle_id=ident.get("cycle_id", "cycle_1"),
                parent_cycle_id=ident.get("parent_cycle_id", ""),
                baseline_id=ident.get("baseline_id", ""),
                baseline_version_id=ident.get("baseline_version_id", "")),
            scope=data.get("scope", ResearchCycleScope.SINGLE_CYCLE),
            roadmap_refs=list(data.get("roadmap_refs", [])),
            architecture_evolution_refs=list(
                data.get("architecture_evolution_refs", [])),
            experiment_compiler_refs=list(
                data.get("experiment_compiler_refs", [])),
            implementation_intake_refs=list(
                data.get("implementation_intake_refs", [])),
            post_merge_assimilation_refs=list(
                data.get("post_merge_assimilation_refs", [])),
            research_baseline_refs=list(data.get("research_baseline_refs", [])),
            soak_refs=list(data.get("soak_refs", [])),
            replication_refs=list(data.get("replication_refs", [])),
            falsification_refs=list(data.get("falsification_refs", [])),
            safety_refs=list(data.get("safety_refs", [])),
            operator_decision_refs=list(data.get("operator_decision_refs", [])),
            current_cycle_state=data.get("current_cycle_state",
                                         "baseline_selected"),
            limitations=list(data.get("limitations", [])),
            metadata=dict(data.get("metadata", {})))

    def persist(self, state_dir: str) -> Dict[str, str]:
        """Write the manifest + append a history entry (local metadata only)."""
        os.makedirs(state_dir, exist_ok=True)
        manifest_path = os.path.join(state_dir, "cycle_manifest.json")
        history_path = os.path.join(state_dir, "cycle_history.jsonl")
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2, default=str)
        with open(history_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"cycle_id": self.identity.cycle_id,
                                 "state": self.current_cycle_state,
                                 "ts": time.time()}, default=str) + "\n")
        return {"manifest": manifest_path, "history": history_path}
