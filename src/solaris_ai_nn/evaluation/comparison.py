"""Comparisons across substrates / feature configurations.

Each comparison groups results by a key and returns both a dict and a plain
Markdown pipe table (no table libraries). Statements stay numeric: the tables
show what the metrics show, nothing more.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple

from .benchmark import ExperimentResult


def _score_row(result: ExperimentResult) -> Dict[str, Any]:
    scores = (result.metrics.get("scores") or {}).get("domains", {})
    return {
        "name": result.manifest.name,
        "success": result.success,
        "adaptation": (scores.get("adaptation_score") or {}).get("score"),
        "reactivity": (scores.get("reactivity_score") or {}).get("score"),
        "continuity": (scores.get("continuity_score") or {}).get("score"),
        "duration_s": round(result.duration, 3),
    }


def _grouped(results: List[ExperimentResult],
             key: Callable[[ExperimentResult], str],
             label: str) -> Tuple[Dict[str, Any], str]:
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in results:
        groups.setdefault(key(r), []).append(_score_row(r))
    table = [f"| {label} | runs | succeeded | mean adaptation | mean duration_s |",
             "|---|---|---|---|---|"]
    for group, rows in sorted(groups.items()):
        adapt = [r["adaptation"] for r in rows if r["adaptation"] is not None]
        mean_adapt = f"{sum(adapt) / len(adapt):.3f}" if adapt else "n/a"
        mean_dur = sum(r["duration_s"] for r in rows) / len(rows)
        table.append(f"| {group} | {len(rows)} | "
                     f"{sum(1 for r in rows if r['success'])} | "
                     f"{mean_adapt} | {mean_dur:.3f} |")
    return {"groups": groups}, "\n".join(table)


def compare_substrates(results: List[ExperimentResult]) -> Dict[str, Any]:
    data, table = _grouped(results, lambda r: r.manifest.substrate, "substrate")
    return {**data, "markdown": table}


def compare_plasticity_modes(results: List[ExperimentResult]) -> Dict[str, Any]:
    data, table = _grouped(
        results,
        lambda r: "plasticity_on" if r.manifest.enabled_features.get("plasticity")
        else "plasticity_off", "plasticity")
    return {**data, "markdown": table}


def compare_embodied_vs_observe_only(results: List[ExperimentResult]) -> Dict[str, Any]:
    data, table = _grouped(
        results,
        lambda r: "embodied" if r.manifest.enabled_features.get("embodiment")
        else "observe_only", "mode")
    return {**data, "markdown": table}


def compare_language_enabled_vs_disabled(results: List[ExperimentResult]) -> Dict[str, Any]:
    data, table = _grouped(
        results,
        lambda r: "language_on" if r.manifest.enabled_features.get("language")
        else "language_off", "language")
    return {**data, "markdown": table}
