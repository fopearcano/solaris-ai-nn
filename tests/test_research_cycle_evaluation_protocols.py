"""Research cycle evaluation protocols are registered and run safely."""

from __future__ import annotations

import tempfile

import pytest

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

_NAMES = (
    "research_cycle", "research_cycle_protocol", "research_cycle_evaluation",
    "cycle_manifest_protocol", "cycle_state_protocol", "decision_gate_protocol",
    "evidence_ledger_protocol", "artifact_graph_protocol",
    "operator_decision_protocol", "cycle_transition_protocol",
    "blocked_state_protocol", "next_action_protocol", "research_cycle_safety",
)


def test_protocols_registered():
    for name in _NAMES:
        assert name in PROTOCOLS


@pytest.mark.parametrize("name", _NAMES)
def test_protocol_runs(name):
    r = ExperimentRegistry()
    m = r.build_manifest("research_cycle", {"state_dir": tempfile.mkdtemp()})
    result = PROTOCOLS[name](m)
    assert result is not None


def test_feature_flag_set():
    r = ExperimentRegistry()
    m = r.build_manifest("research_cycle")
    assert m.enabled_features.get("research_cycle") is True


def test_state_protocol_reports_not_self_approved():
    r = ExperimentRegistry()
    m = r.build_manifest("research_cycle", {"state_dir": tempfile.mkdtemp()})
    result = PROTOCOLS["cycle_state_protocol"](m)
    rc = result.metrics["research_cycle"]
    assert rc["self_approved"] is False
