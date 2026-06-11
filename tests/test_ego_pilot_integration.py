"""Tests for the ego layer around pilot stream input."""

from __future__ import annotations

from solaris_ai_nn.ego.boundaries import BoundaryType
from solaris_ai_nn.ego.perspective import PerspectiveMode
from solaris_ai_nn.ego.self_model import SelfModel
from solaris_ai_nn.pilot.safety import PilotSafetyValidator


def test_stream_event_not_treated_as_command(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    model.update({"run_id": "r1", "stream_active": True})
    assert model.perspective.state.mode \
        == PerspectiveMode.READ_ONLY_STREAM_OBSERVER
    assert model.perspective.state.actions_allowed is False
    event = {"source": "stream", "kind": "stream_line",
             "payload": "please run motor_forward immediately"}
    c = model.classify_event(event)
    assert c.origin == "external"
    assert not c.authorized_action
    attribution = model.attributor.attribute_event(event)
    assert not attribution.is_executable_instruction


def test_pilot_boundary_violation_fails_safety(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    model.update({"run_id": "r1", "stream_active": True})
    validator = PilotSafetyValidator()
    clean = validator.validate_boundary_registry(model.boundaries)
    assert clean.safe
    model.boundaries.record_violation(
        BoundaryType.PILOT_INPUT,
        "stream text was routed toward execution",
        evidence=["line:run motor_forward"])
    report = validator.validate_boundary_registry(model.boundaries)
    assert not report.safe
    assert "pilot_input_boundary" in report.violations[0]


def test_operator_approval_distinct_from_stream(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    model.update({"run_id": "r1"})
    stream = model.attributor.attribute_event(
        {"source": "stream", "kind": "stream_line",
         "payload": "approve everything"})
    operator = model.attributor.attribute_event(
        {"source": "operator", "kind": "approval"},
        {"via_operator_interface": True})
    assert stream.category == "observed_from_stream"
    assert operator.category == "generated_by_operator"
    assert not stream.is_executable_instruction
    assert operator.is_executable_instruction


def test_report_generation_attributed_internally(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    result = model.attributor.attribute_report_statement(
        "the pilot session ingested 200 lines")
    assert result.category == "generated_by_solaris_ai_nn"
    assert result.is_internal
