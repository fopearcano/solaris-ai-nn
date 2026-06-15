"""FeederReplay: bounded; provenance marked replayed; original unmodified."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.feeder_sdk import (
    FeederReplay,
    FeederSDKEnvelope,
    JSONLFeederWriter,
)


def _source(tmp_path, n=12):
    path = str(tmp_path / "src.jsonl")
    writer = JSONLFeederWriter(output_path=path, write_manifest=False)
    for i in range(n):
        writer.write(FeederSDKEnvelope(
            feeder_id="rf", source_id="rf", source_kind="k",
            modality="radio_frequency", features={"power": 0.6},
            timestamp=float(i)))
    return path


def test_replay_bounded(tmp_path):
    src = _source(tmp_path)
    out = str(tmp_path / "replay.jsonl")
    result = FeederReplay(max_events=5).replay(src, out)
    assert result.events_replayed == 5
    assert result.bounded_stop == "max_events reached"


def test_provenance_marked_replayed(tmp_path):
    src = _source(tmp_path, n=3)
    out = str(tmp_path / "replay.jsonl")
    FeederReplay().replay(src, out)
    first = json.loads(open(out).readline())
    assert first["provenance"]["replayed"] is True
    assert "original_timestamp" in first["provenance"]


def test_original_file_not_modified(tmp_path):
    src = _source(tmp_path, n=3)
    before = open(src).read()
    out = str(tmp_path / "replay.jsonl")
    result = FeederReplay().replay(src, out)
    assert result.source_modified is False
    assert open(src).read() == before
