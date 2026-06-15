#!/usr/bin/env python3
"""Feature dropbox feeder -- normalize dropped feature files into envelopes.

This feeder is OUTSIDE Solaris. External tools (e.g. an SDR feature exporter run
separately by the operator) drop feature files into an inbox folder; this script
reads them and writes normalized Sensory Event Envelopes to an output JSONL. It
does NOT modify the source files, does NOT decode private content, and does NOT
control hardware. Standard library only: no network, no shell.

    python feeders/feature_dropbox_feeder.py --inbox .solaris_ai_nn_live/inbox/rf \
        --out .solaris_ai_nn_live/feeds/rf.jsonl --modality alien_rf
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
import uuid


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


def normalize(record: dict, modality: str, source_id: str) -> dict:
    features = record.get("features")
    if not isinstance(features, dict):
        features = {k: v for k, v in record.items()
                    if k not in ("modality", "ts", "timestamp", "annotation")
                    and isinstance(v, (int, float))}
    return {
        "event_id": f"LFE_{uuid.uuid4().hex[:10]}",
        "source_id": source_id,
        "feeder_id": "feature_dropbox_feeder",
        "feeder_mode": "external_feature_drop",
        "modality": record.get("modality", modality),
        "timestamp": float(record.get("timestamp", record.get("ts",
                                                              time.time()))),
        "features": features,
        "provenance": {"source_id": source_id,
                       "feeder_id": "feature_dropbox_feeder",
                       "feeder_mode": "external_feature_drop"},
        "read_only": True,
        "source_mutable_by_solaris": False,
        "trust_level": "external_feature_only",
        "contamination_flags": [],
        "safety_flags": ["source_files_not_modified", "no_private_decoding"],
        "metadata": {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Feature dropbox feeder")
    parser.add_argument("--inbox", required=True, help="inbox folder to read")
    parser.add_argument("--out", required=True, help="output JSONL path")
    parser.add_argument("--modality", default="unknown_field")
    parser.add_argument("--source-id", default="feature_dropbox")
    args = parser.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    written = 0
    if os.path.isdir(args.inbox):
        with open(args.out, "a", encoding="utf-8") as out_fh:
            for name in sorted(os.listdir(args.inbox)):
                path = os.path.join(args.inbox, name)
                if not os.path.isfile(path):
                    continue
                if os.path.splitext(name)[1].lower() not in (".jsonl", ".json",
                                                             ".csv"):
                    continue
                try:
                    records = _read_records(path)
                except (OSError, ValueError, csv.Error):
                    continue
                for rec in records:
                    if isinstance(rec, dict):
                        out_fh.write(json.dumps(
                            normalize(rec, args.modality, args.source_id)) + "\n")
                        written += 1
    print(f"normalized {written} dropbox records to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
