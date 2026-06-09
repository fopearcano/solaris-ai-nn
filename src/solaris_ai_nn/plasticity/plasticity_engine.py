"""PlasticityEngine -- propose, validate, apply, log, and roll back mutations.

The engine is the controller for safe self-modification. It builds a context
from telemetry / Logos / habit / synthesis state, asks the :class:`PlasticityPolicy`
for proposals, validates each through the :class:`PlasticitySafetyValidator`,
applies the safe ones via the :class:`TargetRegistry`, registers rollback data,
and audits *every* proposal, rejection, application, and rollback.

Nothing here edits source code, deletes files, or runs unbounded. Plasticity is
off unless a runner enables it, and a dry-run mode logs proposals without
applying them.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..utils.logging import get_logger
from ..utils.math import norm
from .audit import PlasticityAuditLog
from .mutation import (
    APPLIED,
    REJECTED,
    PlasticityChange,
    PlasticityResult,
    PlasticityStep,
    PlasticityTarget,
    TargetRegistry,
)
from .policy import PlasticityPolicy
from .rollback import RollbackManager
from .safety import PlasticitySafetyValidator

if TYPE_CHECKING:
    from ..bridges.neural_bridge import SolarisNeuralBridge
    from ..plasticity.synthesis_pruning import SynthesisPruner

logger = get_logger(__name__)


@dataclass
class PlasticityEngine:
    """Controlled self-modification controller (off by default at the runner)."""

    bridge: "SolarisNeuralBridge"
    synthesis: Optional["SynthesisPruner"] = None
    runner: Any = None
    audit_path: Optional[str] = None
    run_id: str = ""
    session_id: str = ""
    state_dir: str = ""
    dry_run: bool = False
    policy: PlasticityPolicy = None  # type: ignore[assignment]
    validator: PlasticitySafetyValidator = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.registry = TargetRegistry(self.bridge, synthesis=self.synthesis, runner=self.runner)
        self.policy = self.policy or PlasticityPolicy()
        self.validator = self.validator or PlasticitySafetyValidator()
        self.rollback_manager = RollbackManager()
        if self.audit_path is None and self.state_dir:
            self.audit_path = str(Path(self.state_dir) / "plasticity_audit.jsonl")
        self.audit = PlasticityAuditLog(
            self.audit_path or "plasticity_audit.jsonl",
            run_id=self.run_id, session_id=self.session_id,
        )
        self.applied_count = 0
        self.rejected_count = 0
        self.rollback_count = 0
        self.last_applied: Optional[PlasticityStep] = None
        self.last_rejected: Optional[PlasticityStep] = None
        self._error_high_streak = 0
        self._error_low_streak = 0

    # -- context ------------------------------------------------------------

    def build_context(self) -> Dict[str, Any]:
        """Assemble the policy input from current telemetry / substrate state."""
        b = self.bridge
        tele = b.telemetry
        recent_error = tele.recent_prediction_error
        if tele.readout_updates > 0:
            if recent_error >= self.policy.error_high:
                self._error_high_streak += 1
                self._error_low_streak = 0
            elif recent_error <= self.policy.error_low:
                self._error_low_streak += 1
                self._error_high_streak = 0
            else:
                self._error_high_streak = 0
                self._error_low_streak = 0

        logos = getattr(b, "_logos", None)
        division = logos.division if logos is not None else 0.0
        union = logos.union if logos is not None else 0.0
        fracture = logos.fracture if logos is not None else 0.0

        # Recent absence / reaction stats from the bridge trace.
        recent = b.trace.records[-50:]
        absence = sum(1 for r in recent if r.category == "event" and r.data.get("is_absence"))
        events = sum(1 for r in recent if r.category == "event")
        positive = sum(1 for r in recent if r.category == "reaction" and r.data.get("valence", 0) > 0)
        absence_ratio = (absence / events) if events else 0.0

        # Strongest (most-repeated) habit pathway.
        strongest_habit = None
        if b.habit.counts:
            key = max(b.habit.counts, key=lambda k: b.habit.counts[k])
            strongest_habit = {
                "pattern": key[0], "action": key[1],
                "weight": b.habit.weights.get(key, 0.0), "count": b.habit.counts[key],
            }

        # Unused readout pathways (small but non-zero weights).
        thr = self.synthesis.readout_threshold if self.synthesis is not None else 0.01
        unused = sum(1 for row in b.readout.weights for w in row if 0.0 < abs(w) < thr)

        lifetime_step = (
            self.runner.telemetry.lifetime_steps if self.runner is not None else tele.steps
        )
        return {
            "run_id": self.run_id,
            "session_id": self.session_id,
            "lifetime_step": lifetime_step,
            "recent_error": recent_error,
            "error_high_streak": self._error_high_streak,
            "error_low_streak": self._error_low_streak,
            "logos_division": division,
            "logos_union": union,
            "logos_fracture": fracture,
            "absence_ratio": absence_ratio,
            "positive_reactions": positive,
            "strongest_habit": strongest_habit,
            "unused_pathways": unused,
            "current": self.registry.current_values(),
        }

    # -- propose / apply ----------------------------------------------------

    def propose(self, context: Optional[Dict[str, Any]] = None) -> List[PlasticityStep]:
        """Ask the policy for proposed steps and audit each as 'proposed'."""
        ctx = context or self.build_context()
        steps = self.policy.propose(ctx)
        for step in steps:
            self.audit.proposed(step)
        return steps

    def _current_state(self) -> Dict[str, Any]:
        return {"active_run": True, "state_dir": self.state_dir}

    def apply(self, step: PlasticityStep) -> PlasticityResult:
        """Validate and (unless dry-run) apply a single step."""
        report = self.validator.validate(step, self._current_state())
        step.safety_result = report.to_dict()

        if not report.safe:
            step.status = REJECTED
            self.rejected_count += 1
            self.last_rejected = step
            self.audit.rejected(step)
            return PlasticityResult(
                step_id=step.step_id, status=REJECTED, applied=False,
                message=self.validator.explain_rejection(step, self._current_state()),
                old_value=step.change.old_value, new_value=step.change.new_value,
                safety=report.to_dict())

        if not self.registry.has(step.target):
            step.status = REJECTED
            self.rejected_count += 1
            self.last_rejected = step
            self.audit.rejected(step)
            return PlasticityResult(
                step_id=step.step_id, status=REJECTED, applied=False,
                message=f"no mutable parameter {step.target.label()!r}",
                safety=report.to_dict())

        if self.dry_run:
            return PlasticityResult(
                step_id=step.step_id, status="proposed", applied=False,
                message="dry-run: validated but not applied",
                old_value=step.change.old_value, new_value=step.change.new_value,
                safety=report.to_dict())

        # Apply for real.
        old_actual = self.registry.get(step.target)
        self.registry.set(step.target, step.change.new_value)
        step.change.old_value = old_actual
        step.rollback_data = old_actual
        step.status = APPLIED
        step.observed_effect = {
            "applied_value": self.registry.get(step.target),
            "reservoir_norm": norm(self.bridge.esn.state),
        }
        self.rollback_manager.register(step)
        self.applied_count += 1
        self.last_applied = step
        self.audit.applied(step)
        return PlasticityResult(
            step_id=step.step_id, status=APPLIED, applied=True,
            message="applied", old_value=old_actual, new_value=step.change.new_value,
            safety=report.to_dict())

    def apply_many(self, steps: List[PlasticityStep]) -> List[PlasticityResult]:
        return [self.apply(s) for s in steps]

    def evaluate(self) -> List[PlasticityResult]:
        """Propose from current state, then apply (respecting dry-run)."""
        return self.apply_many(self.propose())

    # -- rollback -----------------------------------------------------------

    def rollback(self, step_id: str) -> PlasticityResult:
        result = self.rollback_manager.rollback(step_id, self.registry)
        rec = self.rollback_manager.records.get(step_id)
        if rec is not None:
            audit_step = PlasticityStep(
                target=rec.target,
                change=PlasticityChange(old_value=rec.new_value, new_value=rec.old_value,
                                        expected_effect="restore previous value"),
                reason="rollback", trigger_source="rollback",
                step_id=rec.step_id, run_id=self.run_id, session_id=self.session_id)
            self.audit.rollback(audit_step, result)
        if result.applied:
            self.rollback_count += 1
        return result

    def rollback_last(self) -> PlasticityResult:
        rec = self.rollback_manager.last_applied()
        if rec is None:
            return PlasticityResult(step_id="", status="rollback_failed", applied=False,
                                    message="no applied plasticity step to roll back")
        return self.rollback(rec.step_id)

    def load_history_from_audit(self) -> int:
        """Rebuild rollback records from the audit log (for cross-process rollback)."""
        rows = self.audit.read_all()
        rolled_back = {r["step_id"] for r in rows if r["event_type"] in ("rollback", "rollback_failed")}
        loaded = 0
        for row in rows:
            if row["event_type"] != "applied":
                continue
            label = str(row["target"])
            component, _, parameter = label.partition(".")
            step = PlasticityStep(
                target=PlasticityTarget(component, parameter),
                change=PlasticityChange(old_value=row.get("old_value"),
                                        new_value=row.get("new_value")),
                step_id=row["step_id"], run_id=self.run_id, session_id=self.session_id)
            self.rollback_manager.register(step)
            if row["step_id"] in rolled_back:
                self.rollback_manager.records[row["step_id"]].rolled_back = True
            loaded += 1
        return loaded

    # -- snapshot -----------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        return {
            "enabled": True,
            "dry_run": self.dry_run,
            "applied_count": self.applied_count,
            "rejected_count": self.rejected_count,
            "rollback_count": self.rollback_count,
            "last_applied": self.last_applied.to_dict() if self.last_applied else None,
            "last_rejected": self.last_rejected.to_dict() if self.last_rejected else None,
            "current_parameters": self.registry.current_values(),
            "safety_status": "ok" if self.rejected_count == 0 else f"{self.rejected_count} rejected",
            "audit_path": self.audit_path,
            "rollback": self.rollback_manager.to_dict(),
        }
