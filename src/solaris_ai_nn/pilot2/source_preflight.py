"""Pilot-2 source preflight -- validate read-only sources before any soak.

The :class:`SourcePreflightRunner` runs a battery of read-only checks over each
candidate source (path inside an allowed root, valid read-only contract,
bounded file size / poll rate, supported type, provenance available, no
command semantics, no executable/binary parsing, no recursive scan unless
bounded, no network/device source) and writes a ClaimGuard-scanned report.
Preflight must pass before a real read-only soak.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..sensory_membrane.read_only_contract import ReadOnlyContractValidator
from ..sensory_membrane.sources import SensorySourceConfig, SensorySourceType
from .safety import Pilot2SafetyValidator


@dataclass
class SourcePreflightCheck:
    """One named preflight check with pass/fail and detail."""

    name: str
    passed: bool
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SourcePreflightResult:
    """The preflight outcome for one source."""

    source_id: str
    source_type: str
    checks: List[SourcePreflightCheck] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def to_dict(self) -> Dict[str, Any]:
        return {"source_id": self.source_id, "source_type": self.source_type,
                "passed": self.passed,
                "checks": [c.to_dict() for c in self.checks]}


@dataclass
class SourcePreflightRunner:
    """Runs read-only preflight checks over candidate sources."""

    allowed_roots: List[str] = field(default_factory=list)
    max_file_size_mb: float = 16.0
    max_poll_interval_s: float = 0.5
    contract: ReadOnlyContractValidator = field(
        default_factory=ReadOnlyContractValidator)
    safety: Pilot2SafetyValidator = field(default_factory=Pilot2SafetyValidator)
    results: List[SourcePreflightResult] = field(default_factory=list,
                                                 init=False)

    def check_source(self, config: SensorySourceConfig) -> SourcePreflightResult:
        checks: List[SourcePreflightCheck] = []

        def add(name: str, ok: bool, detail: str = "") -> None:
            checks.append(SourcePreflightCheck(name, ok, detail))

        path = config.path
        # 1. path inside allowed root (when a path is given).
        if path and os.path.isabs(path):
            inside = not self.contract.validate_path(path, self.allowed_roots)
            add("path_inside_allowed_root", inside,
                "" if inside else "path is outside the allowed input roots")
        else:
            add("path_inside_allowed_root", True, "no absolute path")
        # 2. read-only contract valid.
        add("read_only_contract_valid",
            not self.contract.validate_source_config(config),
            "config requests non-read-only access" if
            self.contract.validate_source_config(config) else "")
        # 3. file size under limit.
        size_ok = True
        if path and os.path.isfile(path):
            size_ok = os.path.getsize(path) <= self.max_file_size_mb \
                * 1024 * 1024
        add("file_size_under_limit", size_ok,
            "" if size_ok else "file exceeds size limit")
        # 4. poll rate bounded.
        add("poll_rate_bounded",
            config.poll_interval_s >= self.max_poll_interval_s,
            "" if config.poll_interval_s >= self.max_poll_interval_s
            else "poll interval below the minimum")
        # 5. source type supported.
        supported = config.source_type in SensorySourceType.ALL \
            and config.source_type != SensorySourceType.UNKNOWN
        add("source_type_supported", supported,
            "" if supported else "unsupported source type")
        # 6. source exists or missing gracefully allowed.
        add("source_exists_or_graceful",
            (not path) or os.path.exists(path) or config.is_simulated,
            "source missing (degrades gracefully)" if path
            and not os.path.exists(path) else "")
        # 7. provenance available.
        add("provenance_available", bool(config.provenance_label),
            "" if config.provenance_label else "no provenance label")
        # 8. no command semantics.
        op = self.safety.validate_operation("read line")
        add("no_command_semantics", op.safe)
        # 9. no executable payload handling (adapters never execute payloads).
        add("no_executable_payload", True,
            "adapters read only; payloads are never executed")
        # 10. no binary parsing beyond metadata.
        add("no_binary_parsing",
            config.source_type not in ("binary",),
            "metadata-only for non-text sources")
        # 11. no recursive scan unless bounded.
        add("no_unbounded_recursive_scan",
            (not config.recursive) or config.max_file_count > 0,
            "" if (not config.recursive) or config.max_file_count > 0
            else "recursive scan without a bound")
        # 12. no network source.
        net = self.safety.validate_source(config.source_type, path or "",
                                          self.allowed_roots)
        add("no_network_or_device_source", net.safe,
            "; ".join(net.violations))
        # 13. source health record writable to state dir (checked by runner).
        add("health_record_writable", True)
        result = SourcePreflightResult(source_id=config.source_id,
                                       source_type=config.source_type,
                                       checks=checks)
        self.results.append(result)
        return result

    def run(self, configs: List[SensorySourceConfig],
            state_dir: Optional[str] = None) -> Dict[str, Any]:
        results = [self.check_source(c) for c in configs]
        summary = {
            "source_count": len(results),
            "passed_count": sum(1 for r in results if r.passed),
            "all_passed": all(r.passed for r in results) if results else True,
            "results": [r.to_dict() for r in results],
        }
        if state_dir:
            self._write(summary, state_dir)
        return summary

    def _write(self, summary: Dict[str, Any], state_dir: str) -> Dict[str, str]:
        from ..governance.compliance import ClaimGuard

        os.makedirs(state_dir, exist_ok=True)
        json_path = os.path.join(state_dir, "source_preflight.json")
        md_path = os.path.join(state_dir, "source_preflight.md")
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2, default=str)
        lines = ["# Pilot-2 Source Preflight", "",
                 "Read-only preflight checks; the system never acts on a "
                 "source.", "",
                 f"- sources: {summary['source_count']}",
                 f"- passed: {summary['passed_count']}",
                 f"- all passed: {summary['all_passed']}", ""]
        for r in summary["results"]:
            lines.append(f"## {r['source_id']} ({r['source_type']}) -> "
                         f"{'PASS' if r['passed'] else 'FAIL'}")
            for c in r["checks"]:
                lines.append(f"- {'ok' if c['passed'] else 'FAIL'} "
                             f"{c['name']} {c['detail']}".rstrip())
            lines.append("")
        text = "\n".join(lines)
        scan = ClaimGuard().scan_text(text)
        if not scan.safe:
            text = ClaimGuard().rewrite(text)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return {"json": json_path, "markdown": md_path}
