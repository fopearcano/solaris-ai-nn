#!/usr/bin/env python3
"""Feeder replay demo: replay a JSONL envelope stream into a new stream.

    python examples/run_feeder_replay_demo.py --state-dir .solaris_ai_nn_feeders/test_replay

Writes a source envelope stream, replays it into a new stream with a speed factor
and a bounded event cap, and confirms the original is unmodified and each replayed
event is marked replayed in its provenance.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.feeder_sdk import (
    FeederReplay,
    FeederSDKEnvelope,
    JSONLFeederWriter,
)


def main():
    parser = argparse.ArgumentParser(description="Feeder replay demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_feeders/test_replay")
    args = parser.parse_args()
    base = args.state_dir
    os.makedirs(base, exist_ok=True)

    src = os.path.join(base, "rf.jsonl")
    writer = JSONLFeederWriter(output_path=src, write_manifest=False)
    for i in range(12):
        writer.write(FeederSDKEnvelope(
            feeder_id="rf_feed", source_id="rf",
            source_kind="external_feature_drop", modality="radio_frequency",
            features={"power": 0.6}, timestamp=float(i)))
    before = open(src).read()

    out = os.path.join(base, "rf_replay.jsonl")
    result = FeederReplay(speed_factor=2.0, max_events=8).replay(src, out)

    print("=== Feeder replay demo ===")
    print(f"events replayed       : {result.events_replayed}")
    print(f"bounded stop          : {result.bounded_stop}")
    print(f"source modified       : {result.source_modified}")
    print(f"original unchanged    : {open(src).read() == before}")
    first = json.loads(open(out).readline())
    print(f"replayed marked       : {first['provenance'].get('replayed')}")
    print(f"original timestamp    : {first['provenance'].get('original_timestamp')}")
    print("note                  : replay is local-only and never modifies the "
          "original stream.")


if __name__ == "__main__":
    main()
