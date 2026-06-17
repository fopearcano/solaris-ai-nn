"""Tester dependency check -- read-only dependency readiness (installs nothing).

:class:`DependencyCheck` checks the Python version, the importability of required and
optional packages, the pyproject metadata, and editable-install support. A missing
required dependency is a blocker; a missing optional/dev/feeder/docs dependency is a
warning. The check installs nothing and provides clear install instructions instead.
"""

from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

_MIN_PYTHON = (3, 11)


class DependencyKind:
    REQUIRED = "required"
    DEV = "dev"
    OPTIONAL = "optional"
    EXTERNAL_FEEDER_OPTIONAL = "external_feeder_optional"
    DOCS_OPTIONAL = "docs_optional"
    UNKNOWN = "unknown"

    ALL = (REQUIRED, DEV, OPTIONAL, EXTERNAL_FEEDER_OPTIONAL, DOCS_OPTIONAL,
           UNKNOWN)


# (module, kind, install_hint)
_DEPENDENCIES: Tuple[Tuple[str, str, str], ...] = (
    ("numpy", DependencyKind.REQUIRED, "pip install -e ."),
    ("solaris_ai_nn", DependencyKind.REQUIRED, "pip install -e ."),
    ("pytest", DependencyKind.DEV, "pip install -e '.[test]'"),
    ("psutil", DependencyKind.EXTERNAL_FEEDER_OPTIONAL,
     "optional: pip install psutil (only for the machine_body feeder example)"),
)


@dataclass
class DependencyFinding:
    """One dependency finding."""

    name: str
    kind: str
    available: bool
    detail: str = ""
    install_hint: str = ""

    @property
    def blocking(self) -> bool:
        return self.kind == DependencyKind.REQUIRED and not self.available

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "kind": self.kind,
                "available": self.available, "detail": self.detail,
                "install_hint": self.install_hint, "blocking": self.blocking}


@dataclass
class DependencyCheckResult:
    """The aggregate dependency check result (read-only; installs nothing)."""

    findings: List[DependencyFinding] = field(default_factory=list)
    python_ok: bool = True
    python_version: str = ""
    editable_install: bool = False
    pyproject_present: bool = False

    @property
    def blockers(self) -> List[DependencyFinding]:
        out = [f for f in self.findings if f.blocking]
        return out

    @property
    def warnings(self) -> List[DependencyFinding]:
        return [f for f in self.findings
                if not f.available and not f.blocking]

    @property
    def passed(self) -> bool:
        return self.python_ok and not self.blockers

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "python_ok": self.python_ok,
            "python_version": self.python_version,
            "editable_install": self.editable_install,
            "pyproject_present": self.pyproject_present,
            "finding_count": len(self.findings),
            "blocker_count": len(self.blockers),
            "warning_count": len(self.warnings),
            "findings": [f.to_dict() for f in self.findings],
            "installs_anything": False,
            "note": "read-only dependency check; it installs nothing and "
                    "provides install instructions instead",
        }


@dataclass
class DependencyCheck:
    """Read-only dependency readiness check (installs nothing)."""

    include_dev: bool = False

    def check(self) -> DependencyCheckResult:
        result = DependencyCheckResult()
        result.python_version = ".".join(str(v) for v in sys.version_info[:3])
        result.python_ok = sys.version_info[:2] >= _MIN_PYTHON
        result.pyproject_present = os.path.isfile("pyproject.toml")
        result.editable_install = self._editable_install()

        for module, kind, hint in _DEPENDENCIES:
            if kind == DependencyKind.DEV and not self.include_dev:
                # Dev dependency: still report, but as optional info.
                available = self._importable(module)
                result.findings.append(DependencyFinding(
                    module, DependencyKind.OPTIONAL, available,
                    "dev dependency (only needed to run the test suite)", hint))
                continue
            available = self._importable(module)
            detail = "" if available else f"{module} not importable"
            result.findings.append(DependencyFinding(
                module, kind, available, detail, hint))
        return result

    @staticmethod
    def _importable(module: str) -> bool:
        try:
            importlib.import_module(module)
            return True
        except Exception:
            return False

    @staticmethod
    def _editable_install() -> bool:
        try:
            import solaris_ai_nn
            path = os.path.dirname(os.path.abspath(solaris_ai_nn.__file__))
            # Editable installs import from the working src tree.
            return "site-packages" not in path
        except Exception:
            return False
