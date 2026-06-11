#!/usr/bin/env python3
"""LLM report polish demo: wording may change; facts may not.

    python examples/run_llm_report_polish_demo.py

A deterministic report is built and saved, the mock adapter polishes it
(structure checks pass), a forced-unsafe adapter tries the same and is
rejected with its reasons named, and the audit log records every attempt
by hash.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.governance.compliance import ClaimGuard
from solaris_ai_nn.language.reporting import (
    ExperimentReportBuilder,
    save_polished_report,
)
from solaris_ai_nn.language.serialization import save_report
from solaris_ai_nn.llm_adapter import MockLLMAdapter, ReportPolisher
from solaris_ai_nn.llm_adapter.audit import LLMAuditLog


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM report polish demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/llm_report")
    args = parser.parse_args()
    state_dir = Path(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)

    report = (ExperimentReportBuilder(title="Session report")
              .add_metadata(steps=120, seed=7)
              .add_section("telemetry", {"steps": 120,
                                         "incident_count": 1})
              .add_section("warnings", ["WARNING: 1 incident recorded"])
              .build())
    md_path = state_dir / "session_report.md"
    save_report(report, state_dir / "session_report.json", md_path)

    print("=" * 70)
    print("Solaris-AI-NN -- LLM report polish demo")
    print("=" * 70)
    print(f"raw report saved: {md_path}")

    audit = LLMAuditLog(state_dir=state_dir)
    polisher = ReportPolisher(adapter=MockLLMAdapter(), audit=audit)
    result = save_polished_report(report, md_path, polisher=polisher)
    print(f"polish accepted: {result['accepted']}")
    print(f"polished report: {result['polished']}")
    if result["polished"]:
        polished = Path(result["polished"]).read_text()
        print(f"claim guard re-scan of polished file: "
              f"{ClaimGuard().is_safe(polished)}")
        print(f"headings preserved: "
              f"{'# Session report' in polished}")
    print()

    bad = ReportPolisher(adapter=MockLLMAdapter(force_unsafe_output=True),
                         audit=audit)
    rejected = bad.polish_markdown(report.to_markdown())
    print("forced-unsafe polish attempt:")
    print(f"  accepted: {rejected.accepted}")
    print(f"  reasons: {rejected.reasons[:2]}")
    print(f"  fell back to raw: "
          f"{rejected.text == report.to_markdown()}")
    print()
    print(f"audit log: {audit.path} ({audit.rows_written} row(s))")
    print("note: the raw deterministic report is always the source of "
          "truth; a polish that touches headings, numbers, warnings, or "
          "limitations is rejected outright.")


if __name__ == "__main__":
    main()
