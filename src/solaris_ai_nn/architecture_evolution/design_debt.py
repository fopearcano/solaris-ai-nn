"""Design debt registry -- keep the uncomfortable findings.

The :class:`DesignDebtRegistry` records design-debt items (overcomplexity,
duplicate responsibility, weak evidence, excessive coupling, missing tests/docs,
unsafe ambiguity, performance overhead, abandoned experiments, ...). Negative
results are not errors; debt items are preserved and can be linked to ADRs.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class DesignDebtSeverity:
    INFO = "info"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

    ALL = (INFO, LOW, MODERATE, HIGH, CRITICAL)


DEBT_CATEGORIES = (
    "overcomplexity", "duplicate_module_responsibility", "weak_evidence",
    "unclear_boundary", "excessive_coupling", "missing_tests", "missing_docs",
    "unsafe_ambiguity", "poor_analyzability", "state_compatibility_risk",
    "performance_overhead", "abandoned_experiment", "naming_inconsistency",
)


@dataclass
class DesignDebtItem:
    """One recorded design-debt item; preserved, never auto-resolved."""

    category: str
    summary: str
    module_name: str = ""
    severity: str = DesignDebtSeverity.MODERATE
    linked_adr_ids: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    item_id: str = field(default_factory=lambda: f"DEBT_{uuid.uuid4().hex[:8]}")
    created_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.category not in DEBT_CATEGORIES:
            raise ValueError(f"unknown debt category {self.category!r}")
        if self.severity not in DesignDebtSeverity.ALL:
            raise ValueError(f"unknown debt severity {self.severity!r}")

    def link_adr(self, adr_id: str) -> None:
        if adr_id not in self.linked_adr_ids:
            self.linked_adr_ids.append(adr_id)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class DesignDebtRegistry:
    """Holds design-debt items; preserves uncomfortable findings."""

    base_dir: str = ".solaris_ai_nn_architecture"
    items: List[DesignDebtItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._path = os.path.join(self.base_dir, "design_debt.jsonl")

    def record(self, item: DesignDebtItem) -> DesignDebtItem:
        self.items.append(item)
        os.makedirs(self.base_dir, exist_ok=True)
        with open(self._path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(item.to_dict(), default=str) + "\n")
        return item

    def add(self, category: str, summary: str, **kwargs: Any) -> DesignDebtItem:
        return self.record(DesignDebtItem(category=category, summary=summary,
                                          **kwargs))

    def critical_items(self) -> List[DesignDebtItem]:
        return [i for i in self.items
                if i.severity in (DesignDebtSeverity.CRITICAL,
                                  DesignDebtSeverity.HIGH)]

    def by_category(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for i in self.items:
            out[i.category] = out.get(i.category, 0) + 1
        return out

    def snapshot(self) -> Dict[str, Any]:
        return {
            "debt_count": len(self.items),
            "critical_count": len(self.critical_items()),
            "by_category": self.by_category(),
            "categories": list(DEBT_CATEGORIES),
            "path": self._path,
            "recent": [i.to_dict() for i in self.items[-8:]],
        }
