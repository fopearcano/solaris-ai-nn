#!/usr/bin/env python3
"""Sensory membrane dry-run: validate read-only sources, publish nothing.

    python examples/run_sensory_membrane_dry_run.py --state-dir .solaris_ai_nn_state/test_sensory_dry_run

Creates small test-fixture sources, validates their read-only contracts, runs
a bounded dry-run (which ingests and normalizes but publishes no stimuli), and
writes the membrane report. The system never acts on the sources.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.sensory_membrane import (
    SensoryMembraneReportBuilder,
    SensoryMembraneRuntime,
    SensorySourceConfig,
)


def _fixtures(root):
    os.makedirs(root, exist_ok=True)
    with open(os.path.join(root, "events.jsonl"), "w", encoding="utf-8") as fh:
        for i in range(5):
            fh.write(json.dumps({"evt": "ping", "i": i}) + "\n")
    with open(os.path.join(root, "log.txt"), "w", encoding="utf-8") as fh:
        fh.write("hello world\nsecond observation\n")


def main():
    parser = argparse.ArgumentParser(description="Sensory membrane dry-run")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_sensory_dry_run")
    args = parser.parse_args()

    root = os.path.join(args.state_dir, "inputs")
    state = os.path.join(args.state_dir, "state")
    _fixtures(root)
    rt = SensoryMembraneRuntime(
        state_dir=state, allowed_input_roots=[root], enabled=True,
        dry_run=True, simulated_sources_only=False,
        real_read_only_sources_enabled=True)
    for sid, st in (("j1", "jsonl_file"), ("t1", "text_file")):
        path = os.path.join(root, "events.jsonl" if st == "jsonl_file"
                            else "log.txt")
        rt.add_source(SensorySourceConfig(source_id=sid, source_type=st,
                                          path=path, enabled=True))
    rt.initialize()
    rt.run_bounded(max_polls=3)
    report = SensoryMembraneReportBuilder(state_dir=state).build_and_write(rt)
    s = rt.summary()

    print("=== Sensory membrane dry-run (no stimuli published) ===")
    print(f"sources        : {s['source_count']}")
    print(f"read-only      : {s['read_only']}")
    print(f"events ingested: {s['total_events']}")
    print(f"published      : {s['published_events']}  (dry-run)")
    print(f"provenance     : {s['provenance_completeness']}")
    print(f"report         : {report.sections['report_paths']['markdown']}")
    print("note           : the world may enter; the system never acts on it")


if __name__ == "__main__":
    main()
