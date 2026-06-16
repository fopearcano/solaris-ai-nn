#!/usr/bin/env python3
"""Response ledger demo: objection, partial answer, accepted limitation, unresolved.

    python examples/run_response_ledger_demo.py --state-dir .solaris_ai_nn_review/test_response_ledger

Records three reviewer objections, then responds: one partially answered (citing
evidence), one accepted as a limitation, and one left unresolved. The ledger is
append-only -- objections cannot be deleted, accepted limitations stay visible, and
the system cannot declare victory over a reviewer by default.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.independent_review import (
    ObjectionStatus,
    ReviewerObjection,
    ReviewerResponse,
    ReviewerResponseLedger,
)


def main():
    parser = argparse.ArgumentParser(description="Response ledger demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_review/test_response_ledger")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    ledger = ReviewerResponseLedger(state_dir=args.state_dir)
    ledger.add_objection(ReviewerObjection(
        objection_id="o1", text="Could this be fixture overfit?",
        claim_refs=["c1"]))
    ledger.add_objection(ReviewerObjection(
        objection_id="o2", text="No live-field replication is shown.",
        claim_refs=["c1"]))
    ledger.add_objection(ReviewerObjection(
        objection_id="o3", text="Could the result be log accumulation?",
        claim_refs=["c2"]))

    ledger.respond("o1", ReviewerResponse(
        text="Partially addressed by the ablation control; held-out fixtures "
             "still pending.",
        evidence_refs=["replication_matrix"]),
        status=ObjectionStatus.PARTIALLY_ANSWERED)
    ledger.respond("o2", ReviewerResponse(
        text="Accepted: no live-field replication exists yet; recorded as a "
             "limitation.",
        admits_missing_evidence=True),
        status=ObjectionStatus.ACCEPTED_AS_LIMITATION)
    ledger.respond("o3", ReviewerResponse(
        text="Acknowledged; a growth-vs-log-size check is required before this "
             "can be answered.",
        admits_missing_evidence=True),
        status=ObjectionStatus.UNRESOLVED)

    d = ledger.to_dict()
    print("=== Response ledger demo ===")
    print(f"  objections           : {d['objection_count']}")
    print(f"  open                 : {d['open_objection_count']}")
    print(f"  unresolved           : {d['unresolved_objection_count']}")
    print(f"  accepted limitations : {d['accepted_limitation_count']}")
    for o in d["objections"]:
        print(f"    - [{o['status']}] {o['text']} "
              f"({o['response_count']} response(s))")
    print("note                   : the ledger is append-only. Objections cannot "
          "be deleted, accepted limitations stay visible, responses cite "
          "evidence or admit its absence, and the system cannot declare victory "
          "over a reviewer by default.")


if __name__ == "__main__":
    main()
