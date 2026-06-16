#!/usr/bin/env python3
"""Theory ledger demo: working hypothesis, challenged, retired/falsified.

    python examples/run_theory_ledger_demo.py --state-dir .solaris_ai_nn_claims/test_theory_ledger

Records a working hypothesis, challenges it with counterevidence (preserving the
prior version), and retires/falsifies a third statement. Theory is a hypothesis
under evidence, never proof; revisions preserve prior versions and
retired/falsified statements stay archived.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.scientific_claims import (
    TheoryLedger,
    TheoryStatement,
    TheoryStatus,
)


def main():
    parser = argparse.ArgumentParser(description="Theory ledger demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_claims/test_theory_ledger")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    ledger = TheoryLedger()
    ledger.add(TheoryStatement(
        theory_id="t_sensorium",
        area="sensorium-shaped cognition",
        text="Sensorium structure shapes downstream representation.",
        status=TheoryStatus.WORKING_HYPOTHESIS,
        evidence_refs=["sensorium_diff_run_3"]))
    ledger.add(TheoryStatement(
        theory_id="t_metabolism", area="perceptual metabolism",
        text="Perceptual metabolism regulates representational load.",
        status=TheoryStatus.WEAKLY_SUPPORTED))
    ledger.add(TheoryStatement(
        theory_id="t_overclaim", area="long-horizon development",
        text="Long-horizon growth reflects development.",
        status=TheoryStatus.WORKING_HYPOTHESIS))

    # Challenge the first hypothesis with counterevidence (prior version kept).
    ledger.revise("t_sensorium",
                  text="Sensorium structure may shape representation, but a "
                       "passive parser produced a similar structure.",
                  status=TheoryStatus.CHALLENGED,
                  counterevidence_refs=["passive_parser_equivalence"])
    # Retire/falsify the third statement.
    ledger.revise("t_overclaim",
                  text="Long-horizon growth was indistinguishable from log "
                       "accumulation; the developmental reading is retired.",
                  status=TheoryStatus.FALSIFIED,
                  counterevidence_refs=["log_accumulation_warning"])

    d = ledger.to_dict()
    print("=== Theory ledger demo ===")
    print(f"  statements : {d['theory_statement_count']} "
          f"(challenged {d['challenged_count']}, falsified {d['falsified_count']}, "
          f"retired {d['retired_count']})")
    for s in d["statements"]:
        print(f"    - [{s['status']}] ({s['area']}) {s['text'][:60]} "
              f"-- {s['revision_count']} revision(s), archived={s['archived']}")
    print("note       : theory is a hypothesis under evidence, not proof. "
          "Revisions preserve prior versions and retired/falsified statements "
          "remain archived.")


if __name__ == "__main__":
    main()
