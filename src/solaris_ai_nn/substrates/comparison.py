"""Substrate comparison helpers -- collect per-substrate rows, render a table.

Used by ``experiments/substrate_comparison.py``. Pure formatting/aggregation;
the experiment supplies the numbers. The "energy proxy" is deliberately crude
and documented as such: throughput divided by average active units -- a rough
"work per active unit" indicator, not a power measurement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ComparisonRow:
    """One substrate's results in a comparison run."""

    substrate: str
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"substrate": self.substrate, **self.metrics}


@dataclass
class ComparisonReport:
    """All substrates' results plus a rendered table."""

    rows: List[ComparisonRow] = field(default_factory=list)

    def add(self, substrate: str, **metrics: Any) -> None:
        self.rows.append(ComparisonRow(substrate=substrate, metrics=metrics))

    def metric_names(self) -> List[str]:
        names: List[str] = []
        for row in self.rows:
            for key in row.metrics:
                if key not in names:
                    names.append(key)
        return names

    def to_dict(self) -> Dict[str, Any]:
        return {"rows": [r.to_dict() for r in self.rows]}

    def table(self) -> str:
        """Render a fixed-width comparison table (metrics x substrates)."""
        if not self.rows:
            return "(no comparison rows)"
        names = self.metric_names()
        subs = [r.substrate for r in self.rows]
        label_w = max(len("metric"), *(len(n) for n in names)) + 2
        col_w = max(12, *(len(s) for s in subs)) + 2

        def fmt(value: Any) -> str:
            if isinstance(value, float):
                return f"{value:.4f}"
            return str(value)

        lines = ["metric".ljust(label_w) + "".join(s.rjust(col_w) for s in subs)]
        lines.append("-" * (label_w + col_w * len(subs)))
        for name in names:
            cells = [fmt(r.metrics.get(name, "-")).rjust(col_w) for r in self.rows]
            lines.append(name.ljust(label_w) + "".join(cells))
        return "\n".join(lines)


def energy_proxy(updates_per_second: float, average_active_units: float) -> float:
    """Crude work-per-active-unit indicator (NOT a power measurement).

    Higher = more updates sustained per active unit. Guards the denominator so
    a fully-silent substrate doesn't divide by zero.
    """
    return updates_per_second / max(1.0, average_active_units)
