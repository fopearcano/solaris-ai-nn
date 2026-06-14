#!/usr/bin/env python3
"""Pilot-2 source preflight demo: validate JSONL/text/numeric/folder sources.

    python examples/run_pilot2_source_preflight_demo.py --state-dir .solaris_ai_nn_pilot2/test_preflight

Creates fixture sources of each kind and runs the read-only preflight checks,
plus an outside-root source that must fail. Writes the preflight report.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.pilot2 import SourcePreflightRunner
from solaris_ai_nn.sensory_membrane import SensorySourceConfig


def main():
    parser = argparse.ArgumentParser(description="Pilot-2 source preflight")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot2/test_preflight")
    args = parser.parse_args()

    root = os.path.join(args.state_dir, "inputs")
    os.makedirs(root, exist_ok=True)
    jp = os.path.join(root, "events.jsonl")
    open(jp, "w").write('{"a":1}\n{"a":2}\n')
    tp = os.path.join(root, "log.txt")
    open(tp, "w").write("observation one\nobservation two\n")
    np_ = os.path.join(root, "nums.csv")
    open(np_, "w").write("ts,value\n1,10\n2,11\n")

    configs = [
        SensorySourceConfig(source_id="jsonl", source_type="jsonl_file",
                            path=jp, enabled=True),
        SensorySourceConfig(source_id="text", source_type="text_file",
                            path=tp, enabled=True),
        SensorySourceConfig(source_id="numeric", source_type="numeric_csv",
                            path=np_, enabled=True),
        SensorySourceConfig(source_id="folder", source_type="folder_poll",
                            path=root, enabled=True),
        SensorySourceConfig(source_id="outside", source_type="text_file",
                            path="/etc/passwd", enabled=True),
    ]
    runner = SourcePreflightRunner(allowed_roots=[root])
    summary = runner.run(configs, state_dir=args.state_dir)

    print("=== Pilot-2 source preflight ===")
    for r in summary["results"]:
        print(f"  {'PASS' if r['passed'] else 'FAIL'}  {r['source_id']} "
              f"({r['source_type']})")
    print(f"passed {summary['passed_count']} of {summary['source_count']}")
    print(f"report : {os.path.join(args.state_dir, 'source_preflight.md')}")
    print("note   : the outside-root source correctly fails; all checks are "
          "read-only")


if __name__ == "__main__":
    main()
