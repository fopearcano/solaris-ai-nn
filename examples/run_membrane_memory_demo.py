#!/usr/bin/env python3
"""Membrane memory demo: source reliability, toxicity, repeated quarantine.

    python examples/run_membrane_memory_demo.py --state-dir .solaris_ai_nn_live/memory_demo

Builds append-only membrane (boundary) memory across two updates for a couple of
sources, showing reliability and toxicity accumulation and that toxic history is
never deleted. Membrane memory is boundary memory, not cognition.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.environmental_membrane import MembraneMemory


def main():
    parser = argparse.ArgumentParser(description="Membrane memory demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/memory_demo")
    args = parser.parse_args()

    mem = MembraneMemory(state_dir=args.state_dir).load()
    # A reliable source accrues useful patterns.
    mem.update_source("run1", "machine_body", useful=5)
    # A toxic source accrues quarantine triggers (never silently forgiven).
    mem.update_source("run1", "mystery_source", quarantined=2,
                      operator_contamination=1)
    mem.update_source("run2", "mystery_source", quarantined=1)
    paths = mem.write()

    print("=== Membrane memory demo ===")
    idx = mem.index()
    print(f"  sources: {idx['membrane_memory_source_count']}; toxic: "
          f"{idx['toxic_source_count']}")
    for sid, m in idx["sources"].items():
        print(f"  {sid:<20} reliability={m['reliability']:.2f} "
              f"toxicity={m['toxicity']:.2f} quarantine={m['quarantine_count']} "
              f"review={m['recommend_review']}")
    print(f"  history entries: {len(mem.history)} (append-only; nothing deleted)")
    print(f"  memory: {paths['memory']}")
    print("note: membrane memory is boundary memory, not cognition. Toxic "
          "history is never deleted; a bad source is never silently forgiven.")


if __name__ == "__main__":
    main()
