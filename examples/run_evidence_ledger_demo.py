#!/usr/bin/env python3
"""Evidence continuity ledger demo: append-only; failures are preserved.

    python examples/run_evidence_ledger_demo.py --state-dir .solaris_ai_nn_research_cycle/test_ledger

Records baseline / post-merge / falsified / missing / negative evidence in the
append-only evidence ledger, then supersedes a stale baseline entry. Negative,
falsified, and missing evidence are preserved (never deleted); stale evidence is
marked superseded, never removed.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.research_cycle import (
    EvidenceContinuityLedger,
    EvidenceLedgerEntryType,
)


def main():
    parser = argparse.ArgumentParser(description="Evidence ledger demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_research_cycle/test_ledger")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    ledger = EvidenceContinuityLedger(state_dir=args.state_dir)
    ledger.add(EvidenceLedgerEntryType.BASELINE, summary="baseline v1 evidence",
               artifact_ref="research_baseline", cycle_id="cycle_1")
    ledger.add(EvidenceLedgerEntryType.POST_MERGE, summary="post-merge evidence",
               artifact_ref="post_merge", cycle_id="cycle_1")
    ledger.add(EvidenceLedgerEntryType.FALSIFICATION,
               summary="a core claim was falsified", cycle_id="cycle_1")
    ledger.add(EvidenceLedgerEntryType.NEGATIVE,
               summary="module had no measurable effect", cycle_id="cycle_1")
    ledger.add(EvidenceLedgerEntryType.MISSING,
               summary="soak evidence missing", artifact_ref="soak",
               cycle_id="cycle_1")

    print("=== Evidence ledger (before supersede) ===")
    index = ledger.index()
    for k in ("evidence_ledger_entry_count", "negative_evidence_entry_count",
              "falsified_evidence_entry_count", "missing_evidence_entry_count",
              "superseded_count", "append_only"):
        print(f"  {k}: {index[k]}")

    superseded = ledger.supersede(EvidenceLedgerEntryType.BASELINE)
    ledger.add(EvidenceLedgerEntryType.BASELINE, summary="baseline v2 evidence",
               artifact_ref="research_baseline", cycle_id="cycle_2")

    print(f"\nsuperseded {superseded} stale baseline entry(ies); added baseline v2")
    print("=== Evidence ledger (after supersede) ===")
    index = ledger.index()
    for k in ("evidence_ledger_entry_count", "superseded_count"):
        print(f"  {k}: {index[k]}")
    print(f"  entry counts by type: {ledger.counts()}")
    print("\nnote: the ledger is append-only. Negative, falsified, and missing "
          "evidence are preserved; stale evidence is marked superseded, never "
          "deleted.")


if __name__ == "__main__":
    main()
