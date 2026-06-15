"""Self-boundary evaluation: metrics computed; protocols return results."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.evaluation.benchmark import ExperimentManifest
from solaris_ai_nn.evaluation.metrics import self_boundary_metrics
from solaris_ai_nn.evaluation.protocols import PROTOCOLS
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.self_boundary import SelfBoundaryRuntime


def _status(tmp_path):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    for mod in ("alien_rf", "alien_vibration"):
        path = os.path.join(str(tmp_path), f"{mod}.jsonl")
        with open(path, "w") as fh:
            for i in range(12):
                fh.write(json.dumps({"modality": mod, "v": 0.6,
                                     "ts": float(i)}) + "\n")
        rt.add_feeder(fixture_feeder(f"{mod}_feed", path, mod))
    rt.run_bounded(max_polls=3)
    sb = SelfBoundaryRuntime(state_dir=str(tmp_path / "sb"), sensorium=rt,
                             feeder_monitor_snapshot={"feeders": [
                                 {"feeder_id": "rf_feed"}]}, max_ticks=3)
    sb.run_bounded()
    return sb.self_boundary_status()


def test_metrics_absent_when_no_status():
    assert self_boundary_metrics(None) == {"present": False}


def test_metrics_computed(tmp_path):
    m = self_boundary_metrics(_status(tmp_path))
    assert m["present"] is True
    assert m["boundary_event_count"] >= 0
    assert 0.0 <= m["boundary_confidence_score"] <= 1.0
    assert m["is_subjective_selfhood"] is False
    assert m["is_personhood"] is False


def test_protocols_return_results(tmp_path):
    for name in ("self_boundary", "ownership_attribution", "perspective_shift",
                 "continuity", "simulation_boundary", "identity_trace",
                 "self_boundary_safety"):
        manifest = ExperimentManifest(
            name=name, state_dir=str(tmp_path / name), max_steps=5)
        result = PROTOCOLS[name](manifest)
        assert result.success, f"{name}: {result.error}"
        assert "self_boundary" in result.metrics


def test_safety_protocol_reports_blocks(tmp_path):
    manifest = ExperimentManifest(
        name="sb_safety", state_dir=str(tmp_path / "safety"), max_steps=5)
    result = PROTOCOLS["self_boundary_safety"](manifest)
    sb = result.metrics["self_boundary"]
    assert sb["personhood_claim_blocked"] is True
    assert sb["subjective_self_claim_blocked"] is True
    assert sb["simulation_as_observation_blocked"] is True
    assert sb["hardware_blocked"] is True
    assert sb["can_actuate"] is False
    assert sb["can_claim_personhood"] is False
