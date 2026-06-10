#!/usr/bin/env python3
"""Combine result JSON files from an output dir into one Markdown report.

    python examples/generate_benchmark_report.py --output-dir .solaris_ai_nn_benchmarks
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.evaluation import (
    ExperimentResult,
    FailureAnalyzer,
    compare_plasticity_modes,
    compare_substrates,
)
from solaris_ai_nn.language.reporting import ExperimentReportBuilder


def main() -> None:
    parser = argparse.ArgumentParser(description="Combined benchmark report")
    parser.add_argument("--output-dir", type=str,
                        default=".solaris_ai_nn_benchmarks")
    args = parser.parse_args()

    out = Path(args.output_dir)
    result_files = sorted(out.glob("runs/*/result.json"))
    if not result_files:
        print(f"No result.json files found under {out}/runs/ -- run a "
              "benchmark first (examples/run_benchmark_suite.py).")
        return

    results = [ExperimentResult.from_dict(json.loads(p.read_text()))
               for p in result_files]
    analyzer = FailureAnalyzer()
    findings = {r.manifest.name: [f.to_dict() for f in analyzer.analyze_result(r)]
                for r in results}

    metric_rows = []
    score_rows = []
    for r in results:
        scores = (r.metrics.get("scores") or {}).get("domains", {})
        score_rows.append({r.manifest.name: {
            k: v["score"] for k, v in scores.items() if v["score"] is not None}})
        metric_rows.append({
            "name": r.manifest.name, "seed": r.manifest.seed,
            "substrate": r.manifest.substrate, "success": r.success,
            "duration_s": round(r.duration, 3),
            "repro_hash": r.reproducibility_hash,
        })

    report = (ExperimentReportBuilder(title="Combined benchmark report")
              .add_metadata(results=len(results), output_dir=str(out))
              .add_section("runs", metric_rows)
              .add_section("scorecards", score_rows)
              .add_section("substrate_comparison",
                           compare_substrates(results)["markdown"])
              .add_section("plasticity_comparison",
                           compare_plasticity_modes(results)["markdown"])
              .add_section("failure_findings",
                           findings or {"none": True})
              .build())
    md_path = out / "combined_report.md"
    md_path.write_text(report.to_markdown(), encoding="utf-8")
    (out / "combined_report.json").write_text(report.to_json(), encoding="utf-8")

    print(f"Combined report written: {md_path}")
    print("-" * 60)
    print("\n".join(report.to_markdown().splitlines()[:20]))


if __name__ == "__main__":
    main()
