"""Stream adapters: JSONL / CSV / watched folder read; read-only preserved."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.plural_sensorium import fixture_feeder
from solaris_ai_nn.plural_sensorium.external_feeders import (
    ExternalFeederDescriptor,
    FeederSourceType,
)
from solaris_ai_nn.plural_sensorium.stream_adapters import (
    read_csv_stream,
    read_jsonl_stream,
    read_watched_folder,
)


def test_jsonl_stream_read(tmp_path):
    path = tmp_path / "rf.jsonl"
    with open(path, "w") as fh:
        for i in range(3):
            fh.write(json.dumps({"modality": "alien_rf", "power": 0.5,
                                 "ts": float(i)}) + "\n")
    feeder = fixture_feeder("rf", str(path), "alien_rf")
    result = read_jsonl_stream(feeder)
    assert len(result.events) == 3
    assert result.events[0].modality == "radio_frequency"
    assert result.events[0].has_provenance


def test_csv_stream_read(tmp_path):
    path = tmp_path / "vib.csv"
    with open(path, "w") as fh:
        fh.write("amp,freq\n0.3,10\n0.4,11\n")
    feeder = fixture_feeder("vib", str(path), "alien_vibration")
    result = read_csv_stream(feeder)
    assert len(result.events) == 2
    assert result.events[0].features["amp"] == 0.3


def test_watched_folder_read(tmp_path):
    folder = tmp_path / "drop"
    folder.mkdir()
    (folder / "a.bin").write_bytes(b"xxx")
    (folder / "b.bin").write_bytes(b"yyyy")
    feeder = ExternalFeederDescriptor(
        feeder_id="drop", source_type=FeederSourceType.FOLDER_DROP,
        path=str(folder), modality_hint="machine_rhythm")
    result = read_watched_folder(feeder)
    assert len(result.events) == 2
    assert all("file_size" in e.features for e in result.events)


def test_read_only_preserved(tmp_path):
    path = tmp_path / "rf.jsonl"
    path.write_text('{"modality":"alien_rf","power":0.5,"ts":0}\n')
    feeder = fixture_feeder("rf", str(path), "alien_rf")
    before = path.read_text()
    result = read_jsonl_stream(feeder)
    # Reading never modifies the source file.
    assert path.read_text() == before
    assert all(e.read_only for e in result.events)
