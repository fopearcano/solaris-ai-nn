#!/usr/bin/env python3
"""JSONL sensory stream demo: ingest, normalize, provenance, publish (bounded).

    python examples/run_jsonl_sensory_stream_demo.py --state-dir .solaris_ai_nn_state/test_jsonl_sensory

Reads an append-only JSONL source as read-only environmental input, normalizes
events into canonical stimuli with provenance, and publishes them to a bounded
ConscienceBus. Malformed lines are skipped with a warning.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.conscience import ConscienceBus
from solaris_ai_nn.sensory_membrane import (
    SensoryMembraneRuntime,
    SensorySourceConfig,
)


def main():
    parser = argparse.ArgumentParser(description="JSONL sensory stream demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_jsonl_sensory")
    args = parser.parse_args()

    root = os.path.join(args.state_dir, "inputs")
    state = os.path.join(args.state_dir, "state")
    os.makedirs(root, exist_ok=True)
    path = os.path.join(root, "events.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(8):
            fh.write(json.dumps({"evt": "ping", "i": i}) + "\n")
        fh.write("{ malformed line\n")

    bus = ConscienceBus(state_dir=state)
    received = []
    bus.subscribe("stimulus",
                  lambda m: received.append(m) if m.source_module
                  == "sensory_membrane" else None, "demo")
    rt = SensoryMembraneRuntime(
        state_dir=state, allowed_input_roots=[root], enabled=True,
        simulated_sources_only=False, real_read_only_sources_enabled=True,
        bus=bus)
    rt.add_source(SensorySourceConfig(source_id="jsonl1",
                                      source_type="jsonl_file", path=path,
                                      enabled=True))
    rt.initialize()
    rt.run_bounded(max_polls=2)
    s = rt.summary()

    print("=== JSONL sensory stream demo ===")
    print(f"events ingested : {s['total_events']}")
    print(f"malformed       : {s['malformed_events']}")
    print(f"published to bus: {s['published_events']}")
    print(f"bus received    : {len(received)}")
    print(f"provenance      : {s['provenance_completeness']}")
    print("note            : environmental input, never an operator command")


if __name__ == "__main__":
    main()
