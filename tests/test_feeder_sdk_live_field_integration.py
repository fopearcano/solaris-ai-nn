"""Feeder SDK <-> Live Field: SDK output validated; manifest; monitor snapshot."""

from __future__ import annotations

import os

from solaris_ai_nn.feeder_sdk import FeederSDKEnvelope, JSONLFeederWriter
from solaris_ai_nn.live_field import LiveFeederRegistry, LiveFieldRuntime


def _runtime(tmp_path):
    base = str(tmp_path / "lf")
    os.makedirs(base, exist_ok=True)
    return base, LiveFieldRuntime(state_dir=base, live_root=base,
                                  registry=LiveFeederRegistry(live_root=base))


def test_live_field_validates_sdk_output(tmp_path):
    base, rt = _runtime(tmp_path)
    path = os.path.join(base, "rf.jsonl")
    writer = JSONLFeederWriter(output_path=path, write_manifest=False)
    for i in range(4):
        writer.write(FeederSDKEnvelope(
            feeder_id="rf", source_id="rf", source_kind="external_feature_drop",
            modality="radio_frequency", features={"power": 0.6},
            timestamp=float(i)))
    result = rt.feeder_sdk_output_validation(path)
    assert result["valid"] is True
    assert result["valid_count"] == 4


def test_feeder_pack_manifest_read(tmp_path):
    _base, rt = _runtime(tmp_path)
    manifest = rt.feeder_sdk_manifest()
    assert manifest["feeders"]
    assert manifest["supported_modalities"]


def test_monitor_snapshot_exposed(tmp_path):
    base, rt = _runtime(tmp_path)
    path = os.path.join(base, "rf.jsonl")
    JSONLFeederWriter(output_path=path, write_manifest=False).write(
        FeederSDKEnvelope(feeder_id="rf", source_id="rf", source_kind="k",
                          modality="radio_frequency", features={"power": 0.6}))
    snap = rt.feeder_sdk_monitor_snapshot([path])
    assert snap["output_count"] == 1
