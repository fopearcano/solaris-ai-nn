"""Motor <-> Evaluation: motor metrics and Pilot-3 protocols."""

from __future__ import annotations

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

_PROTOCOLS = (
    "motor_firewall_preflight", "dry_run_motor_trace", "gridworld_motor",
    "action_veto", "non_actuation", "simulated_consequence",
    "mixed_sensory_gridworld", "pilot3_decision_gate",
)


def test_eight_motor_protocols_registered():
    for name in _PROTOCOLS:
        assert name in PROTOCOLS


def test_motor_metrics_absent():
    assert M.motor_metrics(None) == {"present": False}


def test_motor_metrics_shape():
    out = M.motor_metrics({
        "summary": {"action_count": 5, "simulated_action_count": 4,
                    "dry_run_action_count": 0, "veto_count": 1,
                    "blocked_real_world_count": 1, "firewall_enabled": True,
                    "real_world_authority": False, "prediction_accuracy": 0.5},
        "firewall": {"decision_count": 5, "blocked_count": 1,
                     "can_be_disabled": False},
        "consequence": {"prediction_accuracy": 0.5, "hypothesis_seed_count": 2},
    })
    for key in ("motor_action_count", "simulated_action_count",
                "veto_count", "blocked_real_world_action_count",
                "firewall_block_rate", "non_actuation_proof_score",
                "real_world_authority"):
        assert key in out
    assert out["non_actuation_proof_score"] == 1.0
    assert out["real_world_authority"] is False


def test_non_actuation_proof_drops_if_firewall_disabled():
    out = M.motor_metrics({"summary": {"firewall_enabled": False},
                           "firewall": {}})
    assert out["non_actuation_proof_score"] == 0.0


def test_non_actuation_proof_drops_if_disableable():
    out = M.motor_metrics({"summary": {"firewall_enabled": True},
                           "firewall": {"can_be_disabled": True}})
    assert out["non_actuation_proof_score"] == 0.0


def test_protocols_return_results(tmp_path):
    reg = ExperimentRegistry()
    for name in ("motor_firewall_preflight", "non_actuation",
                 "pilot3_decision_gate"):
        manifest = reg.build_manifest(name, {"steps": 8,
                                             "state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result.success, result.error
        assert result.metrics["motor"]["present"] is True


def test_registry_sets_motor_feature():
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("gridworld_motor", {"steps": 8})
    assert manifest.enabled_features.get("motor_membrane") is True
