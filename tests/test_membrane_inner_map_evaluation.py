"""Membrane Inner MAP + Evaluation integration."""

from __future__ import annotations

import json
import os
import shutil

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FIXTURES = os.path.join(_ROOT, "examples", "environmental_membrane")


def _run(tmp_path):
    from solaris_ai_nn.live_birth import (
        approved_governance, feeder_registry_template)
    from solaris_ai_nn.environmental_membrane import EnvironmentalMembraneRuntime

    state = str(tmp_path)
    for sub in ("governance", "feeders", "inbox"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    shutil.copy(os.path.join(_FIXTURES, "sample_validated_events.jsonl"),
                os.path.join(state, "inbox", "events.jsonl"))
    rt = EnvironmentalMembraneRuntime(state_dir=state, require_governance=True)
    rt.run()
    return rt


def test_inner_map_observer_attaches_membrane(tmp_path):
    from solaris_ai_nn.inner_map.observer import InnerMapObserver

    rt = _run(tmp_path)
    model = InnerMapObserver(environmental_membrane=rt).update()
    assert model.environmental_membrane is not None
    assert model.environmental_membrane["membrane_enabled"] is True


def test_inner_map_warning_when_unavailable():
    from solaris_ai_nn.inner_map.observer import InnerMapObserver

    model = InnerMapObserver().update()
    assert model.environmental_membrane is None


def test_evaluation_metrics_computed(tmp_path):
    from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
    from solaris_ai_nn.evaluation.protocols import PROTOCOLS

    reg = ExperimentRegistry()
    m = reg.build_manifest("environmental_membrane",
                           {"state_dir": str(tmp_path / "eval")})
    assert m.enabled_features.get("environmental_membrane") is True
    res = PROTOCOLS["environmental_membrane"](m)
    mm = res.metrics["environmental_membrane"]
    assert mm["present"] is True
    assert mm["membrane_receptor_count"] == 11
    assert mm["starts_feeders"] is False


def test_evaluation_metrics_empty():
    from solaris_ai_nn.evaluation.metrics import environmental_membrane_metrics

    assert environmental_membrane_metrics(None) == {"present": False}
