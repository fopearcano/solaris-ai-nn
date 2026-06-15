"""Cognition evaluation: metrics computed; protocols return results."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.evaluation.benchmark import ExperimentManifest
from solaris_ai_nn.evaluation.metrics import sensorium_cognition_metrics
from solaris_ai_nn.evaluation.protocols import PROTOCOLS
from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.semiogenesis import SemiogenesisRuntime
from solaris_ai_nn.sensorium_cognition import SensoriumCognitionRuntime


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
    sem = SemiogenesisRuntime(state_dir=str(tmp_path / "s"), ontogenesis=ont,
                              max_ticks=5)
    sem.run_bounded()
    cog = SensoriumCognitionRuntime(state_dir=str(tmp_path / "c"),
                                    semiogenesis=sem, ontogenesis=ont,
                                    max_ticks=4)
    cog.run_bounded()
    return cog.cognition_status()


def test_metrics_absent_when_no_status():
    assert sensorium_cognition_metrics(None) == {"present": False}


def test_metrics_computed(tmp_path):
    m = sensorium_cognition_metrics(_status(tmp_path))
    assert m["present"] is True
    assert m["cognitive_move_count"] >= 0
    assert 0.0 <= m["prediction_success_rate"] <= 1.0
    assert m["is_human_language_reasoning"] is False
    assert m["simulation_is_observation"] is False


def test_protocols_return_results(tmp_path):
    for name in ("sensorium_cognition", "prediction", "anticipation_evaluation",
                 "question_pressure", "internal_simulation", "analogy",
                 "synthesis", "sensorium_cognition_safety"):
        manifest = ExperimentManifest(
            name=name, state_dir=str(tmp_path / name), max_steps=5)
        result = PROTOCOLS[name](manifest)
        assert result.success, f"{name}: {result.error}"
        assert "sensorium_cognition" in result.metrics


def test_safety_protocol_reports_blocks(tmp_path):
    manifest = ExperimentManifest(
        name="cog_safety", state_dir=str(tmp_path / "safety"), max_steps=5)
    result = PROTOCOLS["sensorium_cognition_safety"](manifest)
    cog = result.metrics["sensorium_cognition"]
    assert cog["llm_cognition_blocked"] is True
    assert cog["human_default_blocked"] is True
    assert cog["simulated_as_real_blocked"] is True
    assert cog["understanding_claim_blocked"] is True
    assert cog["can_use_llm"] is False
    assert cog["can_delete_failed_predictions"] is False


def test_simulation_protocol_marks_non_real(tmp_path):
    manifest = ExperimentManifest(
        name="internal_simulation", state_dir=str(tmp_path / "sim"),
        max_steps=5)
    result = PROTOCOLS["internal_simulation"](manifest)
    assert result.metrics["sensorium_cognition"]["any_marked_real"] is False
