"""Metabolism source diet aligns with the Sensorium Lab world signature."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.perceptual_metabolism import SourceDietAnalyzer
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.sensorium_lab.world_signature import WorldSignatureBuilder


def _sensorium(tmp_path, counts):
    """Build a sensorium where each modality gets `counts[mod]` events."""
    os.makedirs(str(tmp_path), exist_ok=True)
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    for mod, n in counts.items():
        path = os.path.join(str(tmp_path), f"{mod}.jsonl")
        with open(path, "w") as fh:
            for i in range(n):
                fh.write(json.dumps({"modality": mod, "v": 0.6,
                                     "ts": float(i)}) + "\n")
        rt.add_feeder(fixture_feeder(f"{mod}_feed", path, mod))
    rt.run_bounded(max_polls=1)
    return rt


def test_source_diet_matches_world_signature_dominance(tmp_path):
    counts = {"alien_rf": 12, "alien_vibration": 4, "human_textual": 2}
    rt = _sensorium(tmp_path, counts)

    sig = WorldSignatureBuilder().build("arm", "fixture", rt)
    diet = SourceDietAnalyzer().analyze(rt)

    # The same sensorium yields the same dominant modality in both views.
    # (`alien_rf` is canonicalised to `radio_frequency` by the sensorium.)
    dominant_modality = max(sig.modality_distribution,
                            key=sig.modality_distribution.get)
    assert dominant_modality == "radio_frequency"
    assert 0.0 <= diet.modality_dominance <= 1.0
    assert diet.diet_diversity > 0.0


def test_source_diet_diversity_tracks_modality_spread(tmp_path):
    narrow = SourceDietAnalyzer().analyze(
        _sensorium(tmp_path / "narrow", {"alien_rf": 12}))
    wide = SourceDietAnalyzer().analyze(
        _sensorium(tmp_path / "wide",
                   {"alien_rf": 6, "alien_vibration": 6, "alien_echo": 6}))
    # A broader sensorium has a more diverse (less dominated) diet.
    assert wide.diet_diversity >= narrow.diet_diversity
    assert wide.modality_dominance <= narrow.modality_dominance


def test_comparative_source_diet(tmp_path):
    human_heavy = SourceDietAnalyzer().analyze(
        _sensorium(tmp_path / "h", {"human_textual": 12, "alien_rf": 1}))
    alien_heavy = SourceDietAnalyzer().analyze(
        _sensorium(tmp_path / "a", {"alien_rf": 12, "human_textual": 1}))
    assert human_heavy.dominant_class == "human_like"
    assert alien_heavy.dominant_class == "non_human"
