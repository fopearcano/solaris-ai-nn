#!/usr/bin/env python3
"""Alpha module registry demo: available, missing, optional-missing, blocked.

    python examples/run_alpha_module_registry_demo.py --state-dir .solaris_ai_nn_alpha/test_registry

Builds the real module registry (import-spec only; no module is executed), then
illustrates the four statuses with synthetic edits so the demo is self-contained:
an available module, a missing required module, an optional-missing module, and a
blocked module. The registry never crashes on a missing module.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.alpha_system import AlphaModuleRegistry, AlphaModuleStatus


def main():
    parser = argparse.ArgumentParser(description="Alpha module registry demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_alpha/test_registry")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    registry = AlphaModuleRegistry.build()
    idx = registry.index()
    print("=== Alpha module registry demo ===")
    print(f"  modules: {idx['alpha_module_count']} "
          f"(available {idx['alpha_available_module_count']}, missing "
          f"{idx['alpha_missing_module_count']}, optional-missing "
          f"{idx['alpha_optional_missing_count']}, blocked "
          f"{idx['alpha_blocked_module_count']})")

    # Illustrate the four statuses with synthetic edits (self-contained).
    examples = {
        AlphaModuleStatus.AVAILABLE: "scientific_claims",
        AlphaModuleStatus.MISSING: "safety_invariants",        # required
        AlphaModuleStatus.OPTIONAL_MISSING: "live_field",       # optional
        AlphaModuleStatus.BLOCKED: "architecture_evolution",
    }
    print("\n  status illustrations:")
    for status, key in examples.items():
        rec = registry.get(key)
        if rec is None:
            continue
        rec.status = status
        rec.detail = f"illustration: {status}"
        print(f"    [{rec.status}] {rec.label} "
              f"(required={rec.required_for_alpha}, "
              f"blocks_alpha={rec.blocks_alpha})")
    print("note: module presence is checked by import-spec only; no module is "
          "executed; a missing required module blocks the specific command, not "
          "the whole CLI, and missing optional modules warn.")


if __name__ == "__main__":
    main()
