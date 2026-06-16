#!/usr/bin/env python3
"""Live event validation demo: valid accepted, unsafe quarantined, report.

    python examples/run_live_birth_event_validation_demo.py --state-dir .solaris_ai_nn_live/test_validation

Copies the bundled safe and unsafe sample events into the inbox, runs the bounded
birth runtime under approved governance, and prints the accepted/quarantined counts
and quarantine reasons. Validation never modifies the original event; unsafe events
are quarantined as evidence, not deleted.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.live_birth import (
    LiveReadOnlyBirthRuntime,
    approved_governance,
    feeder_registry_template,
)

_SAMPLE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "live_birth", "sample_inbox")


def main():
    parser = argparse.ArgumentParser(description="Live event validation demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/test_validation")
    args = parser.parse_args()

    rt = LiveReadOnlyBirthRuntime(state_dir=args.state_dir,
                                  require_governance=True)
    rt.initialize()
    with open(os.path.join(args.state_dir, "governance",
                           "LIVE_READONLY_GOVERNANCE.json"), "w") as fh:
        json.dump(approved_governance(), fh)
    with open(os.path.join(args.state_dir, "feeders", "FEEDER_REGISTRY.json"),
              "w") as fh:
        json.dump(feeder_registry_template(), fh)
    for fn in ("birth_events.jsonl", "unsafe_events.jsonl"):
        src = os.path.join(_SAMPLE, fn)
        if os.path.isfile(src):
            shutil.copy(src, os.path.join(args.state_dir, "inbox", fn))

    rt.run()
    st = rt.live_birth_status()
    q = rt.quarantine.index() if rt.quarantine else {}

    print("=== Live event validation demo ===")
    print(f"  events     : {st['live_event_count']}")
    print(f"  accepted   : {st['live_event_accepted_count']}")
    print(f"  quarantined: {st['live_event_quarantined_count']}")
    print("  quarantine reasons:")
    for reason, count in (q.get("reasons", {}) or {}).items():
        print(f"    - {reason}: {count}")
    print(f"  validation report: "
          f"{os.path.join(args.state_dir, 'reports', 'LIVE_EVENT_VALIDATION_REPORT.md')}")
    print("note       : validation never modifies the original event; unsafe "
          "events are quarantined as evidence, not deleted, and never enter the "
          "sensory membrane.")


if __name__ == "__main__":
    main()
