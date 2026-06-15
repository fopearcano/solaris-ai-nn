#!/usr/bin/env python3
"""Feeder monitor demo: active feeder, silent feeder, invalid event count.

    python examples/run_feeder_monitor_demo.py --state-dir .solaris_ai_nn_feeders/test_monitor

Writes an active feeder output, a stale (silent) one, and one with an invalid
line, then monitors all three read-only. The monitor never starts or modifies a
feeder.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.feeder_sdk import (
    FeederMonitor,
    FeederSDKEnvelope,
    JSONLFeederWriter,
)


def main():
    parser = argparse.ArgumentParser(description="Feeder monitor demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_feeders/test_monitor")
    args = parser.parse_args()
    base = args.state_dir
    os.makedirs(base, exist_ok=True)

    active = os.path.join(base, "rf.jsonl")
    writer = JSONLFeederWriter(output_path=active, write_manifest=False)
    for i in range(5):
        writer.write(FeederSDKEnvelope(
            feeder_id="rf_feed", source_id="rf",
            source_kind="external_feature_drop", modality="radio_frequency",
            features={"power": 0.6}, timestamp=float(i)))
    # A stale/silent feeder (old mtime).
    silent = os.path.join(base, "echo.jsonl")
    JSONLFeederWriter(output_path=silent, write_manifest=False).write(
        FeederSDKEnvelope(feeder_id="echo_feed", source_id="echo",
                          source_kind="external_feature_drop",
                          modality="ultrasound_echo", features={"boundary": 1.0}))
    old = time.time() - 3600
    os.utime(silent, (old, old))
    # A feeder with an invalid line.
    bad = os.path.join(base, "bad.jsonl")
    with open(bad, "w", encoding="utf-8") as fh:
        fh.write('{"feeder_id":"x","source_id":"x","modality":"vibration",'
                 '"timestamp":1,"provenance":{"source_id":"x","feeder_id":"x"},'
                 '"features":{"amplitude":0.4}}\n')
        fh.write("{not valid json\n")

    snap = FeederMonitor(silence_window_s=60.0).monitor([active, silent, bad])

    print("=== Feeder monitor demo ===")
    print(f"outputs monitored     : {len(snap.outputs)}")
    print(f"active outputs        : {snap.active_count}")
    print(f"silent outputs        : {snap.silent_count}")
    print(f"invalid events        : {snap.invalid_event_count}")
    for o in snap.outputs:
        print(f"  {os.path.basename(o.path):>12}: active={o.active} "
              f"silent={o.silent} events={o.event_count} "
              f"invalid={o.invalid_event_count}")
    print("note                  : the monitor reads output only; it never "
          "starts, stops, or modifies a feeder.")


if __name__ == "__main__":
    main()
