#!/usr/bin/env python3
"""Dimensional comparison demo: five event kinds on six fixed axes.

    python examples/run_dimensional_comparison_demo.py

An observed stream event, a simulated GridWorld action, an offline replay
trace, a sidecar suggestion, and an operator approval are each placed on
the six dimensions (temporal, scope, authority, evidence, certainty, risk),
then compared pairwise with deterministic distances and plain-sentence
explanations. No embeddings, no ML -- ordered lists and index arithmetic.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.ego import Dimension, DimensionalComparator

EVENTS = [
    ("observed stream event",
     {"source": "stream", "kind": "stream_line", "payload": "line"}),
    ("simulated GridWorld action",
     {"source": "grid_world", "kind": "simulated_action",
      "label": "move_north"}),
    ("offline replay trace",
     {"source": "offline_replay", "kind": "replay_trace"}),
    ("sidecar suggestion",
     {"source": "sidecar", "kind": "suggestion",
      "label": "remain_observe_only"}),
    ("operator approval",
     {"source": "operator", "kind": "approval", "label": "approve_run"}),
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dimensional comparison demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/"
                                "dimensional_comparison_demo")
    args = parser.parse_args()

    comparator = DimensionalComparator()
    frames = [(name, comparator.classify_event(event))
              for name, event in EVENTS]

    print("=" * 70)
    print("Solaris-AI-NN -- dimensional comparison demo")
    print("=" * 70)
    print("frames (six axes each):")
    for name, frame in frames:
        print(f"  {name}:")
        for dimension in Dimension.ALL:
            print(f"    {dimension:10s} {frame.value(dimension)}")
    print()
    print("pairwise distances and differences:")
    for i in range(len(frames)):
        for j in range(i + 1, len(frames)):
            name_a, frame_a = frames[i]
            name_b, frame_b = frames[j]
            comparison = comparator.compare(frame_a, frame_b)
            print(f"  {name_a}  vs  {name_b}: "
                  f"distance={comparison.distance:.3f}")
            print(f"    {comparison.explanation[:110]}")
    out = Path(args.state_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "dimensional_frames.json", "w", encoding="utf-8") as fh:
        json.dump([{"name": n, **f.to_dict()} for n, f in frames], fh,
                  indent=2, default=str)
    print()
    print(f"frames saved: {out / 'dimensional_frames.json'}")
    print("note: frames are recorded operational placements, not "
          "experiential comparisons.")


if __name__ == "__main__":
    main()
