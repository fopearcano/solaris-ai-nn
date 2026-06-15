"""Sensorium lab <-> Operator console + Inner MAP integration."""

from __future__ import annotations

from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph


def test_inner_map_model_has_sensorium_lab_field():
    assert InnerMapModel().sensorium_lab is None


def test_inner_map_includes_world_signatures():
    observer = InnerMapObserver(sensorium_lab={
        "sensorium_lab_enabled": True, "latest_study_id": "SSD_1",
        "world_signature_count": 9, "modality_fingerprint_count": 12,
        "strongest_structural_difference": "passive vs adaptive: strong",
        "human_label_contamination_score": 0.0})
    model = observer.update()
    assert model.sensorium_lab is not None
    assert model.sensorium_lab["world_signature_count"] == 9


def test_state_graph_has_sensorium_lab_nodes():
    g = build_default_state_graph()
    for node in ("SensoriumStudyDesign", "SensoriumProfile",
                 "SensoriumWorldSignature", "OntologyDriftDetector",
                 "SensoriumStructureMetrics", "SensoriumDifferentiationRunner",
                 "SensoriumComparison", "HumanLabelContaminationAnalyzer",
                 "ModalityFingerprintBuilder",
                 "SensoriumDifferentiationStudyReportBuilder"):
        assert node in g.nodes
    pairs = {(s, d) for s, d, _ in g.edges}
    assert ("SensoriumDifferentiationRunner", "PluralSensoriumRuntime") in pairs
    assert ("SensoriumDifferentiationRunner", "inner_map") in pairs


def test_operator_console_query_is_not_a_consciousness_test():
    from solaris_ai_nn.communication.input_classifier import (
        OperatorInputClassifier,
    )
    from solaris_ai_nn.communication.query_router import QueryRouter

    cls = OperatorInputClassifier().classify("was this a consciousness test?")
    resp = QueryRouter(components={}).route_query(cls)
    assert cls.args["topic"] == "sl_consciousness"
    assert "does not measure or prove consciousness" in resp.text.lower()
