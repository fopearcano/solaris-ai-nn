"""Alpha <-> Inner MAP + Evaluation integration."""

from __future__ import annotations

import tempfile

import pytest

from solaris_ai_nn.alpha_system import AlphaResearchOrchestrator
from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS
from solaris_ai_nn.inner_map.observer import InnerMapObserver

_NAMES = (
    "alpha_research_system", "alpha_profile_protocol",
    "alpha_module_registry_protocol", "alpha_system_check_protocol",
    "alpha_demo_plan_protocol", "alpha_artifact_index_protocol",
    "alpha_cycle_status_protocol", "alpha_safety",
)


def test_inner_map_includes_alpha_state(tmp_path):
    orch = AlphaResearchOrchestrator(state_dir=str(tmp_path), max_ticks=25)
    orch.run()
    model = InnerMapObserver(alpha_system=orch).update()
    assert model.alpha_system is not None
    assert model.alpha_system["alpha_research_system_enabled"] is True
    assert model.alpha_system["controls_feeders"] is False
    assert "alpha_system" in model.to_dict()


def test_inner_map_warning_when_unavailable():
    # No alpha component attached -> the field stays None (recorded as absent).
    model = InnerMapObserver().update()
    assert model.alpha_system is None


def test_metrics_computed():
    metrics = M.alpha_system_metrics({
        "alpha_module_count": 28, "alpha_available_module_count": 28,
        "alpha_demo_step_count": 15, "alpha_cycle_stage": "demo_completed"})
    assert metrics["present"] is True
    assert metrics["alpha_module_count"] == 28
    assert metrics["controls_feeders"] is False
    assert metrics["is_consciousness_or_personhood"] is False


def test_metrics_absent():
    assert M.alpha_system_metrics(None)["present"] is False


@pytest.mark.parametrize("name", _NAMES)
def test_protocols_return_results(name):
    r = ExperimentRegistry()
    m = r.build_manifest("alpha_research_system",
                         {"state_dir": tempfile.mkdtemp()})
    result = PROTOCOLS[name](m)
    assert result.success, result.error
    assert "alpha_system" in result.metrics


def test_feature_flag_set():
    r = ExperimentRegistry()
    m = r.build_manifest("alpha_research_system")
    assert m.enabled_features.get("alpha_system") is True
