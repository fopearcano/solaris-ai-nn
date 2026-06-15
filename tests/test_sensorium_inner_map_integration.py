"""Plural sensorium <-> Inner MAP: model field + state-graph nodes/edges."""

from __future__ import annotations

from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph


def test_model_has_plural_sensorium_field():
    assert InnerMapModel().plural_sensorium is None


def test_observer_populates_plural_sensorium():
    observer = InnerMapObserver(plural_sensorium={
        "plural_sensorium_enabled": True,
        "active_modality_count": 3, "active_receptor_count": 4,
        "cross_modal_relation_count": 2,
        "human_label_contamination_score": 0.0})
    model = observer.update()
    assert model.plural_sensorium is not None
    assert model.plural_sensorium["active_modality_count"] == 3
    assert model.plural_sensorium["human_label_contamination_score"] == 0.0


def test_state_graph_has_sensorium_nodes():
    g = build_default_state_graph()
    for node in ("PluralSensoriumRuntime", "SensoriumModality",
                 "SensoryEventEnvelope", "ExternalFeederDescriptor", "Receptor",
                 "SensoryField", "PerceptualBaseline", "FluxDetector",
                 "AbsenceDetector", "RhythmDetector", "InvariantDetector",
                 "CrossModalDetector", "SensoriumAttentionPolicy",
                 "SensoriumGroundingAnalyzer",
                 "PluralSensoriumSafetyValidator"):
        assert node in g.nodes


def test_state_graph_sensorium_edges():
    g = build_default_state_graph()
    pairs = {(s, d) for s, d, _ in g.edges}
    assert ("ExternalFeederDescriptor", "SensoryEventEnvelope") in pairs
    assert ("SensoryEventEnvelope", "Receptor") in pairs
    assert ("Receptor", "SensoryField") in pairs
    assert ("PluralSensoriumRuntime", "inner_map") in pairs
