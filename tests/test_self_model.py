"""Tests for the SelfModel aggregate."""

from __future__ import annotations

from solaris_ai_nn.ego.self_model import SelfModel, SelfModelObserver


def _model(tmp_path):
    return SelfModel(state_dir=tmp_path)


def test_self_model_updates_from_context(tmp_path):
    model = _model(tmp_path)
    snapshot = model.update({
        "run_id": "r1", "session_id": "s1", "substrate_identity": "esn",
        "state_path": str(tmp_path), "health_level": "ok", "step": 5,
        "executive": {"mode": "arbitrated"}})
    assert snapshot.identity["continuity_score"] == 1.0
    assert snapshot.perspective["current"]["mode"] == "internal_runtime"
    assert snapshot.operational_status["health_level"] == "ok"
    assert "executive" in snapshot.module_summaries
    assert model.updates == 1
    # Persistence works.
    paths = model.save_state()
    assert (tmp_path / "self_model.json").exists()
    assert (tmp_path / "ego_boundaries.json").exists()
    assert paths["self_model"].endswith("self_model.json")


def test_classifies_internal_event(tmp_path):
    model = _model(tmp_path)
    model.update({"run_id": "r1"})
    c = model.classify_event({"source": "homeostasis",
                              "kind": "desire_candidate", "label": "rest"})
    assert c.origin == "internal"
    assert c.attribution == "generated_by_solaris_ai_nn"
    assert c.suggestion is True  # a desire candidate stays a suggestion
    assert model.is_internal({"source": "substrate", "kind": "state"})
    assert (tmp_path / "dimensional_frames.jsonl").exists()


def test_classifies_external_event(tmp_path):
    model = _model(tmp_path)
    model.update({"run_id": "r1"})
    c = model.classify_event({"source": "stream", "kind": "stream_line",
                              "payload": "external text"})
    assert c.origin == "external"
    assert c.attribution == "observed_from_stream"
    assert not c.authorized_action
    assert model.is_external({"source": "operator", "kind": "approval"})


def test_uncertain_classification_reported(tmp_path):
    model = _model(tmp_path)
    model.update({"run_id": "r1"})
    c = model.classify_event({"kind": "mystery_blob"})
    assert c.origin == "unknown"
    assert c.attribution == "unknown_source"
    assert c.confidence <= 0.4
    assert any("uncertain" in r or "low confidence" in r
               for r in c.reasons)
    assert model.classification_counts["unknown"] == 1


def test_predicates_cover_offline_suggestion_authority(tmp_path):
    model = _model(tmp_path)
    model.update({"run_id": "r1"})
    assert model.is_offline({"source": "offline_replay",
                             "kind": "replay_trace"})
    assert model.is_simulated({"source": "counterfactual",
                               "kind": "dream"})
    assert model.is_suggestion({"source": "executive",
                                "kind": "suggestion",
                                "label": "rest"})
    # Real-world shapes are never authorized, anywhere.
    assert not model.is_authorized_action({"source": "executive",
                                           "kind": "action",
                                           "label": "motor_forward"})


def test_self_model_never_executes_or_overrides(tmp_path):
    model = _model(tmp_path)
    assert model.safety.can_execute_actions() is False
    assert model.safety.can_override_governance() is False
    assert model.safety.can_grant_permissions() is False
    # No execution surface exists at all.
    for name in ("execute", "act", "commit", "grant"):
        assert not hasattr(model, name)


def test_observer_pulls_runner_summaries(tmp_path):
    class FakeLifecycle:
        run_id = "run-x"
        session_id = "sess-x"

    class FakeRunner:
        lifecycle = FakeLifecycle()
        bridge = None
        pm = None
        homeostasis = None
        executive = None
        latent = None
        world_model = None

    model = _model(tmp_path)
    observer = SelfModelObserver(self_model=model, runner=FakeRunner())
    snapshot = observer.observe({"health_level": "ok"})
    assert snapshot.identity["anchor_count"] >= 2  # run_id + session_id
    assert model.identity.anchors["run_id"].value == "run-x"
