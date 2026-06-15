"""Semiogenesis: research protocols exist; Sensorium Lab includes sign metrics."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.evaluation.protocols import PROTOCOLS
from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.semiogenesis import SemiogenesisRuntime
from solaris_ai_nn.sensorium_lab.world_signature import WorldSignatureBuilder


def _setup(tmp_path, modalities=("alien_rf", "alien_echo", "alien_vibration")):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    for mod in modalities:
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
    return rt, ont, sem


def test_research_protocols_exist():
    for name in ("semiogenesis", "sign_birth", "sign_utility",
                 "private_syntax", "sign_drift", "sign_contamination",
                 "semiogenesis_safety"):
        assert name in PROTOCOLS
        assert callable(PROTOCOLS[name])


def test_sensorium_lab_includes_sign_metrics(tmp_path):
    rt, ont, sem = _setup(tmp_path)
    sig = WorldSignatureBuilder().build("arm", "fixture", rt, ontogenesis=ont,
                                        semiogenesis=sem)
    data = sig.to_dict()
    assert data["sign_family_distribution"]
    assert "modality_native_sign_ratio" in data
    assert "cross_modal_sign_ratio" in data
    assert "absence_sign_ratio" in data
    assert "contaminated_sign_ratio" in data
    assert "private_syntax_density" in data
    assert "gloss_dependence_score" in data


def test_world_signature_works_without_semiogenesis(tmp_path):
    rt, _, _ = _setup(tmp_path)
    sig = WorldSignatureBuilder().build("arm", "fixture", rt)
    assert sig.sign_family_distribution == {}
