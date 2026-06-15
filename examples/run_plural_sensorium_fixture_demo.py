#!/usr/bin/env python3
"""Plural sensorium fixture demo: mixed human-like + non-human feature streams.

    python examples/run_plural_sensorium_fixture_demo.py --state-dir .solaris_ai_nn_state/test_plural_sensorium

Builds external (fixture) feeders for human-like text and non-human RF / echo /
vibration features, runs the bounded sensorium, updates receptors and the
continuous sensory field, detects absence and invariants, and writes the report.
No hardware is accessed; human labels are never ground truth.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.plural_sensorium.reports import PluralSensoriumReportBuilder


def _write_fixture(path, modality, n=8, key="v"):
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(n):
            fh.write(json.dumps({"modality": modality,
                                 key: 0.5 + 0.4 * (i % 2),
                                 "ts": float(i)}) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Plural sensorium fixture demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_plural_sensorium")
    args = parser.parse_args()
    base = args.state_dir
    feeds = os.path.join(base, "feeds")
    os.makedirs(feeds, exist_ok=True)

    rt = PluralSensoriumRuntime(state_dir=base, input_roots=[feeds])
    for modality, name in (("human_textual", "text"), ("alien_rf", "rf"),
                           ("alien_echo", "echo"),
                           ("alien_vibration", "vib")):
        path = os.path.join(feeds, f"{name}.jsonl")
        _write_fixture(path, modality)
        rt.add_feeder(fixture_feeder(f"{name}_feed", path, modality))

    result = rt.run_bounded(max_polls=2)
    status = rt.plural_sensorium_status()
    out = PluralSensoriumReportBuilder(rt).write()

    print("=== Plural sensorium fixture demo ===")
    print(f"events ingested       : {result['events_ingested']}")
    print(f"active modalities     : {status['active_modalities']}")
    print(f"active receptors      : {status['active_receptor_count']}")
    print(f"sensory field pressure: {status['sensory_field_pressure']:.2f}")
    print(f"absence events        : {status['absence_event_count']}")
    print(f"invariant candidates  : {status['invariant_candidate_count']}")
    print(f"cross-modal relations : {status['cross_modal_relation_count']}")
    print(f"proto-symbols         : "
          f"{status['modality_grounded_proto_symbol_count']}")
    print(f"report                : {out['markdown']}")
    print("note                  : read-only feeders; no hardware; human labels "
          "never ground truth.")


if __name__ == "__main__":
    main()
