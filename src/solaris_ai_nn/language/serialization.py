"""Persistence helpers for language artifacts -- JSONL/JSON/Markdown only.

Traces are truncated to a safe maximum before writing (bounded-memory mode);
nothing here stores huge raw payloads by default.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .schemas import CausalTrace, Explanation, MeaningTrace

DEFAULT_MAX_ATOMS = 1_000


def save_meaning_trace(trace: MeaningTrace, path: Union[str, Path],
                       max_atoms: int = DEFAULT_MAX_ATOMS) -> int:
    """Write a (truncated) meaning trace as JSONL; returns rows written."""
    from ..runtime.persistence import JsonlWriter  # local: avoid cycles

    atoms = trace.atoms[-max_atoms:] if max_atoms > 0 else trace.atoms
    with JsonlWriter(path) as writer:
        for a in atoms:
            writer.write(a.to_dict())
    return len(atoms)


def load_meaning_trace_rows(path: Union[str, Path]) -> List[Dict[str, Any]]:
    from ..runtime.persistence import read_jsonl

    if not Path(path).exists():
        return []
    return list(read_jsonl(path))


def save_causal_trace(trace: CausalTrace, path: Union[str, Path]) -> None:
    _write_json(path, trace.to_dict())


def save_explanations(explanations: Dict[str, Explanation],
                      path: Union[str, Path]) -> None:
    _write_json(path, {name: e.to_dict() for name, e in explanations.items()})


def save_report(report, json_path: Union[str, Path],
                md_path: Union[str, Path],
                claim_guard=None, on_unsafe: str = "annotate"):
    """Persist a SessionReport as JSON + Markdown, ClaimGuard-scanned.

    Every report is scanned before save. If unsupported claims are found:

    * ``on_unsafe="annotate"`` (default): the Markdown gains a
      "Claim Guard Warnings" section and the JSON a ``claim_guard`` entry;
    * ``on_unsafe="block"``: nothing is written and ``ValueError`` is raised.

    Returns the :class:`ClaimGuardReport` of the scan.
    """
    from ..governance.compliance import ClaimGuard  # local: avoid cycles

    guard = claim_guard or ClaimGuard()
    markdown = report.to_markdown()
    scan = guard.scan_text(markdown)
    if not scan.safe:
        if on_unsafe == "block":
            raise ValueError(
                f"report blocked: {len(scan.findings)} unsupported claim(s); "
                + "; ".join(guard.suggest_replacements(markdown)))
        markdown = markdown + "\n" + guard.warning_section(scan)
    data = report.to_dict()
    data["claim_guard"] = scan.to_dict()
    _write_json(json_path, data)
    md_path = Path(md_path)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(markdown, encoding="utf-8")
    return scan


def _write_json(path: Union[str, Path], data: Dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)
