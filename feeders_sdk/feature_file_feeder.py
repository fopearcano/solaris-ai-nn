#!/usr/bin/env python3
"""Feature file feeder -- normalize external feature files into envelopes.

OUTSIDE Solaris. Reads externally-created JSON/CSV feature files and writes
normalized Sensory Event Envelopes, preserving the source path and a content hash.
It NEVER modifies the source files, decodes no private content, and controls no
hardware. Stdlib only: no network, no shell.

    python feeders_sdk/feature_file_feeder.py --input feats.csv --out out/features.jsonl --modality radio_frequency
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import time
import uuid


def _hash(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_records(path: str) -> list:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        with open(path, "r", encoding="utf-8", errors="replace", newline="") \
                as fh:
            rows = []
            for row in csv.DictReader(fh):
                rec = {}
                for k, v in row.items():
                    try:
                        rec[k] = float(v)
                    except (TypeError, ValueError):
                        rec[k] = v
                rows.append(rec)
            return rows
    if ext == ".json":
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            data = json.load(fh)
        return data if isinstance(data, list) else [data]
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def normalize(record: dict, modality: str, source_id: str, src_hash: str,
              src_path: str) -> dict:
    features = record.get("features")
    if not isinstance(features, dict):
        features = {k: v for k, v in record.items()
                    if k not in ("modality", "ts", "timestamp", "annotation")
                    and isinstance(v, (int, float))}
    return {
        "event_id": f"FSE_{uuid.uuid4().hex[:10]}",
        "feeder_id": "feature_file_feeder", "source_id": source_id,
        "source_kind": "external_feature_drop",
        "modality": record.get("modality", modality),
        "timestamp": float(record.get("timestamp", record.get("ts",
                                                              time.time()))),
        "features": features, "annotation": None, "annotation_status": "none",
        "provenance": {"source_id": source_id, "feeder_id": "feature_file_feeder",
                       "source_path": src_path, "source_hash": src_hash},
        "read_only": True, "source_mutable_by_solaris": False,
        "trust_level": "external_feature_only",
        "privacy_flags": ["no_raw_private_content"],
        "contamination_flags": [],
        "safety_flags": ["text_is_observation_not_command",
                         "source_files_not_modified"],
        "schema_version": "feeder-sdk/1.0", "metadata": {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Feature file feeder")
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--modality", default="unknown_field")
    parser.add_argument("--source-id", default="feature_file")
    args = parser.parse_args()
    if not os.path.isfile(args.input):
        print(f"input file missing: {args.input}")
        return 1
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    src_hash = _hash(args.input)
    written = 0
    with open(args.out, "a", encoding="utf-8") as out_fh:
        for rec in _read_records(args.input):
            if isinstance(rec, dict):
                out_fh.write(json.dumps(normalize(
                    rec, args.modality, args.source_id, src_hash,
                    args.input)) + "\n")
                written += 1
    print(f"feature_file_feeder wrote {written} envelope(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
