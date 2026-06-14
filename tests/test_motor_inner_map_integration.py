"""Motor <-> Inner MAP: status field on the model and state-graph nodes."""

from __future__ import annotations

from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph
from solaris_ai_nn.motor_membrane import (
    EmbodimentSandboxRuntime,
    MotorAction,
    MotorActionScope,
    MotorActionType,
)


def test_model_has_motor_membrane_field():
    model = InnerMapModel()
    assert model.motor_membrane is None


def test_observer_populates_motor_membrane(tmp_path):
    rt = EmbodimentSandboxRuntime(state_dir=str(tmp_path))
    rt.initialize()
    rt.submit(MotorAction(MotorActionType.MOVE_EAST,
                          scope=MotorActionScope.SANDBOX_ONLY))
    observer = InnerMapObserver(motor_membrane=rt)
    model = observer.update()
    assert model.motor_membrane is not None
    assert model.motor_membrane["real_world_authority"] is False
    assert model.motor_membrane["firewall_enabled"] is True


def test_state_graph_has_motor_nodes():
    g = build_default_state_graph()
    for node in ("motor_action", "actuation_firewall", "action_veto_layer",
                 "embodiment_sandbox_runtime", "consequence_model",
                 "gridworld_actuator", "action_ledger"):
        assert node in g.nodes


def test_state_graph_firewall_edge_exists():
    g = build_default_state_graph()
    pairs = {(s, d) for s, d, _ in g.edges}
    assert ("motor_contract_validator", "actuation_firewall") in pairs
