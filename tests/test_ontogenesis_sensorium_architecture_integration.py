"""Ontogenesis: Sensorium Lab world signature + Architecture Evolution input."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.architecture_evolution import ontogenesis_revision_proposals
from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
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
    return rt, ont


def test_sensorium_lab_includes_concept_family_distribution(tmp_path):
    rt, ont = _setup(tmp_path)
    sig = WorldSignatureBuilder().build("arm", "fixture", rt, ontogenesis=ont)
    data = sig.to_dict()
    assert data["concept_family_distribution"]
    assert "concept_stability_profile" in data
    assert "modality_native_concept_ratio" in data


def test_world_signature_works_without_ontogenesis(tmp_path):
    rt, _ = _setup(tmp_path)
    sig = WorldSignatureBuilder().build("arm", "fixture", rt)
    assert sig.concept_family_distribution == {}


def test_architecture_evolution_receives_report_input(tmp_path):
    _, ont = _setup(tmp_path)
    status = ont.ontogenesis_status()
    proposals = ontogenesis_revision_proposals(status)
    # Proposals are advisory only (no code rewrite / actuation).
    assert isinstance(proposals, list)
    assert all(p.get("advisory_only") is True for p in proposals)


def test_architecture_evolution_flags_contamination(tmp_path):
    # A contaminated status yields a sensorium/contamination revision proposal.
    status = {"human_label_contamination_score": 0.8,
              "concept_explosion_warning_count": 0,
              "modality_native_concept_ratio": 0.5,
              "world_formation_density": 0.5}
    proposals = ontogenesis_revision_proposals(status)
    targets = {p["target"] for p in proposals}
    assert "sensorium_profile" in targets
    assert "contamination_mitigation" in targets
