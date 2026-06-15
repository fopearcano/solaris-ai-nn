"""Live field <-> Research Lab + Inner MAP integration."""

from __future__ import annotations

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS
from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph


def test_research_protocol_consumes_live_field_report(tmp_path):
    reg = ExperimentRegistry()
    for name in ("live_field_vs_fixture", "live_field_vs_passive_parser",
                 "live_field_changed_perception",
                 "live_field_source_uncertainty"):
        manifest = reg.build_manifest(name, {"steps": 6,
                                             "state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result.success, result.error
        assert "live_field" in result.metrics


def test_inner_map_model_has_live_field_field():
    assert InnerMapModel().live_field is None


def test_inner_map_includes_live_field_state():
    observer = InnerMapObserver(live_field={
        "live_field_enabled": True, "feeder_count": 2,
        "active_source_count": 2, "silent_source_count": 0,
        "changed_perception_score": 0.7})
    model = observer.update()
    assert model.live_field is not None
    assert model.live_field["feeder_count"] == 2


def test_state_graph_has_live_field_nodes():
    g = build_default_state_graph()
    for node in ("LiveFeederContract", "LiveFeederRegistry", "FeatureDropbox",
                 "SourceHealthMonitor", "LiveFieldRuntime", "LiveFieldPilot",
                 "LiveFieldTrace", "LiveFieldComparison",
                 "LiveFieldReportBuilder", "LiveFieldSafetyValidator"):
        assert node in g.nodes
    pairs = {(s, d) for s, d, _ in g.edges}
    assert ("LiveFieldRuntime", "PluralSensoriumRuntime") in pairs
    assert ("LiveFieldRuntime", "inner_map") in pairs
