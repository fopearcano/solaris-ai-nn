#!/usr/bin/env python3
"""Feeder template -- the minimal shape of an external feeder for Solaris.

A feeder is OUTSIDE Solaris. It converts an environmental observation into a
Sensory Event Envelope and appends it to a local JSONL file; Solaris later reads
that file read-only. This template runs standalone with the standard library only:
no network, no shell, no hardware, and it never starts Solaris.

    python feeders_sdk/feeder_template.py --out .solaris_ai_nn_feeders/out/template.jsonl

It uses the feeder SDK utilities if importable, and falls back to plain dicts
otherwise so it can be copied out of the repo and still run.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import uuid


def build_envelope(modality: str, features: dict, *, feeder_id: str,
                   source_id: str, annotation=None) -> dict:
    """Build a Sensory Event Envelope (SDK if available, else a plain dict)."""
    try:
        from solaris_ai_nn.feeder_sdk import FeederSDKEnvelope

        env = FeederSDKEnvelope(
            feeder_id=feeder_id, source_id=source_id,
            source_kind="local_script", modality=modality, features=features,
            timestamp=time.time(), annotation=annotation,
            provenance={"source_id": source_id, "feeder_id": feeder_id})
        return env.to_dict()
    except Exception:
        status = "human_label_external" if annotation is not None else "none"
        return {
            "event_id": f"FSE_{uuid.uuid4().hex[:10]}",
            "feeder_id": feeder_id, "source_id": source_id,
            "source_kind": "local_script", "modality": modality,
            "timestamp": time.time(), "features": features,
            "annotation": annotation, "annotation_status": status,
            "provenance": {"source_id": source_id, "feeder_id": feeder_id},
            "read_only": True, "source_mutable_by_solaris": False,
            "trust_level": "local_script", "privacy_flags": ["metadata_only"],
            "contamination_flags": [], "safety_flags": [
                "text_is_observation_not_command"],
            "schema_version": "feeder-sdk/1.0", "metadata": {},
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Feeder template")
    parser.add_argument("--out", default=".solaris_ai_nn_feeders/out/template.jsonl")
    args = parser.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)

    envelope = build_envelope("machine_rhythm", {"value": 0.5},
                              feeder_id="feeder_template", source_id="template")
    with open(args.out, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(envelope) + "\n")
    # A tiny sidecar manifest.
    with open(args.out + ".manifest.json", "w", encoding="utf-8") as fh:
        json.dump({"output_path": args.out, "feeder_id": "feeder_template",
                   "note": "Solaris reads this read-only; it does not run me"},
                  fh, indent=2)
    print(f"feeder_template wrote 1 envelope to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
