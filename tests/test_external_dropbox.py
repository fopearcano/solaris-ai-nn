"""FeatureDropbox: JSONL/JSON/CSV read; source files never modified."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.live_field import FeatureDropbox, FeatureDropboxIngestor


def _dropbox(tmp_path):
    db = FeatureDropbox(live_root=str(tmp_path))
    db.ensure_folders()
    return db


def test_jsonl_dropbox_read(tmp_path):
    db = _dropbox(tmp_path)
    path = os.path.join(db.folder_for("rf"), "rf.jsonl")
    with open(path, "w") as fh:
        fh.write(json.dumps({"power": 0.7, "ts": 1.0}) + "\n")
    result = FeatureDropboxIngestor(dropbox=db).poll()
    assert result.envelopes
    assert result.envelopes[0].modality == "radio_frequency"


def test_json_dropbox_read(tmp_path):
    db = _dropbox(tmp_path)
    path = os.path.join(db.folder_for("echo"), "echo.json")
    with open(path, "w") as fh:
        json.dump([{"boundary": 1.0, "ts": 1.0}, {"boundary": 1.2, "ts": 2.0}],
                  fh)
    result = FeatureDropboxIngestor(dropbox=db).poll()
    assert len(result.envelopes) == 2


def test_csv_dropbox_read(tmp_path):
    db = _dropbox(tmp_path)
    path = os.path.join(db.folder_for("vibration"), "vib.csv")
    with open(path, "w") as fh:
        fh.write("amp,freq\n0.3,10\n0.4,11\n")
    result = FeatureDropboxIngestor(dropbox=db).poll()
    assert len(result.envelopes) == 2
    assert result.envelopes[0].modality == "vibration"


def test_source_files_not_modified(tmp_path):
    db = _dropbox(tmp_path)
    path = os.path.join(db.folder_for("rf"), "rf.jsonl")
    content = json.dumps({"power": 0.5, "ts": 1.0}) + "\n"
    with open(path, "w") as fh:
        fh.write(content)
    FeatureDropboxIngestor(dropbox=db).poll()
    # Reading never deletes, moves, or modifies the source file.
    assert os.path.isfile(path)
    assert open(path).read() == content


def test_corrupt_file_recorded(tmp_path):
    db = _dropbox(tmp_path)
    path = os.path.join(db.folder_for("rf"), "bad.json")
    with open(path, "w") as fh:
        fh.write("{not valid json")
    result = FeatureDropboxIngestor(dropbox=db).poll()
    assert path in result.corrupt_files
