#!/usr/bin/env python3
"""Simulated multimodal feeder demo -- generate a mixed feeder stream + ingest it.

    python examples/run_simulated_multimodal_feeder_demo.py --state-dir .solaris_ai_nn_feeders/test_multimodal

Generates simulated RF / echo / vibration / thermal / magnetic envelopes (with
jitter, silence, drift, and noise), validates the output, and shows it is
consumable by the Live Field (read-only). These are simulated fixtures, NOT real
sensors.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import uuid

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.feeder_sdk import (
    FeederOutputValidator,
    FeederSDKEnvelope,
    JSONLFeederWriter,
)
from solaris_ai_nn.feeder_sdk.noise import DriftModel, DropoutModel, FeatureNoiseModel


def main():
    parser = argparse.ArgumentParser(description="Simulated multimodal feeder")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_feeders/test_multimodal")
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    base = args.state_dir
    os.makedirs(base, exist_ok=True)

    out = os.path.join(base, "multimodal.jsonl")
    writer = JSONLFeederWriter(output_path=out, write_manifest=True)
    noise = FeatureNoiseModel(sigma=0.05, seed=args.seed)
    dropout = DropoutModel(probability=0.15, seed=args.seed)
    drift = DriftModel(rate=0.01)
    rng = random.Random(args.seed)
    modalities = ("radio_frequency", "ultrasound_echo", "vibration",
                  "thermal_gradient", "magnetic")
    written = 0
    for i in range(args.count):
        for modality in modalities:
            if dropout.drop():  # silence / missing expected
                continue
            value = drift.apply(noise.apply(0.5 + 0.2 * rng.random()))
            writer.write(FeederSDKEnvelope(
                feeder_id=f"sim_{modality}", source_id=f"sim_{modality}",
                source_kind="fixture_replay", modality=modality,
                features={"value": round(value, 4)},
                timestamp=float(i) + rng.uniform(-0.1, 0.1),
                trust_level="simulated_fixture",
                provenance={"source_id": f"sim_{modality}",
                            "feeder_id": f"sim_{modality}",
                            "simulated_fixture": True}))
            written += 1

    report = FeederOutputValidator().validate_file(out)
    print("=== Simulated multimodal feeder demo ===")
    print(f"modalities            : {list(modalities)}")
    print(f"envelopes written     : {written}")
    print(f"output valid          : {report['valid']} "
          f"(events {report['valid_count']}, invalid {report['invalid_count']})")
    print(f"output (Live Field can read this): {out}")
    print("note                  : simulated fixtures, NOT real sensors; "
          "provenance marks simulated_fixture.")


if __name__ == "__main__":
    main()
