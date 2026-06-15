"""Ontogenesis evaluation: metrics computed; protocols return results."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.evaluation.benchmark import ExperimentManifest
from solaris_ai_nn.evaluation.metrics import perceptual_ontogenesis_metrics
from solaris_ai_nn.evaluation.protocols import PROTOCOLS
from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


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
    ont = PerceptualOntogenesisRuntime(state_dir=str(tmp_path / "o"),
                                       sensorium=rt, max_ticks=6)
    ont.run_bounded()
    return ont.ontogenesis_status()


def test_metrics_absent_when_no_status():
    assert perceptual_ontogenesis_metrics(None) == {"present": False}


def test_metrics_computed(tmp_path):
    m = perceptual_ontogenesis_metrics(_status(tmp_path))
    assert m["present"] is True
    assert m["perceptual_atom_count"] >= 0
    assert m["proto_concept_candidate_count"] >= 0
    assert 0.0 <= m["world_formation_density"] <= 1.0
    # Hard honesty flags.
    assert m["proto_concepts_are_words"] is False
    assert m["world_formation_is_subjective"] is False


def test_protocols_return_results(tmp_path):
    for name in ("perceptual_ontogenesis", "proto_concept_birth",
                 "concept_stabilization", "concept_decay",
                 "concept_contamination", "world_formation",
                 "perceptual_ontogenesis_safety"):
        manifest = ExperimentManifest(
            name=name, state_dir=str(tmp_path / name), max_steps=5)
        result = PROTOCOLS[name](manifest)
        assert result.success, f"{name}: {result.error}"
        assert "perceptual_ontogenesis" in result.metrics


def test_safety_protocol_reports_blocks(tmp_path):
    manifest = ExperimentManifest(
        name="po_safety", state_dir=str(tmp_path / "safety"), max_steps=5)
    result = PROTOCOLS["perceptual_ontogenesis_safety"](manifest)
    po = result.metrics["perceptual_ontogenesis"]
    assert po["hardware_blocked"] is True
    assert po["feeder_control_blocked"] is True
    assert po["label_ground_truth_blocked"] is True
    assert po["subjective_claim_blocked"] is True
    assert po["can_actuate"] is False
    assert po["can_delete_concepts"] is False
