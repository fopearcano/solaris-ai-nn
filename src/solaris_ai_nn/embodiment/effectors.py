"""Simulated effectors -- the body's only outputs, all into the grid world.

Effectors validate preconditions (energy, exhaustion), drive the environment
exclusively through ``environment.step(...)``, charge the action's energy cost,
and return an :class:`ActionResult`. None of them can reach outside the
simulation: there is no filesystem, network, OS, or process access here.
"""

from __future__ import annotations

from .action_space import ACTION_SPACE, MOVEMENT_ACTIONS, ActionSpec
from .base import ActionResult, Body, EffectorCommand, Effector, Environment


def _blocked(action: str, reason: str, body: Body) -> ActionResult:
    pos = getattr(body, "position", None)
    return ActionResult(action=action, executed=False, position_before=pos,
                        position_after=pos, blocked_reason=reason,
                        consequence=f"blocked: {reason}")


def _check_preconditions(spec: ActionSpec, body: Body) -> str | None:
    if "not_exhausted" in spec.preconditions and body.energy.exhausted:
        return "exhausted"
    if not body.energy.can_afford(spec.energy_cost):
        return "insufficient_energy"
    return None


def _run_world_action(spec: ActionSpec, body: Body,
                      environment: Environment) -> ActionResult:
    """Common path: precondition check -> world step -> energy charge."""
    reason = _check_preconditions(spec, body)
    if reason is not None:
        return _blocked(spec.name, reason, body)
    outcome = environment.step(spec.name)
    body.energy.spend(spec.energy_cost)
    return ActionResult(
        action=spec.name,
        executed=True,
        position_before=outcome["position_before"],
        position_after=outcome["position_after"],
        energy_cost=spec.energy_cost,
        consequence=outcome["blocked"] or (outcome["events"][0] if outcome["events"] else "ok"),
        events=list(outcome["events"]),
        environment_changed=outcome["environment_changed"],
        blocked_reason=outcome["blocked"],
    )


class MovementEffector(Effector):
    """Moves the body (cardinal steps, approach/avoid the signal source)."""

    name = "movement"
    actions = MOVEMENT_ACTIONS

    def execute(self, command: EffectorCommand, body: Body,
                environment: Environment) -> ActionResult:
        return _run_world_action(ACTION_SPACE[command.action], body, environment)


class LookEffector(Effector):
    """Senses without moving."""

    name = "look"
    actions = ("look",)

    def execute(self, command: EffectorCommand, body: Body,
                environment: Environment) -> ActionResult:
        return _run_world_action(ACTION_SPACE["look"], body, environment)


class RestEffector(Effector):
    """Recovers energy (the only action always available when exhausted)."""

    name = "rest"
    actions = ("rest",)

    def execute(self, command: EffectorCommand, body: Body,
                environment: Environment) -> ActionResult:
        outcome = environment.step("rest")
        recovered = body.energy.rest()
        result = ActionResult(
            action="rest", executed=True,
            position_before=outcome["position_before"],
            position_after=outcome["position_after"],
            energy_cost=0.0,
            consequence=f"recovered {recovered:.2f} energy",
            events=list(outcome["events"]) + [f"recovered:{recovered:.2f}"],
        )
        return result


class PingEffector(Effector):
    """Emits a ping; the echo names the nearest object kind."""

    name = "ping"
    actions = ("emit_ping",)

    def execute(self, command: EffectorCommand, body: Body,
                environment: Environment) -> ActionResult:
        return _run_world_action(ACTION_SPACE["emit_ping"], body, environment)


class TouchEffector(Effector):
    """Interacts with an object on/next to the body (consumes markers)."""

    name = "touch"
    actions = ("touch_object",)

    def execute(self, command: EffectorCommand, body: Body,
                environment: Environment) -> ActionResult:
        return _run_world_action(ACTION_SPACE["touch_object"], body, environment)


def default_effectors() -> list[Effector]:
    return [MovementEffector(), LookEffector(), RestEffector(), PingEffector(),
            TouchEffector()]
