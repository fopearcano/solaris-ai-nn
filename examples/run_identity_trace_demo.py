#!/usr/bin/env python3
"""Identity trace demo: operational identity trace, restart/gap, no personhood.

    python examples/run_identity_trace_demo.py --state-dir .solaris_ai_nn_self_boundary/test_identity_trace

Records an operational identity trace with a run identity and a restart/gap event,
and shows that identity is continuity metadata, NOT personhood.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.self_boundary import IdentityTraceEventType, IdentityTraceStore


def main():
    parser = argparse.ArgumentParser(description="Identity trace demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_self_boundary/test_identity_trace")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    store = IdentityTraceStore(state_dir=args.state_dir)
    store.record_event(IdentityTraceEventType.RUN_IDENTITY,
                       {"run_id": store.trace.run_id})
    store.record_event(IdentityTraceEventType.RESTART,
                       {"detail": "process restarted; state reloaded"})
    store.record_event(IdentityTraceEventType.MEMORY_GAP,
                       {"detail": "gap between last tick and restart"})
    store.trace.active_receptors = ["rf_recv", "vib_recv"]
    store.trace.stable_signs = ["rf:01"]

    print("=== Identity trace demo ===")
    print(f"run id                : {store.trace.run_id}")
    print(f"identity events       : {store.event_count()}")
    print(f"restart events        : {store.trace.restart_events}")
    print(f"memory gaps           : {store.trace.memory_gaps}")
    print(f"active receptors      : {store.trace.active_receptors}")
    print(f"trace file written    : "
          f"{os.path.isfile(os.path.join(args.state_dir, 'identity_trace.jsonl'))}")
    print("note: the identity trace is operational continuity metadata, not "
          "personal identity; no personhood, self-awareness, or subjective "
          "experience is implied.")


if __name__ == "__main__":
    main()
