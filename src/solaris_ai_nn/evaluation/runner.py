"""BenchmarkRunner -- run experiments/suites with isolated state and reports.

Each run gets its own state directory under the output dir, executes strictly
bounded, writes `manifest.json` / `result.json` / `result.md` / `artifacts.json`
into `runs/<experiment_id>/`, and a suite produces `suite_summary.{json,md}`.
Failures are captured in results; the runner itself never raises for a failed
experiment and never leaves anything running.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..language.reporting import ExperimentReportBuilder
from ..utils.logging import get_logger
from .benchmark import BenchmarkSuite, ExperimentResult
from .experiment_registry import ExperimentRegistry
from .failure_analysis import FailureAnalyzer

logger = get_logger(__name__)

DEFAULT_OUTPUT_DIR = ".solaris_ai_nn_benchmarks"


@dataclass
class BenchmarkRunner:
    """Runs registered experiments and persists their evidence."""

    output_dir: str = DEFAULT_OUTPUT_DIR
    registry: ExperimentRegistry = field(default_factory=ExperimentRegistry)
    analyzer: FailureAnalyzer = field(default_factory=FailureAnalyzer)

    def run_experiment(self, name: str,
                       config: Optional[Dict[str, Any]] = None) -> ExperimentResult:
        """Run one bounded experiment; always returns a result."""
        manifest = self.registry.build_manifest(name, config)
        if not manifest.state_dir:
            manifest.state_dir = str(
                Path(self.output_dir) / "state" / manifest.experiment_id)
        protocol = self.registry.get(name)
        result = protocol(manifest)
        findings = self.analyzer.analyze_result(result)
        result.metrics["failure_findings"] = [f.to_dict() for f in findings]
        self._write_run(result)
        return result

    def run_suite(self, names: List[str],
                  config: Optional[Dict[str, Any]] = None) -> List[ExperimentResult]:
        """Run several experiments; failures never stop the suite."""
        results: List[ExperimentResult] = []
        for name in names:
            try:
                results.append(self.run_experiment(name, config))
            except ValueError as exc:  # unknown experiment / bad config
                logger.warning("skipping %s: %s", name, exc)
        self.save_results(results, self.output_dir)
        return results

    # -- persistence ----------------------------------------------------------

    def _write_run(self, result: ExperimentResult) -> str:
        run_dir = Path(self.output_dir) / "runs" / result.manifest.experiment_id
        run_dir.mkdir(parents=True, exist_ok=True)
        _write_json(run_dir / "manifest.json", result.manifest.to_dict())
        _write_json(run_dir / "result.json", result.to_dict())
        _write_json(run_dir / "artifacts.json", result.artifacts)
        (run_dir / "result.md").write_text(self._result_markdown(result),
                                           encoding="utf-8")
        return str(run_dir)

    def _result_markdown(self, result: ExperimentResult) -> str:
        builder = (ExperimentReportBuilder(
            title=f"Benchmark: {result.manifest.name}")
            .add_metadata(experiment_id=result.manifest.experiment_id,
                          seed=result.manifest.seed,
                          substrate=result.manifest.substrate,
                          success=result.success,
                          duration_s=round(result.duration, 3))
            .add_section("metrics", {
                k: v for k, v in result.metrics.items()
                if k not in ("scores", "failure_findings", "governance")})
            .add_section("scorecard", result.metrics.get("scores"))
            .add_section("governance", result.metrics.get("governance"))
            .add_section("failure_findings",
                         result.metrics.get("failure_findings") or
                         ["no findings"])
            .add_section("artifacts", result.artifacts or {"none": "collected"}))
        if result.error:
            builder.add_section("error", result.error)
        return builder.build().to_markdown()

    def save_results(self, results: List[ExperimentResult],
                     output_dir: Optional[str] = None) -> Dict[str, str]:
        """Write the suite summary (JSON + Markdown)."""
        out = Path(output_dir or self.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        suite = BenchmarkSuite(results=list(results))
        summary = self.summarize(results)
        _write_json(out / "suite_summary.json",
                    {"suite": suite.to_dict(), "summary": summary})
        md = (ExperimentReportBuilder(title="Benchmark suite summary")
              .add_metadata(experiments=len(results),
                            succeeded=suite.succeeded(),
                            failed=suite.failed())
              .add_section("experiments", summary["experiments"])
              .add_section("warnings", summary["warnings"] or ["none"])
              .build().to_markdown())
        (out / "suite_summary.md").write_text(md, encoding="utf-8")
        return {"json": str(out / "suite_summary.json"),
                "markdown": str(out / "suite_summary.md")}

    # -- aggregation ------------------------------------------------------------

    def summarize(self, results: List[ExperimentResult]) -> Dict[str, Any]:
        rows = []
        warnings: List[str] = []
        for r in results:
            scores = (r.metrics.get("scores") or {}).get("domains", {})
            available = {k: v["score"] for k, v in scores.items()
                         if v.get("score") is not None}
            rows.append({
                "name": r.manifest.name,
                "experiment_id": r.manifest.experiment_id,
                "success": r.success,
                "duration_s": round(r.duration, 3),
                "scores": available,
                "findings": len(r.metrics.get("failure_findings") or []),
            })
            warnings.extend(r.warnings[:2])
        return {"experiments": rows, "warnings": warnings[:20]}


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)
