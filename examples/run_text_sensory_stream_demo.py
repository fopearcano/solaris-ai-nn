#!/usr/bin/env python3
"""Text sensory stream demo: text lines as environmental stimuli, not commands.

    python examples/run_text_sensory_stream_demo.py --state-dir .solaris_ai_nn_state/test_text_sensory

Reads text lines as read-only environmental stimuli. A line that looks like a
command (e.g. "rm -rf /") is still only environmental text; it is never
executed and never an operator command. Repeated patterns may become
internally-generated proto-symbol candidates.
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
    parser = argparse.ArgumentParser(description="Text sensory stream demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_text_sensory")
    args = parser.parse_args()

    root = os.path.join(args.state_dir, "inputs")
    state = os.path.join(args.state_dir, "state")
    os.makedirs(root, exist_ok=True)
    path = os.path.join(root, "log.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("temperature rising\nrm -rf /\ntemperature rising\n"
                 "temperature rising\nbird call observed\n")

    rt = SensoryMembraneRuntime(
        state_dir=state, allowed_input_roots=[root], enabled=True,
        simulated_sources_only=False, real_read_only_sources_enabled=True)
    rt.add_source(SensorySourceConfig(source_id="text1",
                                      source_type="text_file", path=path,
                                      enabled=True))
    rt.initialize()
    rt.run_bounded(max_polls=3)

    print("=== Text sensory stream demo ===")
    print(f"events ingested      : {rt.summary()['total_events']}")
    print("every line classified : textual_environmental_stimulus "
          "(NOT a command)")
    g = rt.grounding.snapshot()
    print(f"proto-symbol candidates: {g['proto_symbol_candidate_count']} "
          "(internally generated; input words are not the symbols)")
    print("note                  : 'rm -rf /' was treated as text, never run")


if __name__ == "__main__":
    main()
