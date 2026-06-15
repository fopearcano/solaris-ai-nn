"""Semiogenesis evaluation: metrics computed; protocols return results."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.evaluation.benchmark import ExperimentManifest
from solaris_ai_nn.evaluation.metrics import semiogenesis_metrics
from solaris_ai_nn.evaluation.protocols import PROTOCOLS
from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.semiogenesis import SemiogenesisRuntime


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
    return sem.semiogenesis_status()


def test_metrics_absent_when_no_status():
    assert semiogenesis_metrics(None) == {"present": False}


def test_metrics_computed(tmp_path):
    m = semiogenesis_metrics(_status(tmp_path))
    assert m["present"] is True
    assert m["internal_sign_count"] >= 0
    assert 0.0 <= m["modality_native_sign_ratio"] <= 1.0
    assert m["signs_are_words"] is False
    assert m["private_syntax_is_human_grammar"] is False


def test_protocols_return_results(tmp_path):
    for name in ("semiogenesis", "sign_birth", "sign_utility",
                 "private_syntax", "sign_drift", "sign_contamination",
                 "semiogenesis_safety"):
        manifest = ExperimentManifest(
            name=name, state_dir=str(tmp_path / name), max_steps=5)
        result = PROTOCOLS[name](manifest)
        assert result.success, f"{name}: {result.error}"
        assert "semiogenesis" in result.metrics


def test_safety_protocol_reports_blocks(tmp_path):
    manifest = ExperimentManifest(
        name="sg_safety", state_dir=str(tmp_path / "safety"), max_steps=5)
    result = PROTOCOLS["semiogenesis_safety"](manifest)
    sg = result.metrics["semiogenesis"]
    assert sg["llm_generation_blocked"] is True
    assert sg["human_default_blocked"] is True
    assert sg["gloss_ground_truth_blocked"] is True
    assert sg["language_understanding_claim_blocked"] is True
    assert sg["can_use_llm"] is False
    assert sg["can_delete_signs"] is False
