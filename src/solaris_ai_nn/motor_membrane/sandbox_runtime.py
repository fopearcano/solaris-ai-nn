"""Embodiment sandbox runtime -- the one place a motor action may (simulated) run.

The :class:`EmbodimentSandboxRuntime` receives a proposed :class:`MotorAction`,
logs it to the ledger, validates it through the motor contract, runs the veto
layer, passes it through the always-on actuation firewall, and only then
executes it on a simulated actuator -- recording the result and its predicted
vs observed consequence. Bounded by default; dry-run records without changing
simulation; emergency mode stops execution. No real-world effect is ever
possible.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .action_ledger import ActionLedger
from .actions import MotorAction, MotorActionScope, MotorActionStatus
from .actuation_firewall import ActuationFirewall
from .consequence_model import ConsequenceModel
from .motor_contract import MotorContractValidator
from .safety import MotorMembraneSafetyValidator
from .simulated_actuators import GridWorldActuator, InternalActuator
from .veto import ActionVetoLayer


@dataclass
class EmbodimentSandboxRuntime:
    """Bounded, simulation-only runtime for motor actions behind the firewall."""

    state_dir: Optional[str] = None
    sandbox_id: str = "sandbox"
    profile_id: str = "gridworld_minimal"
    max_steps: int = 80
    max_actions_per_step: int = 1
    enable_gridworld: bool = True
    enable_internal_actions: bool = True
    dry_run: bool = False
    seed: int = 7
    emergency_mode: bool = False
    bus: Any = None

    def __post_init__(self) -> None:
        self.firewall = ActuationFirewall()
        self.contract = MotorContractValidator(
            sandbox_roots=[self.state_dir] if self.state_dir else [])
        self.veto_layer = ActionVetoLayer()
        self.safety = MotorMembraneSafetyValidator()
        self.ledger = ActionLedger(state_dir=self.state_dir)
        self.consequence = ConsequenceModel()
        self._world = None
        self._actuators: List[Any] = []
        self.step_count = 0
        self.action_count = 0
        self.simulated_action_count = 0
        self.dry_run_action_count = 0
        self.executed_count = 0
        self.started_at = time.time()

    def initialize(self) -> Dict[str, Any]:
        if self.enable_gridworld:
            from ..embodiment.grid_world import GridWorld

            self._world = GridWorld(seed=self.seed)
            self._actuators.append(GridWorldActuator(self._world))
        if self.enable_internal_actions:
            self._actuators.append(InternalActuator())
        return {"profile_id": self.profile_id, "dry_run": self.dry_run,
                "actuators": [a.name for a in self._actuators],
                "real_world_authority": False}

    # -- the gated pipeline -----------------------------------------------------

    def submit(self, action: MotorAction,
               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run one proposed action through the full gated pipeline."""
        ctx = dict(context or {})
        ctx.setdefault("executive_validated", True)
        ctx["emergency_mode"] = self.emergency_mode or ctx.get(
            "emergency_mode", False)
        self.action_count += 1

        # 1. Mandatory pre-execution ledger record.
        record = self.ledger.record_proposal(
            action, proposal_source=ctx.get("proposal_source", "executive"))

        # 2. Motor contract.
        contract_violations = self.contract.validate_action(action, ctx)
        if action.target_ref:
            contract_violations += self.contract.validate_target(
                action.target_ref, ctx)
        # 3. Veto layer.
        veto = self.veto_layer.evaluate(action, ctx)
        # 4. Firewall (always on).
        decision = self.firewall.evaluate(action, ctx)

        if contract_violations or veto is not None or not decision.allowed:
            status = (MotorActionStatus.VETOED if veto is not None
                      else MotorActionStatus.BLOCKED_BY_FIREWALL)
            action.status = status
            self.ledger.update_decisions(
                record, executive=ctx.get("executive_decision", "validated"),
                firewall="blocked" if not decision.allowed else "n/a",
                safety="blocked" if contract_violations else "ok",
                final_status=status,
                result_summary=(veto.reason if veto else decision.reason))
            self._publish_block(action, decision, veto)
            return {"executed": False, "status": status,
                    "firewall": decision.to_dict(),
                    "veto": veto.to_dict() if veto else None,
                    "contract_violations": [v.to_dict()
                                            for v in contract_violations]}

        # 5. Dry-run: record, but change nothing.
        if self.dry_run or action.scope == MotorActionScope.DRY_RUN_ONLY:
            action.status = MotorActionStatus.DRY_RUN_RECORDED
            self.dry_run_action_count += 1
            self.ledger.update_decisions(
                record, executive="validated", firewall="allowed",
                safety="ok", final_status=MotorActionStatus.DRY_RUN_RECORDED,
                result_summary="dry-run (no simulation state change)")
            return {"executed": False, "status": action.status,
                    "dry_run": True}

        # 6. Execute on a simulated actuator.
        pred = self.consequence.predict(action, ctx.get("situation"))
        actuator = self._select_actuator(action)
        if actuator is None:
            action.status = MotorActionStatus.FAILED
            self.ledger.update_decisions(record, final_status=action.status,
                                         result_summary="no actuator")
            return {"executed": False, "status": action.status,
                    "reason": "no actuator"}
        result = actuator.execute(action)
        self.ledger.record_result(result)
        self.consequence.record(action.action_id, result,
                                ctx.get("situation_after"))
        action.status = MotorActionStatus.EXECUTED_IN_SIMULATION
        self.simulated_action_count += 1
        self.executed_count += 1
        self.ledger.update_decisions(
            record, executive="validated", firewall="allowed", safety="ok",
            governance=ctx.get("governance_decision", "ok"),
            final_status=MotorActionStatus.EXECUTED_IN_SIMULATION,
            result_summary=result.effect_summary)
        self._publish_reaction(result)
        return {"executed": True, "status": action.status,
                "result": result.to_dict(),
                "prediction": pred.to_dict()}

    def step(self, actions: List[MotorAction],
             context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Submit up to ``max_actions_per_step`` actions for one step."""
        self.step_count += 1
        out = []
        for action in actions[:self.max_actions_per_step]:
            out.append(self.submit(action, context))
        return out

    def _select_actuator(self, action: MotorAction) -> Any:
        for a in self._actuators:
            if a.can_handle(action):
                return a
        return None

    def _publish_reaction(self, result: Any) -> None:
        if self.bus is None:
            return
        try:
            self.bus.publish("reaction", "motor_membrane",
                             {"valence": result.reaction_valence,
                              "simulated": True,
                              "origin": "simulated_motor_action"},
                             step=self.step_count)
        except Exception:
            pass

    def _publish_block(self, action: MotorAction, decision: Any,
                       veto: Any) -> None:
        if self.bus is None:
            return
        try:
            self.bus.publish("safety_event", "motor_membrane",
                             {"blocked_action": action.action_type,
                              "reason": (veto.reason if veto
                                         else decision.reason),
                              "real_world_attempt":
                                  decision.is_real_world_attempt},
                             step=self.step_count)
        except Exception:
            pass

    def request_emergency_stop(self) -> None:
        self.emergency_mode = True

    def summary(self) -> Dict[str, Any]:
        latest = (self.firewall.decisions[-1].to_dict()
                  if self.firewall.decisions else None)
        return {
            "enabled": True,
            "profile_id": self.profile_id,
            "real_world_authority": False,
            "dry_run": self.dry_run,
            "step_count": self.step_count,
            "action_count": self.action_count,
            "simulated_action_count": self.simulated_action_count,
            "dry_run_action_count": self.dry_run_action_count,
            "executed_count": self.executed_count,
            "veto_count": self.veto_layer.veto_count(),
            "blocked_real_world_count": self.firewall.blocked_real_world_count,
            "firewall_enabled": self.firewall.enabled,
            "firewall_can_be_disabled": False,
            "latest_firewall_decision": latest,
            "sandbox_health": self.sandbox_health(),
            "ledger_write_failures": self.ledger.write_failures,
            "prediction_accuracy": self.consequence.prediction_accuracy(),
            "action_ledger_path": self.ledger.actions_path,
            "pilot3_report_path": getattr(self, "pilot3_report_path", None),
            "emergency_mode": self.emergency_mode,
        }

    def sandbox_health(self) -> str:
        """Coarse sandbox integrity signal for Ops ('ok' / 'degraded').

        Degraded if the ledger could not persist, or if the gridworld body is
        expected but its snapshot is unreadable (possible corruption).
        """
        if self.ledger.write_failures:
            return "degraded"
        if self.enable_gridworld and self._world is not None:
            try:
                snap = self._world.snapshot()
                if not isinstance(snap, dict):
                    return "degraded"
            except Exception:
                return "corrupt"
        return "ok"

    def snapshot(self) -> Dict[str, Any]:
        return {
            "summary": self.summary(),
            "firewall": self.firewall.snapshot(),
            "veto": self.veto_layer.snapshot(),
            "ledger": self.ledger.snapshot(),
            "consequence": self.consequence.snapshot(),
            "contract": self.contract.snapshot(),
            "safety": self.safety.snapshot(),
            "world": (self._world.snapshot() if self._world is not None
                      else None),
        }
