#!/usr/bin/env python3
"""Folder rhythm feeder -- observe folder metadata -> file/rhythm events.

OUTSIDE Solaris. Reads a folder's file metadata and writes machine-rhythm
envelopes (file presence, size, name length). It NEVER modifies or deletes the
watched folder; it writes only to its own output. Stdlib only: no network, no
shell, no hardware.

    python feeders_sdk/folder_rhythm_feeder.py --watch /some/folder --out out/folder.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import uuid


def scan(folder: str, source_id: str = "watched_folder") -> list:
    envelopes = []
    if not os.path.isdir(folder):
        return envelopes
    for name in sorted(os.listdir(folder)):
        full = os.path.join(folder, name)
        if not os.path.isfile(full):
            continue
        try:
            size = float(os.path.getsize(full))
            mtime = os.path.getmtime(full)
        except OSError:
            continue
        envelopes.append({
            "event_id": f"FSE_{uuid.uuid4().hex[:10]}",
            "feeder_id": "folder_rhythm_feeder", "source_id": source_id,
            "source_kind": "local_folder", "modality": "machine_rhythm",
            "timestamp": mtime,
            "features": {"file_size": size, "name_length": float(len(name))},
            "annotation": None, "annotation_status": "none",
            "provenance": {"source_id": source_id,
                           "feeder_id": "folder_rhythm_feeder", "file": name},
            "read_only": True, "source_mutable_by_solaris": False,
            "trust_level": "local_script",
            "privacy_flags": ["contains_file_metadata", "no_raw_private_content"],
            "contamination_flags": [],
            "safety_flags": ["text_is_observation_not_command",
                             "watched_files_not_modified"],
            "schema_version": "feeder-sdk/1.0", "metadata": {}})
    return envelopes


def main() -> int:
    parser = argparse.ArgumentParser(description="Folder rhythm feeder")
    parser.add_argument("--watch", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--source-id", default="watched_folder")
    args = parser.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    envelopes = scan(args.watch, args.source_id)
    with open(args.out, "a", encoding="utf-8") as fh:
        for env in envelopes:
            fh.write(json.dumps(env) + "\n")
    print(f"folder_rhythm_feeder wrote {len(envelopes)} envelope(s) to "
          f"{args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
