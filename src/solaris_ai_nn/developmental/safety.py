"""Developmental safety -- months of runtime, none of it unguarded.

Hard rules: no month/year mode without governance approval, no memory
growth without limits, no pruning of raw evidence without a summary, no
source-code rewriting, no real-world action, no sidecar commits, no
counterfactual treated as real history, no ClaimGuard violations in
autobiographical reports, no self-description as conscious/alive/person.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

HARD_RULES = (
    "no unbounded month/year mode without governance approval",
    "no memory growth without limits",
    "no pruning of raw evidence without a summary",
    "no source-code rewriting",
    "no real-world action",
    "no sidecar committed actions",
    "no counterfactual treated as real history",
    "no ClaimGuard violations in autobiographical reports",
    "no self-description as conscious, alive, or a person",
)

_FORBIDDEN_SELF_DESCRIPTIONS = (
    r"\bis conscious\b", r"\bis alive\b", r"\bis a person\b",
    r"\bis sentient\b", r"\bhas feelings\b", r"\bcame alive\b",
)


@dataclass
class DevelopmentalSafetyReport:
    safe: bool
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "violations": list(self.violations)}


@dataclass
class DevelopmentalSafetyValidator:
    """Validates configs, memory, pruning, history, and reports."""

    rejected_count: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list,
                                            init=False)

    def _finish(self, check: str,
                violations: List[str]) -> DevelopmentalSafetyReport:
        report = DevelopmentalSafetyReport(safe=not violations,
                                           violations=violations)
        if violations:
            self.rejected_count += 1
        self.decisions.append({"check": check, **report.to_dict()})
        self.decisions = self.decisions[-100:]
        return report

    # -- validations ----------------------------------------------------------------

    def validate_config(self, runtime: Any,
                        governance: Any = None,
                        ) -> DevelopmentalSafetyReport:
        violations: List[str] = []
        if getattr(runtime, "enable_month_scale", False):
            approved = (governance is not None
                        and governance.permissions.allows(
                            "enable_month_scale_testing"))
            if not approved:
                violations.append(
                    "month-scale mode requires explicit governance "
                    "approval (enable_month_scale_testing)")
        if getattr(runtime, "enable_year_scale", False):
            approved = (governance is not None
                        and governance.permissions.allows(
                            "enable_year_scale_testing"))
            if not approved:
                violations.append(
                    "year-scale mode requires explicit governance "
                    "approval (enable_year_scale_testing)")
        if getattr(runtime, "max_steps", None) is None \
                and getattr(runtime, "max_duration_s", None) is None:
            violations.append("a developmental run must be bounded by "
                              "steps or duration; unbounded runs need a "
                              "governed run manifest")
        return self._finish("config", violations)

    def validate_memory(self, manager: Any,
                        ) -> DevelopmentalSafetyReport:
        violations: List[str] = []
        for layer in manager.over_budget_layers():
            violations.append(f"memory layer {layer!r} is over budget; "
                              "growth without limits is forbidden")
        return self._finish("memory", violations)

    def validate_pruning(self, pruned_items: List[Any],
                         summary: str) -> DevelopmentalSafetyReport:
        violations: List[str] = []
        if pruned_items and not str(summary).strip():
            violations.append(
                "pruning raw evidence without an evidence summary is "
                "forbidden; nothing is silently destroyed")
        return self._finish("pruning", violations)

    def validate_history_event(self, event: Any,
                               context: Optional[Dict[str, Any]] = None,
                               ) -> DevelopmentalSafetyReport:
        """Counterfactual/offline output never enters real history."""
        ctx = dict(context or {})
        violations: List[str] = []
        text = str(getattr(event, "text", event)).lower()
        if (ctx.get("counterfactual_active")
                or "counterfactual" in text or "dream" in text) \
                and not getattr(event, "simulated", True) \
                and "counterfactual" not in text:
            violations.append("counterfactual output cannot be recorded "
                              "as real history")
        if ("counterfactual" in text or "dream" in text) \
                and ("actually happened" in text
                     or "really observed" in text):
            violations.append("counterfactual content described as real "
                              "observation")
        return self._finish("history_event", violations)

    def validate_report(self, text: str) -> DevelopmentalSafetyReport:
        from ..governance.compliance import ClaimGuard

        violations: List[str] = []
        lowered = str(text).lower()
        for pattern in _FORBIDDEN_SELF_DESCRIPTIONS:
            if re.search(pattern, lowered):
                violations.append(
                    f"forbidden self-description matching {pattern!r}; "
                    "the runtime is measured, not declared alive")
        if not ClaimGuard().is_safe(str(text)):
            violations.append("the report contains claims ClaimGuard "
                              "flags as unsupported")
        return self._finish("report", violations)

    def validate_paths(self, state_dir: Any,
                       artifact_dir: Any = None,
                       ) -> DevelopmentalSafetyReport:
        violations: List[str] = []
        for label, value in (("state_dir", state_dir),
                             ("artifact_dir", artifact_dir)):
            if value is None:
                continue
            path = str(Path(value))
            if path.startswith(("/etc", "/usr", "/bin", "/sys",
                                "/proc")):
                violations.append(f"{label} {path!r} is outside the "
                                  "allowed workspace paths")
        return self._finish("paths", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "recent_decisions": self.decisions[-8:],
        }
