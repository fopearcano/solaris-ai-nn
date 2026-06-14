"""Inner MAP integration: conscience field, observer wiring, state graph."""

from __future__ import annotations

from solaris_ai_nn.conscience import (
    ConscienceOrchestrator,
    RunContext,
    RunMode,
)
from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph

_CONSCIENCE_NODES = (
    "conscience_orchestrator", "conscience_spine", "conscience_bus",
    "module_registry", "module_lifecycle_manager", "conscience_scheduler",
    "scenario_runner", "scenario_profile", "integration_health_monitor",
    "snapshot_builder", "full_system_report_builder",
)


def test_model_has_conscience_field():
    assert hasattr(InnerMapModel(), "conscience")
    assert InnerMapModel().conscience is None


def test_state_graph_has_eleven_conscience_nodes():
    g = build_default_state_graph()
    for node in _CONSCIENCE_NODES:
        assert node in g.nodes, node


def test_state_graph_links_conscience_to_inner_map():
    g = build_default_state_graph()
    edges = {(e["src"] if isinstance(e, dict) else e[0],
              e["dst"] if isinstance(e, dict) else e[1])
             for e in g.to_dict()["edges"]}
    assert ("conscience_orchestrator", "inner_map") in edges


def test_observer_reports_conscience_summary(tmp_path):
    orch = ConscienceOrchestrator()
    orch.configure(RunContext(
        mode=RunMode.SHORT_DEMO, state_dir=str(tmp_path), max_steps=10,
        enabled_modules=["bridge", "ecology", "governance"]))
    orch.initialize()
    for _ in range(5):
        orch.step()
    observer = InnerMapObserver(conscience=orch)
    model = observer.update()
    assert model.conscience is not None
    assert "no module is sovereign" in model.conscience["authority_note"]
