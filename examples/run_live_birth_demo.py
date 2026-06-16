#!/usr/bin/env python3
"""Live birth demo: bounded birth, accepted/quarantine, certificate, first contact.

    python examples/run_live_birth_demo.py --state-dir .solaris_ai_nn_live/test_demo --max-events 50

Sets up approved governance and the sample inbox, runs the bounded live read-only
birth runtime, and prints the accepted/quarantined counts, membrane activation,
first-contact markers, the birth certificate path, and the next recommended (not
executed) phases. Solaris never controls the source.
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
    parser = argparse.ArgumentParser(description="Live birth demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/test_demo")
    parser.add_argument("--max-events", type=int, default=50, dest="max_events")
    args = parser.parse_args()

    rt = LiveReadOnlyBirthRuntime(state_dir=args.state_dir,
                                  require_governance=True,
                                  max_events=args.max_events,
                                  operator_note="first bounded live read-only "
                                  "exposure (demo)")
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

    result = rt.run()
    st = rt.live_birth_status()

    print("=== Live read-only birth demo ===")
    print(f"  run id              : {st['birth_run_id']}")
    print(f"  governance          : {st['governance_status']} (passed "
          f"{st['governance_passed']})")
    print(f"  blocked             : {result['blocked']}")
    print(f"  events              : {st['live_event_count']} (accepted "
          f"{st['live_event_accepted_count']}, quarantined "
          f"{st['live_event_quarantined_count']})")
    print(f"  membrane activation : {st['membrane_activation_status']}")
    print(f"  first event id      : "
          f"{rt.membrane.get('first_event_id') or 'none'}")
    print(f"  first absence id    : "
          f"{rt.membrane.get('first_absence_event_id') or 'none'}")
    print(f"  first pulse id      : "
          f"{rt.membrane.get('first_operator_pulse_id') or 'none'}")
    print(f"  birth certificate   : {st['latest_birth_certificate_path']}")
    print(f"  starts feeders/net  : {st['starts_feeders']} / "
          f"{st['accesses_network']}")
    print("  next recommended phases (not executed):")
    for p in rt.next_phase_recommendations():
        print(f"    - {p['phase']}: {p['detail']}")
    print("note                  : this is an operational live-read-only birth. "
          "Solaris never controls the source, and it makes no claim of "
          "consciousness, life, or agency.")


if __name__ == "__main__":
    main()
