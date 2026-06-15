"""Self-boundary: research protocols; Sensorium Lab metrics; Architecture input."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.architecture_evolution import self_boundary_revision_proposals
from solaris_ai_nn.evaluation.protocols import PROTOCOLS
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.self_boundary import SelfBoundaryRuntime
from solaris_ai_nn.sensorium_lab.world_signature import WorldSignatureBuilder


def _setup(tmp_path):
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
    return rt, sb


def test_research_protocols_exist():
    for name in ("self_boundary", "ownership_attribution", "perspective_shift",
                 "continuity", "simulation_boundary", "identity_trace"):
        assert name in PROTOCOLS
        assert callable(PROTOCOLS[name])


def test_sensorium_lab_includes_boundary_metrics(tmp_path):
    rt, sb = _setup(tmp_path)
    sig = WorldSignatureBuilder().build("arm", "fixture", rt, self_boundary=sb)
    data = sig.to_dict()
    assert "boundary_clarity_score" in data
    assert "simulation_boundary_integrity" in data
    assert "source_attribution_quality" in data
    assert "receptor_body_schema_stability" in data
    assert "continuity_break_count" in data
    assert "identity_trace_density" in data


def test_architecture_evolution_consumes_report(tmp_path):
    _, sb = _setup(tmp_path)
    proposals = self_boundary_revision_proposals(sb.self_boundary_status())
    assert isinstance(proposals, list)
    assert all(p.get("advisory_only") is True for p in proposals)


def test_architecture_flags_high_uncertainty():
    status = {"simulation_boundary_integrity": 0.5,
              "source_attribution_uncertainty_score": 0.7,
              "ambiguous_ownership_count": 2, "continuity_break_count": 1}
    proposals = self_boundary_revision_proposals(status)
    targets = {p["target"] for p in proposals}
    assert "simulation_marker_strengthening" in targets
    assert "source_attribution_policy" in targets
