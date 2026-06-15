#!/usr/bin/env python3
"""Architecture inventory demo: catalogue modules and mark safety-critical ones.

    python examples/run_architecture_inventory_demo.py --state-dir .solaris_ai_nn_architecture/test_inventory

Builds the module inventory, reports available vs unavailable packages, and marks
the safety-critical modules that can never be pruned on performance evidence
alone. This is analysis only; no source code is touched.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.architecture_evolution import ModuleInventory


def main():
    parser = argparse.ArgumentParser(description="Architecture inventory demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_architecture/test_inventory")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    inv = ModuleInventory()
    snap = inv.snapshot()
    path = os.path.join(args.state_dir, "module_inventory.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(inv.to_dict(), fh, indent=2, default=str)

    print("=== Architecture inventory demo ===")
    print(f"modules catalogued    : {snap['module_count']}")
    print(f"available             : {snap['available_count']}")
    print(f"unavailable           : {snap['unavailable']}")
    print(f"safety-critical (no perf-pruning): {len(snap['safety_critical'])}")
    print(f"  {snap['safety_critical']}")
    print(f"written               : {path}")
    print("note                  : analysis only; no source code is modified.")


if __name__ == "__main__":
    main()
