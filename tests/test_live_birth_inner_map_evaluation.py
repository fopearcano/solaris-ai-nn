"""Live birth <-> Inner MAP + Evaluation integration."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.live_birth import (
    LiveReadOnlyBirthRuntime,
    approved_governance,
    feeder_registry_template,
)

_NAMES = (
    "live_birth", "live_governance_protocol", "live_feeder_registry_protocol",
    "live_event_schema_protocol", "live_event_validation_protocol",
    "live_quarantine_protocol", "live_membrane_activation_protocol",
    "birth_certificate_protocol", "live_birth_safety",
)


def _runtime(tmp_path):
    state = str(tmp_path)
    rt = LiveReadOnlyBirthRuntime(state_dir=state, require_governance=True)
    rt.initialize()
    with open(os.path.join(state, "governance",
                           "LIVE_READONLY_GOVERNANCE.json"), "w") as fh:
        json.dump(approved_governance(), fh)
    with open(os.path.join(state, "feeders", "FEEDER_REGISTRY.json"), "w") as fh:
        json.dump(feeder_registry_template(), fh)
    rt.run()
    return rt


def test_inner_map_includes_live_birth_state(tmp_path):
    rt = _runtime(tmp_path)
    model = InnerMapObserver(live_birth=rt).update()
    assert model.live_birth is not None
    assert model.live_birth["live_birth_enabled"] is True
    assert model.live_birth["starts_feeders"] is False
    assert "live_birth" in model.to_dict()


def test_inner_map_warning_when_unavailable():
    model = InnerMapObserver().update()
    assert model.live_birth is None


def test_metrics_computed():
    metrics = M.live_birth_metrics({
        "governance_passed": True, "live_feeder_count": 6,
        "live_event_accepted_count": 6, "live_event_quarantined_count": 5,
        "membrane_activation_status": "activated",
        "latest_birth_certificate_path": "/x/BIRTH_CERTIFICATE_run.md"})
    assert metrics["present"] is True
    assert metrics["live_birth_governance_pass_count"] == 1
    assert metrics["live_event_accepted_count"] == 6
    assert metrics["birth_certificate_count"] == 1
    assert metrics["is_consciousness_or_personhood"] is False


def test_metrics_absent():
    assert M.live_birth_metrics(None)["present"] is False


@pytest.mark.parametrize("name", _NAMES)
def test_protocols_return_results(name):
    r = ExperimentRegistry()
    m = r.build_manifest("live_birth", {"state_dir": tempfile.mkdtemp()})
    result = PROTOCOLS[name](m)
    assert result.success, result.error
    assert "live_birth" in result.metrics


def test_feature_flag_set():
    r = ExperimentRegistry()
    m = r.build_manifest("live_birth")
    assert m.enabled_features.get("live_birth") is True
