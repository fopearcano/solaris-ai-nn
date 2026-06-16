#!/usr/bin/env python3
"""Live birth init demo: state layout + governance/feeder registry templates.

    python examples/run_live_birth_init_demo.py --state-dir .solaris_ai_nn_live/test_init

Initializes the live state layout and writes the SAFE-OFF governance template and
the feeder registry template (never over-writing existing files). The governance
template is disabled and unapproved by default; the operator must approve it.
Nothing is started, controlled, published, or sent.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.live_birth import LiveReadOnlyBirthRuntime


def main():
    parser = argparse.ArgumentParser(description="Live birth init demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/test_init")
    args = parser.parse_args()

    rt = LiveReadOnlyBirthRuntime(state_dir=args.state_dir)
    layout = rt.initialize()
    paths = rt.write_templates()

    print("=== Live birth init demo ===")
    print(f"  state dir            : {args.state_dir}")
    print(f"  directories created  : {len(layout['directories'])} "
          "(existing reused; none deleted)")
    print(f"  governance template  : {paths['governance']}")
    print(f"  feeder registry      : {paths['feeder_registry']}")
    print("  governance default   : SAFE-OFF (live_readonly_enabled=false, "
          "operator_approved=false)")
    print("note                   : the operator must explicitly approve "
          "governance before a live birth. Solaris never starts/controls "
          "feeders, hardware, network, Git/GitHub, shell, browser, or OS, and "
          "makes no consciousness/life/agency claim.")


if __name__ == "__main__":
    main()
