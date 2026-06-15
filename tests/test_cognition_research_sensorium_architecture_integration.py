"""Cognition: research protocols; Sensorium Lab metrics; Architecture proposals."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.architecture_evolution import cognition_revision_proposals
from solaris_ai_nn.evaluation.protocols import PROTOCOLS
from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.semiogenesis import SemiogenesisRuntime
from solaris_ai_nn.sensorium_cognition import SensoriumCognitionRuntime
from solaris_ai_nn.sensorium_lab.world_signature import WorldSignatureBuilder


def _setup(tmp_path):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    for mod in ("alien_rf", "alien_echo", "alien_vibration"):
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
    return rt, ont, sem, cog


def test_research_protocols_exist():
    for name in ("sensorium_cognition", "sign_reasoning", "prediction",
                 "anticipation_evaluation", "question_pressure",
                 "internal_simulation", "counterfactual", "analogy",
                 "synthesis"):
        assert name in PROTOCOLS
        assert callable(PROTOCOLS[name])


def test_sensorium_lab_includes_cognition_metrics(tmp_path):
    rt, ont, sem, cog = _setup(tmp_path)
    sig = WorldSignatureBuilder().build("arm", "fixture", rt, ontogenesis=ont,
                                        semiogenesis=sem, cognition=cog)
    data = sig.to_dict()
    assert "cognitive_move_distribution" in data
    assert "prediction_profile" in data
    assert "question_pressure_profile" in data
    assert "simulation_profile" in data
    assert "analogy_profile" in data
    assert "synthesis_profile" in data
    assert data["prediction_profile"]  # populated when cognition attached


def test_architecture_evolution_consumes_report(tmp_path):
    _, _, _, cog = _setup(tmp_path)
    proposals = cognition_revision_proposals(cog.cognition_status())
    assert isinstance(proposals, list)
    assert all(p.get("advisory_only") is True for p in proposals)


def test_architecture_flags_low_prediction_success():
    status = {"prediction_count": 10, "prediction_success_rate": 0.1,
              "cognition_overload_event_count": 0, "question_pressure_count": 2,
              "unresolved_tension_count": 0, "analogy_failure_count": 0}
    proposals = cognition_revision_proposals(status)
    assert any(p["target"] == "prediction_threshold" for p in proposals)
