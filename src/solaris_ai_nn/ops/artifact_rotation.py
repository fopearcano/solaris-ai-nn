"""ArtifactRotationPolicy -- bounded evidence, never destroyed evidence.

Rotation compresses large JSONL logs (stdlib gzip) and trims *only* rotated
archives beyond a keep-count — always strictly inside the configured
directories. Hard safety: every candidate path is resolved and verified to be
inside an allowed directory; source files (``*.py``) are never touched; dry-run
shows exactly what would happen.
"""

from __future__ import annotations

import gzip
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Union

PROTECTED_SUFFIXES = (".py",)


def _inside(path: Path, allowed: List[Path]) -> bool:
    resolved = path.resolve()
    for base in allowed:
        try:
            resolved.relative_to(base.resolve())
            return True
        except ValueError:
            continue
    return False


@dataclass
class ArtifactRotationPolicy:
    """Compress big JSONL logs; keep only the newest N archives per name."""

    directories: List[Union[str, Path]]
    keep_archives: int = 3
    compress_jsonl_over_bytes: int = 256 * 1024
    report: Dict[str, Any] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._allowed = [Path(d) for d in self.directories]

    # -- planning -------------------------------------------------------------

    def scan(self) -> Dict[str, List[str]]:
        """What rotation would touch: {'compress': [...], 'trim': [...]}"""
        compress: List[str] = []
        trim: List[str] = []
        for base in self._allowed:
            if not base.exists():
                continue
            for path in base.rglob("*.jsonl"):
                if not self._safe_target(path):
                    continue
                if path.stat().st_size >= self.compress_jsonl_over_bytes:
                    compress.append(str(path))
            # Archives grouped by original name; oldest beyond keep are trimmed.
            archives: Dict[str, List[Path]] = {}
            for path in base.rglob("*.jsonl.*.gz"):
                if self._safe_target(path):
                    stem = path.name.split(".jsonl.")[0]
                    archives.setdefault(f"{path.parent}/{stem}", []).append(path)
            for group in archives.values():
                group.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                trim.extend(str(p) for p in group[self.keep_archives:])
        return {"compress": compress, "trim": trim}

    def _safe_target(self, path: Path) -> bool:
        if path.suffix in PROTECTED_SUFFIXES or path.name.endswith(".py"):
            return False
        return _inside(path, self._allowed)

    # -- execution --------------------------------------------------------------

    def dry_run(self) -> Dict[str, Any]:
        """Report what rotation would do, changing nothing."""
        plan = self.scan()
        self.report = {"dry_run": True, "timestamp": time.time(),
                       "would_compress": plan["compress"],
                       "would_trim": plan["trim"], "errors": []}
        return self.report

    def rotate(self) -> Dict[str, Any]:
        """Compress + trim inside allowed directories only."""
        plan = self.scan()
        compressed: List[str] = []
        trimmed: List[str] = []
        errors: List[str] = []
        stamp = time.strftime("%Y%m%d%H%M%S")
        for raw in plan["compress"]:
            path = Path(raw)
            if not self._safe_target(path):  # defense in depth
                errors.append(f"refused (outside allowed dirs): {path}")
                continue
            target = path.with_name(f"{path.stem}.jsonl.{stamp}.gz")
            try:
                with open(path, "rb") as src, gzip.open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                path.write_text("", encoding="utf-8")  # truncate, keep the file
                compressed.append(str(target))
            except OSError as exc:
                errors.append(f"compress failed for {path}: {exc}")
        for raw in plan["trim"]:
            path = Path(raw)
            if not self._safe_target(path):
                errors.append(f"refused (outside allowed dirs): {path}")
                continue
            try:
                path.unlink()
                trimmed.append(str(path))
            except OSError as exc:
                errors.append(f"trim failed for {path}: {exc}")
        self.report = {"dry_run": False, "timestamp": time.time(),
                       "compressed": compressed, "trimmed": trimmed,
                       "errors": errors}
        return self.report

    def to_dict(self) -> Dict[str, Any]:
        return {
            "directories": [str(d) for d in self._allowed],
            "keep_archives": self.keep_archives,
            "compress_jsonl_over_bytes": self.compress_jsonl_over_bytes,
            "last_report": dict(self.report),
        }
