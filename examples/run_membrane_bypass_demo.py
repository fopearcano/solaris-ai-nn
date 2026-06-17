#!/usr/bin/env python3
"""Membrane bypass demo: raw-event bypass, missing impression ancestry, strict blocker.

    python examples/run_membrane_bypass_demo.py --state-dir .solaris_ai_nn_live/bypass_demo

Stages a pipeline whose proto-concept has NO impression ancestry (its source events
were never produced by the membrane), then runs the integration runtime in strict
enforced mode and prints the resulting bypass findings and blocker status.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.membrane_integration import (
    MembraneBypassDetector,
    MembraneIntegrationRuntime,
)
from run_membrane_integration_demo import stage_pipeline


def main():
    parser = argparse.ArgumentParser(description="Membrane bypass demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/bypass_demo")
    args = parser.parse_args()

    stage_pipeline(args.state_dir, include_bypass=True)
    rt = MembraneIntegrationRuntime(
        args.state_dir, profile="live_integration_enforced_v0")
    rt.run()
    summ = MembraneBypassDetector.summary(rt.bypass_findings)

    print("=== Membrane bypass demo (strict enforced) ===")
    print(f"  blocked             : {rt.blocked}")
    print(f"  bypass findings     : {summ['bypass_finding_count']} (worst "
          f"{summ['worst_severity']})")
    for f in summ["findings"]:
        print(f"    - [{f['severity']}] {f['finding']}: {f['detail']}")
    print(f"  pipeline status     : "
          f"{rt.audit.overall_status if rt.audit else 'unknown'}")
    print("note                  : in strict live mode a direct raw-event "
          "downstream path / missing impression ancestry is a blocker; no "
          "bypass is silently ignored.")


if __name__ == "__main__":
    main()
