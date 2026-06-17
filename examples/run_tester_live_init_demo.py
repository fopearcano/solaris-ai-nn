#!/usr/bin/env python3
"""Tester live init demo: generate templates + state layout (no live run).

    python examples/run_tester_live_init_demo.py \\
        --state-dir .solaris_ai_nn_live/test_live_init \\
        --tester-state-dir .solaris_ai_nn_tester/live/test_live_init

Writes the SAFE-OFF governance template, the feeder registry template, the safe/unsafe
event packs, and the checklist, and runs the live tester doctor. It performs no live
run; Solaris starts no feeder.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_live_readonly import TesterLiveReadOnlyRuntime


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state-dir", default=".solaris_ai_nn_live/test_live_init")
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/live/test_live_init")
    args = ap.parse_args()

    rt = TesterLiveReadOnlyRuntime(
        state_dir=args.state_dir, tester_state_dir=args.tester_state_dir,
        profile="tester_live_init_only_v0", write_templates=True)
    result = rt.run()
    st = rt.tester_live_status()
    print("tester live init demo")
    print(f"  run id            : {st['tester_live_run_id']}")
    print(f"  governance        : {st['governance_status']} (edit by hand to "
          "enable)")
    print(f"  feeder registry   : present={st['feeder_registry_present']}")
    print(f"  live doctor       : {st['live_doctor_status']}")
    print(f"  templates written : {rt.template_results}")
    for step in result["recommended_next_steps"]:
        print(f"  next              : {step}")
    print("note: no live run; Solaris started no feeder and controls nothing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
