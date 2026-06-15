"""Writer utilities: JSONL appends; rolling rotates; manifest; no source mod."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.feeder_sdk import (
    FeederSDKEnvelope,
    JSONLFeederWriter,
    RollingJSONLFeederWriter,
)


def _env(i=0):
    return FeederSDKEnvelope(feeder_id="rf", source_id="rf", source_kind="k",
                            modality="radio_frequency", features={"power": 0.6},
                            timestamp=float(i))


def test_jsonl_writer_appends(tmp_path):
    out = str(tmp_path / "rf.jsonl")
    writer = JSONLFeederWriter(output_path=out)
    writer.write(_env(0))
    writer.write(_env(1))
    lines = open(out).read().strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["modality"] == "radio_frequency"


def test_manifest_written(tmp_path):
    out = str(tmp_path / "rf.jsonl")
    result = JSONLFeederWriter(output_path=out).write(_env())
    assert result.manifest_path and os.path.isfile(result.manifest_path)
    assert result.checksum


def test_rolling_writer_rotates(tmp_path):
    out = str(tmp_path / "rf.jsonl")
    writer = RollingJSONLFeederWriter(output_path=out, max_events=3)
    rotated = False
    for i in range(7):
        if writer.write(_env(i)).rotated:
            rotated = True
    assert rotated
    # A rotated file exists alongside the current one.
    assert any(p.name.startswith("rf.jsonl.") for p in tmp_path.iterdir())


def test_no_source_modification(tmp_path):
    # A writer only touches its own output path.
    source = tmp_path / "source.jsonl"
    source.write_text('{"x": 1}\n')
    before = source.read_text()
    out = str(tmp_path / "out.jsonl")
    JSONLFeederWriter(output_path=out).write(_env())
    assert source.read_text() == before
