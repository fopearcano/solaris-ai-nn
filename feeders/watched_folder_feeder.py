#!/usr/bin/env python3
"""Watched folder feeder -- observe a folder, write file-rhythm events.

This feeder is OUTSIDE Solaris. It inspects a folder's *metadata* (which files
exist, their sizes, their modification times) and writes Sensory Event Envelopes
describing presence / change / rhythm. It NEVER modifies or deletes the watched
files; it writes only to its own output JSONL. Standard library only: no network,
no shell.

    python feeders/watched_folder_feeder.py --watch /some/folder \
        --out .solaris_ai_nn_live/feeds/folder.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import time
import uuid


def scan_folder(folder: str, source_id: str = "watched_folder") -> list:
    """Return one envelope per file describing its (read-only) metadata."""
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
            "event_id": f"LFE_{uuid.uuid4().hex[:10]}",
            "source_id": source_id,
            "feeder_id": "watched_folder_feeder",
            "feeder_mode": "local_folder",
            "modality": "machine_rhythm",
            "timestamp": mtime,
            "features": {"file_size": size, "name_length": float(len(name))},
            "provenance": {"source_id": source_id,
                           "feeder_id": "watched_folder_feeder",
                           "feeder_mode": "local_folder", "file": name},
            "read_only": True,
            "source_mutable_by_solaris": False,
            "trust_level": "trusted_local_script",
            "contamination_flags": [],
            "safety_flags": ["watched_files_not_modified"],
            "metadata": {},
        })
    return envelopes


def main() -> int:
    parser = argparse.ArgumentParser(description="Watched folder feeder")
    parser.add_argument("--watch", required=True, help="folder to observe")
    parser.add_argument("--out", required=True, help="output JSONL path")
    parser.add_argument("--source-id", default="watched_folder")
    args = parser.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    envelopes = scan_folder(args.watch, args.source_id)
    with open(args.out, "a", encoding="utf-8") as fh:
        for env in envelopes:
            fh.write(json.dumps(env) + "\n")
    print(f"wrote {len(envelopes)} folder envelopes to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
