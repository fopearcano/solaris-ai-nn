"""Plural sensorium <-> proto-language / world model: modality-native structure."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def _runtime(tmp_path, modality="alien_rf"):
    path = os.path.join(tmp_path, f"{modality}.jsonl")
    with open(path, "w") as fh:
        for i in range(10):
            fh.write(json.dumps({"modality": modality, "v": 0.7,
                                 "ts": float(i)}) + "\n")
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path) + "/s")
    rt.add_feeder(fixture_feeder(f"{modality}_feed", path, modality))
    rt.run_bounded(max_polls=1)
    return rt


def test_modality_grounded_proto_symbol_created(tmp_path):
    rt = _runtime(str(tmp_path), "alien_rf")
    assert rt.proto_symbol_candidates
    sym = rt.proto_symbol_candidates[0]
    assert sym["symbol_type"] == "rf_grounded_symbol"
    assert sym["modality"] == "radio_frequency"
    # The symbol emerges from a recurrent invariant, not a raw feature name.
    assert sym["support"] >= 3
    assert sym["provenance"]["source_id"] == "alien_rf_feed"


def test_world_model_preserves_modality_native_structure(tmp_path):
    rt = _runtime(str(tmp_path), "alien_echo")
    kinds = {s["kind"] for s in rt.world_model_structures}
    assert "modality_source" in kinds
    # The structures keep the modality, not a human object label.
    src = next(s for s in rt.world_model_structures
              if s["kind"] == "modality_source")
    assert src["modality"] == "ultrasound_echo"
    blob = json.dumps(rt.world_model_structures).lower()
    for human_label in ("person", "chair", "room", "object"):
        assert human_label not in blob


def test_echo_symbol_type(tmp_path):
    rt = _runtime(str(tmp_path), "alien_echo")
    assert any(p["symbol_type"] == "echo_grounded_symbol"
               for p in rt.proto_symbol_candidates)
