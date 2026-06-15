"""Perceptual energy budget -- a compute/attention metaphor that bounds work.

A :class:`PerceptualEnergyBudget` allocates a finite per-tick budget across the
perceptual tasks (receptor update, field update, detection, proto-symbol
generation, hypothesis seeding, consolidation, replay, reports). It is NOT
biological energy: it is a local metaphor that prevents infinite processing and
degrades gracefully -- when the budget is low, safety, continuity, absence, and
source-health tasks are prioritized.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

TASKS = (
    "receptor_update", "sensory_field_update", "absence_detection",
    "rhythm_detection", "invariant_detection", "cross_modal_detection",
    "proto_symbol_candidate_generation", "hypothesis_seeding",
    "logos_tension_processing", "memory_consolidation", "latent_replay",
    "report_generation",
)

# Tasks that stay funded even when the budget is low (graceful degradation).
PRIORITY_TASKS = ("receptor_update", "sensory_field_update",
                  "absence_detection")

# Default per-task cost (a relative metaphor, not seconds).
_COST = {t: 1.0 for t in TASKS}
_COST["proto_symbol_candidate_generation"] = 1.5
_COST["hypothesis_seeding"] = 1.5
_COST["latent_replay"] = 2.0
_COST["memory_consolidation"] = 2.0


@dataclass
class EnergyAllocation:
    task: str
    requested: float
    granted: float
    deferred: bool

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class EnergyBudgetResult:
    allocations: List[EnergyAllocation] = field(default_factory=list)
    spent: float = 0.0
    remaining: float = 0.0
    exhausted: bool = False
    deferred_tasks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allocations": [a.to_dict() for a in self.allocations],
            "spent": round(self.spent, 4),
            "remaining": round(self.remaining, 4),
            "exhausted": self.exhausted,
            "deferred_tasks": list(self.deferred_tasks),
        }


@dataclass
class PerceptualEnergyBudget:
    """A finite, gracefully-degrading per-tick processing budget."""

    budget_per_tick: float = 12.0

    def allocate(self, requested_tasks: List[str]) -> EnergyBudgetResult:
        """Allocate the budget across requested tasks, priority-first."""
        result = EnergyBudgetResult(remaining=self.budget_per_tick)
        # Priority tasks are funded first so low budget degrades gracefully.
        ordered = ([t for t in requested_tasks if t in PRIORITY_TASKS]
                   + [t for t in requested_tasks if t not in PRIORITY_TASKS])
        for task in ordered:
            cost = _COST.get(task, 1.0)
            if result.remaining >= cost:
                result.allocations.append(EnergyAllocation(
                    task=task, requested=cost, granted=cost, deferred=False))
                result.remaining -= cost
                result.spent += cost
            else:
                result.allocations.append(EnergyAllocation(
                    task=task, requested=cost, granted=0.0, deferred=True))
                result.deferred_tasks.append(task)
        result.exhausted = result.remaining <= 0.0
        return result

    def priority_tasks(self) -> List[str]:
        return list(PRIORITY_TASKS)

    def to_dict(self) -> Dict[str, Any]:
        return {"budget_per_tick": self.budget_per_tick,
                "tasks": list(TASKS), "priority_tasks": list(PRIORITY_TASKS),
                "note": "compute/attention metaphor; not biological energy"}
