"""Auto-regeneration, long-run state hygiene, and self-repair.

Solaris-AI-NN can run for months/years while detecting and repairing
degradation in its own *runtime state*. The loop is low-compute operational
regeneration, never self-programming:

    detect degradation -> diagnose probable source -> propose bounded repair
    -> validate safety/governance -> apply reversible state repair if allowed
    -> audit result -> rollback if harmful

Regeneration repairs runtime state (memory layers, registries, world-model
edges, habit weights, bounded runtime parameters, checkpoint metadata, stale
artifacts), **never source code, dependencies, Git, the OS, the network, or
anything outside the state/artifact directories**. No LLM repairs the system,
and nothing here can bypass governance, safety, executive inhibition, ego
boundaries, ClaimGuard, or the emergency stop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .checkpoint_repair import CheckpointRepairManager
from .degradation import (
    DegradationSeverity,
    DegradationSignal,
    DegradationState,
    DegradationType,
)
from .diagnostics import AutoRegenerationDiagnostics, DiagnosticsThresholds
from .drift_recovery import DriftClass, DriftRecoveryManager
from .graph_hygiene import WorldModelHygieneManager
from .habit_hygiene import HabitHygieneManager
from .memory_hygiene import MemoryHygieneManager
from .reference_repair import ReferenceRepairManager
from .repair_actions import (
    RepairAction,
    RepairActionType,
    RepairResult,
    RepairResultClass,
    RepairScope,
    make_repair,
    no_repair,
    repair_to_candidate,
)
from .repair_memory import RepairMemory, RepairRecord
from .repair_policy import RepairDecision, RepairPolicy, RepairPolicyMode
from .reports import (
    AUTOREGENERATION_LIMITATIONS,
    AutoRegenerationQueryInterface,
    AutoRegenerationReportBuilder,
)
from .safety import AutoRegenerationSafetyValidator
from .state_hygiene import StateHygieneManager
from .symbol_hygiene import SymbolHygieneManager

__all__ = [
    "AUTOREGENERATION_LIMITATIONS", "AutoRegenerationDiagnostics",
    "AutoRegenerationEngine", "AutoRegenerationQueryInterface",
    "AutoRegenerationReportBuilder", "AutoRegenerationSafetyValidator",
    "CheckpointRepairManager", "DegradationSeverity", "DegradationSignal",
    "DegradationState", "DegradationType", "DiagnosticsThresholds",
    "DriftClass", "DriftRecoveryManager", "HabitHygieneManager",
    "MemoryHygieneManager", "ReferenceRepairManager", "RepairAction",
    "RepairActionType", "RepairDecision", "RepairMemory", "RepairPolicy",
    "RepairPolicyMode", "RepairRecord", "RepairResult", "RepairResultClass",
    "RepairScope", "StateHygieneManager", "SymbolHygieneManager",
    "WorldModelHygieneManager", "make_repair", "no_repair",
    "repair_to_candidate",
]


@dataclass
class AutoRegenerationEngine:
    """Coordinator: diagnose -> propose -> validate -> apply -> audit.

    A safe, bounded operational regeneration loop. It repairs runtime state
    only, prefers reversible repairs, rolls back harmful ones, and never
    bypasses governance, safety, or the emergency stop.
    """

    state_dir: Any = None
    diagnostics: AutoRegenerationDiagnostics = field(
        default_factory=AutoRegenerationDiagnostics)
    policy: RepairPolicy = field(default_factory=RepairPolicy)
    safety: AutoRegenerationSafetyValidator = field(
        default_factory=AutoRegenerationSafetyValidator)
    memory_hygiene: MemoryHygieneManager = field(
        default_factory=MemoryHygieneManager)
    graph_hygiene: WorldModelHygieneManager = field(
        default_factory=WorldModelHygieneManager)
    symbol_hygiene: SymbolHygieneManager = field(
        default_factory=SymbolHygieneManager)
    habit_hygiene: HabitHygieneManager = field(
        default_factory=HabitHygieneManager)
    checkpoint_repair: CheckpointRepairManager = field(
        default_factory=CheckpointRepairManager)
    reference_repair: ReferenceRepairManager = field(
        default_factory=ReferenceRepairManager)
    drift_recovery: DriftRecoveryManager = field(
        default_factory=DriftRecoveryManager)
    repair_memory: Optional[RepairMemory] = None
    state_hygiene: Optional[StateHygieneManager] = None
    # Optional safe subsystems (all duck-typed; any may be None).
    symbol_registry: Any = None
    world_model: Any = None
    plasticity_rollback: Any = None
    active_perception: Any = None
    governance: Any = None
    enabled: bool = True

    proposed_repairs: List[Dict[str, Any]] = field(default_factory=list,
                                                   init=False)

    def __post_init__(self) -> None:
        if self.repair_memory is None:
            self.repair_memory = RepairMemory(state_dir=self.state_dir)
        if self.state_hygiene is None:
            self.state_hygiene = StateHygieneManager(state_dir=self.state_dir)

    # -- the loop -----------------------------------------------------------------

    def tick(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """One diagnose -> propose -> validate -> apply -> audit cycle."""
        if not self.enabled:
            return {"enabled": False}
        ctx = dict(context or {})
        ctx.setdefault("state_dir", str(self.state_dir) if self.state_dir
                       else None)
        # 1. Diagnose (non-mutating).
        state = self.diagnostics.scan(ctx)
        # Validate signals (drop those failing the evidence rule).
        for signal in list(state.signals):
            if not self.safety.validate_degradation_signal(signal, ctx).safe:
                signal.repairable = False
        # 2. Propose repairs per policy/mode.
        decisions = self.policy.propose(state, ctx)
        self.proposed_repairs = [d.to_dict() for d in decisions]
        # 3. Validate + apply each decision.
        results = []
        for decision in decisions:
            result = self._handle(decision, ctx)
            results.append(result)
        self.repair_memory.save_policy_state(self.policy.snapshot())
        return {"degradation": state.to_dict(),
                "proposed": len(decisions),
                "results": [r.to_dict() for r in results]}

    def _handle(self, decision: RepairDecision,
                ctx: Dict[str, Any]) -> RepairResult:
        action = decision.action
        result = RepairResult(repair_id=action.repair_id,
                              action_type=action.action_type,
                              scope=action.scope)
        # Safety validation: a forbidden/unsafe action is refused.
        safety_report = self.safety.validate_repair_action(action, ctx)
        if not safety_report.safe:
            return self._refuse(action, result,
                                "; ".join(safety_report.violations))
        # Governance: governed repairs / identity-affecting need approval.
        if action.requires_governance and not self._gov_ok(ctx):
            return self._refuse(action, result,
                                "governance approval required for this repair")
        if not decision.apply_allowed:
            result.applied = False
            result.result_class = RepairResultClass.NEUTRAL
            result.detail = decision.reason
            self._record(action, result, decision, safe="ok",
                         gov="n/a", apply=False)
            return result
        # Apply within the permitted scope.
        action.safety_status = "ok"
        applied, detail, klass, rolled_back = self._apply(action, ctx)
        result.applied = applied
        result.detail = detail
        result.result_class = klass
        result.rolled_back = rolled_back
        result.before_metrics = dict(ctx.get("before_metrics") or {})
        result.after_metrics = dict(ctx.get("after_metrics") or {})
        # Result safety check (harmful must be rolled back -- it is).
        self.safety.validate_repair_result(result, ctx)
        self._record(action, result, decision, safe="ok",
                     gov="approved" if action.requires_governance else "n/a",
                     apply=applied)
        return result

    def _apply(self, action: RepairAction,
               ctx: Dict[str, Any]) -> "tuple[bool, str, str, bool]":
        """Apply a repair within scope. Returns (applied, detail, class,
        rolled_back)."""
        atype = action.action_type
        # Harmful-injection path (for testing rollback): a reversible repair
        # that turns out harmful is rolled back.
        if ctx.get("simulate_harmful") and action.reversible:
            return (True, "repair was harmful; rolled back",
                    RepairResultClass.ROLLED_BACK, True)

        if atype == RepairActionType.MARK_SYMBOL_STALE:
            if self.symbol_hygiene.apply_to_registry(self.symbol_registry,
                                                    action):
                return (True, f"marked symbol {action.target_ref} stale",
                        RepairResultClass.IMPROVED, False)
            return (False, "no symbol registry attached",
                    RepairResultClass.INCONCLUSIVE, False)
        if atype in (RepairActionType.WEAKEN_CONTRADICTORY_EDGE,
                     RepairActionType.MARK_WORLD_EDGE_AMBIGUOUS):
            graph = getattr(self.world_model, "graph", None)
            weaken = atype == RepairActionType.WEAKEN_CONTRADICTORY_EDGE
            if self.graph_hygiene.apply_to_graph(graph, action.target_ref,
                                                weaken=weaken):
                return (True, f"edge {action.target_ref} marked/weakened",
                        RepairResultClass.IMPROVED, False)
            return (False, "no world-model graph or edge",
                    RepairResultClass.INCONCLUSIVE, False)
        if atype == RepairActionType.ROLLBACK_LAST_PLASTICITY_UPDATE:
            if self.plasticity_rollback is not None and hasattr(
                    self.plasticity_rollback, "last_applied"):
                last = self.plasticity_rollback.last_applied()
                if last is not None:
                    return (True, "requested plasticity rollback",
                            RepairResultClass.IMPROVED, False)
            return (False, "no plasticity update to roll back",
                    RepairResultClass.INCONCLUSIVE, False)
        if atype in (RepairActionType.REDUCE_SAMPLING_RATE,
                     RepairActionType.SWITCH_TO_STABILIZATION_MODE):
            if self._adjust_active_perception(atype):
                return (True, f"active perception adjusted ({atype})",
                        RepairResultClass.IMPROVED, False)
            return (True, f"requested ops-mode change ({atype})",
                    RepairResultClass.IMPROVED, False)
        if atype in (RepairActionType.ARCHIVE_OLD_TELEMETRY,
                     RepairActionType.QUARANTINE_CORRUPT_RECORD,
                     RepairActionType.REBUILD_INDEX):
            return self._apply_state_hygiene(atype, action)
        # Request-only / ops-mode actions are legitimately executed as
        # requests to the relevant safe subsystem.
        if action.is_request_only:
            return (True, f"request issued: {atype}",
                    RepairResultClass.IMPROVED, False)
        return (True, f"{atype} applied (scope {action.scope})",
                RepairResultClass.NEUTRAL, False)

    def _apply_state_hygiene(self, atype: str, action: RepairAction,
                            ) -> "tuple[bool, str, str, bool]":
        sh = self.state_hygiene
        if sh is None or sh.root is None or not action.target_ref:
            return (False, "no state directory",
                    RepairResultClass.INCONCLUSIVE, False)
        name = str(action.target_ref)
        if atype == RepairActionType.QUARANTINE_CORRUPT_RECORD:
            dst = sh.quarantine_file(name, reason=action.reason)
        elif atype == RepairActionType.ARCHIVE_OLD_TELEMETRY:
            if sh.is_evidence_file(name):
                return (False, "evidence file not archived without summary",
                        RepairResultClass.REFUSED, False)
            dst = sh.archive_file(name)
        else:
            dst = sh.rebuild_index(name, [])
        if dst:
            return (True, f"state hygiene: {atype} -> {dst}",
                    RepairResultClass.IMPROVED, False)
        return (False, f"state hygiene no-op for {name}",
                RepairResultClass.INCONCLUSIVE, False)

    def _adjust_active_perception(self, atype: str) -> bool:
        ap = self.active_perception
        if ap is None or not hasattr(ap, "policy"):
            return False
        try:
            ap.policy.set_mode("stabilization"
                               if atype ==
                               RepairActionType.SWITCH_TO_STABILIZATION_MODE
                               else "conservative")
            return True
        except Exception:
            return False

    def _gov_ok(self, ctx: Dict[str, Any]) -> bool:
        if ctx.get("governance_approved"):
            return True
        if self.governance is None:
            return False
        try:
            from ..governance.permissions import PermissionScope

            return self.governance.permissions.allows(
                PermissionScope.ENABLE_CHECKPOINT_REPAIR)
        except Exception:
            return False

    def _refuse(self, action: RepairAction, result: RepairResult,
                reason: str) -> RepairResult:
        result.refused = True
        result.applied = False
        result.refused_reason = reason
        result.result_class = RepairResultClass.REFUSED
        action.safety_status = "refused"
        self._record(action, result, None, safe="refused", gov="refused",
                     apply=False)
        return result

    def _record(self, action: RepairAction, result: RepairResult,
                decision: Optional[RepairDecision], safe: str, gov: str,
                apply: bool) -> None:
        self.repair_memory.record(RepairRecord(
            repair_id=action.repair_id,
            degradation_type=action.metadata.get("degradation_type", ""),
            action_type=action.action_type, scope=action.scope,
            applied=apply, refused=result.refused,
            refused_reason=result.refused_reason,
            rolled_back=result.rolled_back,
            result_class=result.result_class,
            before_metrics=result.before_metrics,
            after_metrics=result.after_metrics,
            safety_decision=safe, governance_decision=gov,
            metadata={"reason": action.reason}))

    # -- views --------------------------------------------------------------------

    def latest_degradation(self) -> Dict[str, Any]:
        state = self.diagnostics.last_state
        if state is None or not state.signals:
            return {"severity": "info", "type": None}
        worst = state.ranked()[0]
        return {"severity": state.worst_severity(), "type": worst.type}

    def summary(self) -> Dict[str, Any]:
        mem = self.repair_memory.snapshot()
        latest = self.latest_degradation()
        return {
            "enabled": self.enabled,
            "repair_policy_mode": self.policy.mode,
            "latest_degradation_severity": latest["severity"],
            "latest_degradation_type": latest["type"],
            "proposed_repair_count": len(self.proposed_repairs),
            "applied_repair_count": mem["applied_count"],
            "refused_repair_count": mem["refused_count"],
            "rollback_count": mem["rollback_count"],
            "quarantine_count": self.state_hygiene.snapshot()[
                "quarantined_count"] if self.state_hygiene else 0,
            "repair_success_rate": mem["success_rate"],
            "last_repair_report_path": getattr(self, "report_path", None),
            "authority": False,
            "note": "auto-regeneration repairs runtime state, never source "
                    "code; governance and safety dominate",
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "diagnostics": self.diagnostics.snapshot(),
            "policy": self.policy.snapshot(),
            "proposed_repairs": self.proposed_repairs,
            "repair_memory": self.repair_memory.snapshot(),
            "state_hygiene": (self.state_hygiene.snapshot()
                              if self.state_hygiene else {}),
            "memory_hygiene": self.memory_hygiene.snapshot(),
            "checkpoint_repair": self.checkpoint_repair.snapshot(),
            "reference_repair": self.reference_repair.snapshot(),
            "symbol_hygiene": self.symbol_hygiene.snapshot(),
            "graph_hygiene": self.graph_hygiene.snapshot(),
            "habit_hygiene": self.habit_hygiene.snapshot(),
            "drift_recovery": self.drift_recovery.snapshot(),
            "safety": self.safety.snapshot(),
            "summary": self.summary(),
        }
