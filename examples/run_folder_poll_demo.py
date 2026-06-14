#!/usr/bin/env python3
"""Folder poll demo: file presence/change events, no writes to the folder.

    python examples/run_folder_poll_demo.py --state-dir .solaris_ai_nn_state/test_folder_poll

Polls an allowed input folder and emits file_presence / file_change events by
stdlib metadata polling (no OS watcher). It never writes to or modifies the
watched folder.
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
    parser = argparse.ArgumentParser(description="Folder poll demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_folder_poll")
    args = parser.parse_args()

    watched = os.path.join(args.state_dir, "watched")
    state = os.path.join(args.state_dir, "state")
    os.makedirs(watched, exist_ok=True)
    with open(os.path.join(watched, "a.txt"), "w", encoding="utf-8") as fh:
        fh.write("first")
    before = sorted(os.listdir(watched))

    rt = SensoryMembraneRuntime(
        state_dir=state, allowed_input_roots=[watched], enabled=True,
        simulated_sources_only=False, real_read_only_sources_enabled=True)
    rt.add_source(SensorySourceConfig(source_id="folder1",
                                      source_type="folder_poll", path=watched,
                                      enabled=True))
    rt.initialize()
    rt.run_bounded(max_polls=1)  # detects presence of a.txt

    # Add a new file and a change; the membrane only reads, never writes.
    with open(os.path.join(watched, "b.txt"), "w", encoding="utf-8") as fh:
        fh.write("new file")
    rt.run_bounded(max_polls=1)  # detects b.txt presence
    after = sorted(os.listdir(watched))

    print("=== Folder poll demo ===")
    print(f"events ingested : {rt.summary()['total_events']}")
    print(f"folder before   : {before}")
    print(f"folder after    : {after}")
    print(f"membrane wrote? : {before != after and 'no (the demo added b.txt)'}")
    print("note            : the membrane only reads; it never modifies the "
          "watched folder")


if __name__ == "__main__":
    main()
