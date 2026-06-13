"""Drift recovery -- distinguish adaptation from runaway, recover carefully.

The :class:`DriftRecoveryManager` reads LongRunDriftMonitor reports and
classifies drift as healthy adaptation, stagnation, instability, runaway, or
unknown, then proposes bounded recovery (stabilization, reduced sampling,
more consolidation, latent replay, checkpoint, rollback of the last
plasticity update, governance review, or safe shutdown). It does not erase
adaptation as if all drift were bad, nor preserve runaway drift; when
uncertain it prefers stabilization and reporting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .repair_actions import RepairAction, RepairActionType, make_repair


class DriftClass:
    HEALTHY_ADAPTATION = "healthy_adaptation"
    STAGNATION = "stagnation"
    INSTABILITY = "instability"
    RUNAWAY = "runaway"
    UNKNOWN = "unknown"

    ALL = (HEALTHY_ADAPTATION, STAGNATION, INSTABILITY, RUNAWAY, UNKNOWN)


@dataclass
class DriftRecoveryManager:
    """Classifies drift and proposes bounded recovery actions."""

    history: List[Dict[str, Any]] = field(default_factory=list)

    def classify(self, context: Dict[str, Any]) -> str:
        drift = (context or {}).get("drift") or {}
        classification = (drift.get("classification")
                          or drift.get("latest_classification"))
        velocity = drift.get("drift_velocity")
        if classification == "fast_warning":
            # Very high velocity reads as runaway; moderate as instability.
            if velocity is not None and float(velocity) > 2.0:
                return DriftClass.RUNAWAY
            return DriftClass.INSTABILITY
        if classification == "inert_warning" \
                or (context or {}).get("stagnation_status") in (
                    "stagnating", "inert"):
            return DriftClass.STAGNATION
        if classification == "healthy_slow":
            return DriftClass.HEALTHY_ADAPTATION
        return DriftClass.UNKNOWN

    def propose(self, context: Dict[str, Any]) -> List[RepairAction]:
        drift_class = self.classify(context)
        self.history.append({"class": drift_class})
        self.history = self.history[-100:]
        actions: List[RepairAction] = []
        if drift_class == DriftClass.HEALTHY_ADAPTATION:
            # Do not repair adaptation away.
            return []
        if drift_class == DriftClass.RUNAWAY:
            actions.append(make_repair(
                RepairActionType.SWITCH_TO_STABILIZATION_MODE,
                target_ref="drift",
                reason="runaway drift detected",
                expected_benefit="reduce uncontrolled drift"))
            actions.append(make_repair(
                RepairActionType.ROLLBACK_LAST_PLASTICITY_UPDATE,
                target_ref="drift",
                reason="runaway drift may follow the last plasticity update",
                expected_benefit="revert the most recent mutation"))
        elif drift_class == DriftClass.INSTABILITY:
            actions.append(make_repair(
                RepairActionType.SWITCH_TO_STABILIZATION_MODE,
                target_ref="drift",
                reason="unstable drift",
                expected_benefit="stabilize the runtime"))
            actions.append(make_repair(
                RepairActionType.REDUCE_SAMPLING_RATE, target_ref="drift",
                reason="reduce input variability while stabilizing",
                expected_benefit="lower stimulus variability"))
        elif drift_class == DriftClass.STAGNATION:
            actions.append(make_repair(
                RepairActionType.REQUEST_LATENT_REPLAY, target_ref="drift",
                reason="stagnation; consolidate and replay",
                expected_benefit="consolidate without forcing novelty"))
        else:  # unknown -> prefer stabilization + report
            actions.append(make_repair(
                RepairActionType.SWITCH_TO_STABILIZATION_MODE,
                target_ref="drift",
                reason="drift classification unknown; stabilize and report",
                expected_benefit="prefer caution under uncertainty"))
            actions.append(make_repair(
                RepairActionType.GENERATE_OPERATOR_REVIEW_REQUEST,
                target_ref="drift",
                reason="drift unclear; request review",
                expected_benefit="human review of unclear drift"))
        return actions

    def snapshot(self) -> Dict[str, Any]:
        return {"recent_classes": [h["class"] for h in self.history[-5:]]}
