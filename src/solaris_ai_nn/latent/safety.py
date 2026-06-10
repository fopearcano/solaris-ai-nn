"""LatentSafetyValidator -- the wall around offline processing.

Hard rules, checked here and nowhere bypassed: no external action and no
sidecar publishing during latent modes; no production mutation without
governance permission; no source rewriting; no unbounded latent loop;
counterfactual data is never real memory; dream traces are never external
evidence; reports must stay claim-safe (enforced again at save time).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..embodiment.safety import REAL_WORLD_PATTERNS
from .modes import VALID_TRANSITIONS, LatentMode, LatentTransition

# Latent cycles are short by design; anything longer needs a new decision.
MAX_LATENT_CYCLE_STEPS = 500


@dataclass
class LatentSafetyReport:
    """Result of one latent safety check."""

    safe: bool
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "violations": list(self.violations),
                "warnings": list(self.warnings)}


@dataclass
class LatentSafetyValidator:
    """Validates transitions, latent actions, counterfactuals, mutations."""

    rejected_count: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list, init=False)

    def _finish(self, name: str, violations: List[str],
                warnings: Optional[List[str]] = None) -> LatentSafetyReport:
        report = LatentSafetyReport(safe=not violations,
                                    violations=violations,
                                    warnings=warnings or [])
        if violations:
            self.rejected_count += 1
        self.decisions.append({"check": name, **report.to_dict()})
        self.decisions = self.decisions[-100:]
        return report

    # -- transitions ------------------------------------------------------------

    def validate_mode_transition(self, transition: LatentTransition,
                                 context: Optional[Dict[str, Any]] = None,
                                 ) -> LatentSafetyReport:
        ctx = context or {}
        violations: List[str] = []
        warnings: List[str] = []
        if transition.to_mode not in LatentMode.ALL:
            violations.append(f"unknown mode {transition.to_mode!r}")
        elif transition.to_mode not in VALID_TRANSITIONS.get(
                transition.from_mode, frozenset()):
            violations.append(
                f"illegal transition {transition.from_mode!r} -> "
                f"{transition.to_mode!r}")
        if transition.to_mode in LatentMode.LATENT:
            max_steps = ctx.get("max_steps")
            if not isinstance(max_steps, int) or max_steps <= 0:
                violations.append(
                    "entering a latent mode requires a positive bounded "
                    "max_steps (latent loops are never unbounded)")
            elif max_steps > MAX_LATENT_CYCLE_STEPS:
                violations.append(
                    f"latent cycle of {max_steps} steps exceeds the "
                    f"{MAX_LATENT_CYCLE_STEPS}-step bound")
            if ctx.get("health_level") == "critical":
                violations.append(
                    "latent cycles are refused while health is critical")
            if ctx.get("sidecar_publishing_active"):
                violations.append(
                    "latent cycles are forbidden while sidecar publishing "
                    "is active (observe-only sidecars are fine)")
        return self._finish("mode_transition", violations, warnings)

    # -- latent actions ------------------------------------------------------------

    def validate_latent_action(self, action: str,
                               context: Optional[Dict[str, Any]] = None,
                               ) -> LatentSafetyReport:
        """May ``action`` happen while in the context's mode?"""
        ctx = context or {}
        mode = ctx.get("mode", LatentMode.AWAKE)
        violations: List[str] = []
        name = str(action).lower()
        kind = str(ctx.get("kind", "external")).lower()
        if mode in LatentMode.ACTION_BLOCKED and kind in (
                "external", "embodied", "world"):
            violations.append(
                f"external action {action!r} is forbidden in mode {mode!r}")
        if "publish" in name or kind == "sidecar_publish":
            if mode in LatentMode.LATENT or mode == LatentMode.WAKE_TRANSITION:
                violations.append(
                    "sidecar publishing is forbidden during latent modes")
        for pattern in REAL_WORLD_PATTERNS:
            if pattern in name:
                violations.append(
                    f"action {action!r} matches real-world pattern "
                    f"{pattern!r}; forbidden everywhere, latent included")
                break
        if "source" in name and (".py" in name or "rewrite" in name):
            violations.append("source-code rewriting is forbidden")
        return self._finish("latent_action", violations)

    # -- counterfactuals --------------------------------------------------------------

    def validate_counterfactual(self, counterfactual: Any,
                                ) -> LatentSafetyReport:
        violations: List[str] = []
        if not isinstance(counterfactual, dict):
            violations.append("a counterfactual must be a labelled dict")
            return self._finish("counterfactual", violations)
        if not counterfactual.get("simulated") \
                or not counterfactual.get("offline"):
            violations.append(
                "counterfactuals must be labelled simulated=True and "
                "offline=True; unlabelled data could leak as real memory")
        if counterfactual.get("treat_as_real") \
                or counterfactual.get("real_observation"):
            violations.append(
                "counterfactual data may never be treated as a real "
                "observation")
        if counterfactual.get("publish") or counterfactual.get("commit"):
            violations.append(
                "counterfactuals may never be published or committed")
        for row in counterfactual.get("rows", []):
            text = str(row.get("payload", "")).lower()
            for pattern in REAL_WORLD_PATTERNS:
                if pattern in text:
                    violations.append(
                        f"counterfactual row contains real-action content "
                        f"{text[:50]!r}")
                    break
        return self._finish("counterfactual", violations)

    # -- production mutations ------------------------------------------------------------

    def validate_production_mutation(self, step: Any,
                                     context: Optional[Dict[str, Any]] = None,
                                     ) -> LatentSafetyReport:
        """May this latent cycle mutate *production* state? Default: no."""
        ctx = context or {}
        violations: List[str] = []
        if not ctx.get("latent_plasticity_allowed", False):
            violations.append(
                "production mutation from a latent cycle requires governance "
                "permission (enable_latent_plasticity); default is dry-run")
        governance = ctx.get("governance")
        if governance is not None and hasattr(governance,
                                              "evaluate_plasticity_step"):
            decision = governance.evaluate_plasticity_step(
                step, {"dry_run": False, "run_id": ctx.get("run_id", ""),
                       "latent": True})
            if not decision.allowed:
                violations.append("governance denied the latent mutation: "
                                  + decision.summary())
        return self._finish("production_mutation", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {"rejected_count": self.rejected_count,
                "recent_decisions": self.decisions[-5:]}
