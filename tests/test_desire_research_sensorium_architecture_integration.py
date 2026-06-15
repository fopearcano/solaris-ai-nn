"""Desire: research protocols; Sensorium Lab metrics; Architecture input."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.architecture_evolution import desire_revision_proposals
from solaris_ai_nn.desire_formation import DesireFormationRuntime
from solaris_ai_nn.evaluation.protocols import PROTOCOLS
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.sensorium_lab.world_signature import WorldSignatureBuilder


def _setup(tmp_path):
    ps = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    p = os.path.join(str(tmp_path), "rf.jsonl")
    with open(p, "w") as fh:
        for i in range(10):
            fh.write(json.dumps({"modality": "alien_rf", "power": 0.6,
                                 "ts": float(i)}) + "\n")
    ps.add_feeder(fixture_feeder("rf_feed", p, "alien_rf"))
    ps.run_bounded(max_polls=1)
    rt = DesireFormationRuntime(
        state_dir=str(tmp_path / "d"),
        metabolism={"deprivation_state": True, "novelty_appetite_pressure": 0.7},
        cognition={"failed_prediction_count": 2}, max_ticks=2)
    rt.run_bounded()
    return ps, rt


def test_research_protocols_exist():
    for name in ("desire_formation", "valence_assessment", "push_formation",
                 "desire_arbitration", "internal_action_readiness",
                 "desire_outcome", "desire_safety"):
        assert name in PROTOCOLS
        assert callable(PROTOCOLS[name])


def test_sensorium_lab_includes_desire_metrics(tmp_path):
    ps, rt = _setup(tmp_path)
    sig = WorldSignatureBuilder().build("arm", "fixture", ps,
                                        desire_formation=rt)
    data = sig.to_dict()
    assert "valence_profile" in data
    assert "push_profile" in data
    assert "desire_kind_distribution" in data
    assert "internal_action_profile" in data
    assert "no_op_profile" in data
    assert "conflict_profile" in data


def test_architecture_evolution_consumes_report(tmp_path):
    _, rt = _setup(tmp_path)
    proposals = desire_revision_proposals(rt.desire_status())
    assert isinstance(proposals, list)
    assert all(p.get("advisory_only") is True for p in proposals)


def test_architecture_flags_safety_blocks():
    status = {"desire_candidate_count": 5, "inhibited_desire_count": 1,
              "safety_blocked_desire_count": 2, "desire_conflict_count": 0,
              "no_op_count": 1}
    proposals = desire_revision_proposals(status)
    assert any(p["target"] == "safety_gate_improvements" for p in proposals)
