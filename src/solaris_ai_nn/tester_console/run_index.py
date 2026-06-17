"""Console run index -- a persistent, append-only index of discovered runs.

:class:`TesterRunIndex` records one :class:`TesterRunRecord` per discovered run (fixture,
live, membrane, observation, …) with its status, report/bundle paths, blocker/warning
counts, and safety/membrane/reproducibility/regression status. Old runs are preserved;
the latest run is clearly marked.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List


class RunType:
    ALPHA_FIXTURE = "alpha_fixture"
    TESTER_FIXTURE = "tester_fixture"
    TESTER_LIVE = "tester_live"
    LIVE_BIRTH = "live_birth"
    MEMBRANE = "membrane"
    OBSERVATION = "observation"
    ONTOGENESIS = "ontogenesis"
    SEMIOGENESIS = "semiogenesis"
    COGNITION = "cognition"
    DOCS = "docs"
    UNKNOWN = "unknown"

    ALL = (ALPHA_FIXTURE, TESTER_FIXTURE, TESTER_LIVE, LIVE_BIRTH, MEMBRANE,
           OBSERVATION, ONTOGENESIS, SEMIOGENESIS, COGNITION, DOCS, UNKNOWN)


@dataclass
class TesterRunRecord:
    """One run record in the console run index."""

    run_id: str
    run_type: str = RunType.UNKNOWN
    created: float = 0.0
    profile: str = ""
    state_root: str = ""
    status: str = "unknown"
    report_paths: List[str] = field(default_factory=list)
    bundle_paths: List[str] = field(default_factory=list)
    blocker_count: int = 0
    warning_count: int = 0
    safety_status: str = "unknown"
    membrane_status: str = "unknown"
    reproducibility_status: str = "unknown"
    regression_status: str = "unknown"
    latest: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id, "run_type": self.run_type,
            "created": self.created, "profile": self.profile,
            "state_root": self.state_root, "status": self.status,
            "report_paths": list(self.report_paths),
            "bundle_paths": list(self.bundle_paths),
            "blocker_count": self.blocker_count,
            "warning_count": self.warning_count,
            "safety_status": self.safety_status,
            "membrane_status": self.membrane_status,
            "reproducibility_status": self.reproducibility_status,
            "regression_status": self.regression_status,
            "latest": self.latest,
        }


@dataclass
class TesterRunIndex:
    """The persistent console run index (append-only; old runs preserved)."""

    runs: List[TesterRunRecord] = field(default_factory=list)

    def upsert(self, record: TesterRunRecord) -> None:
        for i, existing in enumerate(self.runs):
            if existing.run_id == record.run_id:
                self.runs[i] = record
                return
        self.runs.append(record)

    def mark_latest(self) -> None:
        for r in self.runs:
            r.latest = False
        if self.runs:
            newest = max(self.runs, key=lambda r: r.created)
            newest.latest = True

    def to_dict(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for r in self.runs:
            types[r.run_type] = types.get(r.run_type, 0) + 1
        return {
            "run_count": len(self.runs),
            "by_type": types,
            "latest_run_id": next((r.run_id for r in self.runs if r.latest), ""),
            "runs": [r.to_dict() for r in sorted(
                self.runs, key=lambda r: r.created, reverse=True)],
            "note": "append-only run index; old runs are preserved and the "
                    "latest run is marked",
        }

    def to_markdown(self) -> str:
        d = self.to_dict()
        lines = ["# Tester Run Index", "",
                 f"- runs: {d['run_count']}; latest: {d['latest_run_id']}", "",
                 "| run id | type | status | safety | membrane | repro | "
                 "regression | latest |",
                 "| --- | --- | --- | --- | --- | --- | --- | --- |"]
        for r in d["runs"]:
            lines.append(
                f"| {r['run_id']} | {r['run_type']} | {r['status']} | "
                f"{r['safety_status']} | {r['membrane_status']} | "
                f"{r['reproducibility_status']} | {r['regression_status']} | "
                f"{'yes' if r['latest'] else ''} |")
        lines += ["", "_Old runs are preserved; the latest run is marked._"]
        return "\n".join(lines)


@dataclass
class RunIndexBuilder:
    """Builds (and persists) the run index from the discovery result."""

    def build(self, discovery) -> TesterRunIndex:
        from .artifact_discovery import ArtifactKind as K

        index = TesterRunIndex()

        for art in discovery.by_kind(K.TESTER_FIXTURE_REPORT):
            rid = art.summary.get("tester_run_id") or _run_id_from_name(
                art.path, ("TESTER_DEMO_REPORT_", "TESTER_RUN_SUMMARY_"))
            index.upsert(TesterRunRecord(
                run_id=rid, run_type=RunType.TESTER_FIXTURE,
                created=art.summary.get("_mtime", 0.0),
                state_root=art.state_root, status="present",
                report_paths=[art.path],
                reproducibility_status=art.summary.get(
                    "reproducibility_status", "unknown"),
                regression_status=art.summary.get("regression_status",
                                                  "unknown"),
                safety_status="ok"))

        for art in discovery.by_kind(K.TESTER_LIVE_REPORT):
            rid = art.summary.get("tester_live_run_id") or _run_id_from_name(
                art.path, ("TESTER_LIVE_RUN_SUMMARY_",
                           "TESTER_LIVE_READONLY_REPORT_"))
            index.upsert(TesterRunRecord(
                run_id=rid, run_type=RunType.TESTER_LIVE,
                created=art.summary.get("_mtime", 0.0),
                state_root=art.state_root, status="present",
                report_paths=[art.path],
                membrane_status="present" if art.summary.get(
                    "membrane_impression_count") else "unknown"))

        for kind, rtype in ((K.LIVE_BIRTH_REPORT, RunType.LIVE_BIRTH),
                            (K.MEMBRANE_REPORT, RunType.MEMBRANE),
                            (K.OBSERVATION_REPORT, RunType.OBSERVATION),
                            (K.CONCEPT_MEMORY, RunType.ONTOGENESIS),
                            (K.SIGN_MEMORY, RunType.SEMIOGENESIS),
                            (K.COGNITION_MEMORY, RunType.COGNITION),
                            (K.ALPHA_REPORT, RunType.ALPHA_FIXTURE)):
            for art in discovery.by_kind(kind):
                rid = f"{rtype}_{_stem(art.path)}"
                index.upsert(TesterRunRecord(
                    run_id=rid, run_type=rtype,
                    created=art.summary.get("_mtime", 0.0),
                    state_root=art.state_root, status="present",
                    report_paths=[art.path]))

        index.mark_latest()
        return index

    def write(self, index: TesterRunIndex, console_dir: str) -> Dict[str, str]:
        base = os.path.join(console_dir, "index")
        os.makedirs(base, exist_ok=True)
        json_path = os.path.join(base, "TESTER_RUN_INDEX.json")
        md_path = os.path.join(base, "TESTER_RUN_INDEX.md")
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(index.to_dict(), fh, indent=2, default=str)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(index.to_markdown())
        return {"json": json_path, "markdown": md_path}


def _stem(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def _run_id_from_name(path: str, prefixes: tuple) -> str:
    stem = _stem(path)
    for prefix in prefixes:
        if stem.startswith(prefix):
            return stem[len(prefix):]
    return stem
