#!/usr/bin/env python3
"""Numeric sensory stream demo: trend / spike / stable / missing detection.

    python examples/run_numeric_sensory_stream_demo.py --state-dir .solaris_ai_nn_state/test_numeric_sensory

Reads CSV-like numeric rows (stdlib only, no pandas) as read-only
environmental input and labels per-row trends (rising / falling / stable /
spike). Malformed rows become warning events.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.sensory_membrane import (
    SensoryMembraneRuntime,
    SensorySourceConfig,
)


def main():
    parser = argparse.ArgumentParser(description="Numeric sensory stream demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_numeric_sensory")
    args = parser.parse_args()

    root = os.path.join(args.state_dir, "inputs")
    state = os.path.join(args.state_dir, "state")
    os.makedirs(root, exist_ok=True)
    path = os.path.join(root, "nums.csv")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("ts,value\n1,10\n2,11\n3,10\n4,100\noops,bad\n6,12\n")

    rt = SensoryMembraneRuntime(
        state_dir=state, allowed_input_roots=[root], enabled=True,
        simulated_sources_only=False, real_read_only_sources_enabled=True)
    rt.add_source(SensorySourceConfig(source_id="num1",
                                      source_type="numeric_csv", path=path,
                                      enabled=True))
    rt.initialize()
    rt.run_bounded(max_polls=2)

    s = rt.summary()
    print("=== Numeric sensory stream demo ===")
    print(f"rows ingested : {s['total_events']}")
    print(f"malformed     : {s['malformed_events']} (the 'oops,bad' row)")
    print("trends labelled: rising / falling / stable / spike per row")
    print("spike example : value jumped 10 -> 100 (spike)")
    print("note          : stdlib CSV parsing only; no pandas")


if __name__ == "__main__":
    main()
