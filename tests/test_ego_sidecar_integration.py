"""Tests for ego attribution and boundaries around the sidecar."""

from __future__ import annotations

from solaris_ai_nn.ego.boundaries import BoundaryStatus, BoundaryType
from solaris_ai_nn.ego.self_model import SelfModel
from solaris_ai_nn.experiments.solaris_sidecar_observation import (
    FakeConscience,
)
from solaris_ai_nn.integration.conscience_sidecar import SolarisNNSidecar


def test_solaris_observed_action_attributed_external(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    model.update({"run_id": "r1", "sidecar_attached": True})
    c = model.classify_event(
        {"source": "sidecar", "kind": "observed_action",
         "payload": "Solaris_Ai committed Action X"})
    assert c.origin == "external"
    assert c.attribution == "observed_from_solaris_sidecar"
    # Observed Solaris actions are not Solaris-AI-NN actions.
    assert not c.authorized_action
    assert model.perspective.state.mode == "solaris_sidecar_observer"


def test_sidecar_suggestion_remains_suggestion(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    candidate = type("C", (), {"action_type": "sidecar_suggestion",
                               "label": "remain_observe_only",
                               "committed": False, "metadata": {}})()
    result = model.attributor.attribute_action_candidate(candidate)
    assert result.category == "observed_from_solaris_sidecar"
    assert result.is_committed_action is False
    assert any("suggestion" in r for r in result.reasons)


def test_attach_detach_record_boundary_events(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    model.update({"run_id": "r1"})
    sidecar = SolarisNNSidecar(observe_only=True, ego=model)
    sidecar.attach(FakeConscience())
    boundary = model.boundaries.get(BoundaryType.SIDECAR)
    assert boundary.current_status == BoundaryStatus.CROSSED_SAFELY
    assert model.boundaries.crossings_total == 1
    sidecar.detach()
    assert model.boundaries.crossings_total == 2
    narrated = {e.template_id for e in model.narrative.events}
    assert {"sidecar_attached", "sidecar_detached"} <= narrated
    # The compatibility identity is on the record.
    attach_events = [e for e in model.boundaries.events
                     if e.kind == "crossing"]
    assert any("compatibility:" in ref
               for e in attach_events for ref in e.evidence_refs)


def test_sidecar_has_no_action_authority(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    model.update({"run_id": "r1", "sidecar_attached": True})
    assert model.action_authority() == "none"
    assert model.perspective.state.actions_allowed is False
