#!/usr/bin/env python3
"""Operator evidence-search demo: artifact + report index + local search.

    python examples/run_operator_evidence_search_demo.py --state-dir .solaris_ai_nn_operator/test_evidence

Writes a couple of local evidence artifacts, indexes artifacts and reports, and
runs a local keyword search. It searches local artifacts only -- no external
search, no vector DB, no LLM authority -- and reports corrupted artifacts.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.operator_console import (
    ArtifactIndexer,
    EvidenceNavigator,
    ReportIndexer,
)


def main():
    parser = argparse.ArgumentParser(description="Operator evidence-search demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_operator/test_evidence")
    args = parser.parse_args()
    base = args.state_dir
    os.makedirs(base, exist_ok=True)

    # Seed a couple of local evidence artifacts to find.
    with open(os.path.join(base, "research_report.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"summary": "baseline beat random on a safety proxy",
                   "evidence_refs": ["run:1", "run:2"]}, fh)
    with open(os.path.join(base, "SAFETY_INVARIANT_REPORT.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"status": "ok", "summary": "all invariants held"}, fh)

    artifacts = ArtifactIndexer([base]).index()
    reports = ReportIndexer([base]).index()
    nav = EvidenceNavigator([base])
    indexed = nav.index()
    results = nav.search("safety")

    print("=== Operator evidence-search demo ===")
    print(f"artifacts indexed     : {artifacts.to_dict()['artifact_count']}")
    print(f"corrupted artifacts   : {artifacts.to_dict()['corrupted_count']}")
    print(f"reports indexed       : {reports.to_dict()['report_count']}")
    print(f"evidence entries      : {indexed}")
    print(f"search 'safety' hits  : {len(results)}")
    if results:
        print(f"  first hit           : {results[0].title}")
        print(f"  evidence refs       : {results[0].evidence_refs}")
    print("note                  : local search only; no external/LLM search.")


if __name__ == "__main__":
    main()
