"""Alpha system check (doctor) -- is the local Alpha System ready and safe?

:class:`AlphaSystemCheck` runs a set of read-only checks (package importable,
Python version, state dir writable, profile valid, registry built, safety
validator available, ClaimGuard available, fixture/report writers present, docs/
examples present) plus the negative safety checks (no live mode by default, no
network/Git/GitHub requirement, no feeder auto-start, no unbounded runtime, no
unsupported claim text). Each check is a pass/info/warning/blocker result.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class AlphaCheckSeverity:
    PASS = "pass"
    INFO = "info"
    WARNING = "warning"
    BLOCKER = "blocker"

    ALL = (PASS, INFO, WARNING, BLOCKER)


@dataclass
class AlphaCheckResult:
    """One check result."""

    name: str
    severity: str = AlphaCheckSeverity.PASS
    detail: str = ""

    def __post_init__(self) -> None:
        if self.severity not in AlphaCheckSeverity.ALL:
            self.severity = AlphaCheckSeverity.INFO

    @property
    def is_blocker(self) -> bool:
        return self.severity == AlphaCheckSeverity.BLOCKER

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "severity": self.severity,
                "detail": self.detail, "is_blocker": self.is_blocker}


@dataclass
class AlphaSystemCheck:
    """Runs the read-only Alpha doctor checks."""

    results: List[AlphaCheckResult] = field(default_factory=list)

    def run(self, *, state_root: str, profile: Any, registry: Any,
            require_claimguard: bool = False,
            repo_root: Optional[str] = None) -> List[AlphaCheckResult]:
        self.results = []
        self._check_package()
        self._record("python_version", AlphaCheckSeverity.INFO,
                     f"Python {sys.version.split()[0]}")
        self._check_state_writable(state_root)
        self._check_profile(profile)
        self._check_registry(registry)
        self._check_safety_validator()
        self._check_claimguard(require_claimguard)
        self._check_fixture(repo_root)
        self._check_report_writer()
        self._check_docs_examples(repo_root)
        self._check_no_live_default(profile)
        self._check_no_external_requirement(profile)
        self._check_no_feeder_autostart()
        self._check_bounded(profile)
        self._check_no_unsupported_claims(profile)
        return self.results

    # -- individual checks --------------------------------------------------

    def _record(self, name: str, severity: str, detail: str = "") -> None:
        self.results.append(AlphaCheckResult(name=name, severity=severity,
                                             detail=detail))

    def _check_package(self) -> None:
        try:
            import solaris_ai_nn  # noqa: F401

            self._record("package_importable", AlphaCheckSeverity.PASS)
        except Exception as exc:
            self._record("package_importable", AlphaCheckSeverity.BLOCKER,
                         f"cannot import solaris_ai_nn: {exc}")

    def _check_state_writable(self, state_root: str) -> None:
        try:
            os.makedirs(state_root, exist_ok=True)
            probe = os.path.join(state_root, ".alpha_doctor_probe")
            with open(probe, "w", encoding="utf-8") as fh:
                fh.write("ok")
            os.remove(probe)
            self._record("state_dir_writable", AlphaCheckSeverity.PASS,
                         state_root)
        except Exception as exc:
            self._record("state_dir_writable", AlphaCheckSeverity.BLOCKER,
                         f"state dir not writable: {exc}")

    def _check_profile(self, profile: Any) -> None:
        if profile is None or not getattr(profile, "profile_id", ""):
            self._record("alpha_profile_valid", AlphaCheckSeverity.BLOCKER,
                         "no valid alpha profile")
            return
        self._record("alpha_profile_valid", AlphaCheckSeverity.PASS,
                     profile.profile_id)

    def _check_registry(self, registry: Any) -> None:
        if registry is None or not getattr(registry, "records", None):
            self._record("module_registry_built", AlphaCheckSeverity.BLOCKER,
                         "module registry not built")
            return
        idx = registry.index()
        blocking = idx.get("alpha_blocking_alpha_count", 0)
        if blocking:
            self._record("module_registry_built", AlphaCheckSeverity.BLOCKER,
                         f"{blocking} required alpha module(s) missing/blocked")
        else:
            self._record("module_registry_built", AlphaCheckSeverity.PASS,
                         f"{idx['alpha_available_module_count']} module(s) "
                         "available")

    def _check_safety_validator(self) -> None:
        try:
            from .safety import AlphaResearchSafetyValidator

            AlphaResearchSafetyValidator()
            self._record("safety_validator_available", AlphaCheckSeverity.PASS)
        except Exception as exc:
            self._record("safety_validator_available",
                         AlphaCheckSeverity.BLOCKER, str(exc))

    def _check_claimguard(self, require_claimguard: bool) -> None:
        try:
            from ..governance.compliance import ClaimGuard

            ClaimGuard()
            self._record("claimguard_available", AlphaCheckSeverity.PASS)
        except Exception:
            self._record(
                "claimguard_available",
                AlphaCheckSeverity.BLOCKER if require_claimguard
                else AlphaCheckSeverity.WARNING,
                "ClaimGuard unavailable")

    def _check_fixture(self, repo_root: Optional[str]) -> None:
        # The orchestrator falls back to a synthetic fixture, so this is a
        # warning at most.
        path = self._fixture_path(repo_root)
        if path and os.path.isfile(path):
            self._record("fixture_available", AlphaCheckSeverity.PASS, path)
        else:
            self._record("fixture_available", AlphaCheckSeverity.INFO,
                         "bundled fixture not found; synthetic fallback is used")

    def _check_report_writer(self) -> None:
        try:
            from .reports import AlphaResearchReportBuilder  # noqa: F401

            self._record("report_writer_available", AlphaCheckSeverity.PASS)
        except Exception as exc:
            self._record("report_writer_available", AlphaCheckSeverity.BLOCKER,
                         str(exc))

    def _check_docs_examples(self, repo_root: Optional[str]) -> None:
        root = repo_root or self._guess_repo_root()
        docs = os.path.join(root, "docs") if root else None
        examples = os.path.join(root, "examples") if root else None
        self._record("docs_present",
                     AlphaCheckSeverity.PASS if docs and os.path.isdir(docs)
                     else AlphaCheckSeverity.INFO,
                     docs or "docs directory not located")
        self._record("examples_present",
                     AlphaCheckSeverity.PASS if examples
                     and os.path.isdir(examples) else AlphaCheckSeverity.INFO,
                     examples or "examples directory not located")

    def _check_no_live_default(self, profile: Any) -> None:
        if profile is not None and getattr(profile, "live_read_only_allowed",
                                           False):
            self._record("no_live_mode_default", AlphaCheckSeverity.WARNING,
                         "profile allows live read-only; governance required")
        else:
            self._record("no_live_mode_default", AlphaCheckSeverity.PASS,
                         "fixture-only by default")

    def _check_no_external_requirement(self, profile: Any) -> None:
        constraints = set(getattr(profile, "safety_constraints", []) or [])
        if {"no_network", "no_git_github"} <= constraints:
            self._record("no_network_git_github_requirement",
                         AlphaCheckSeverity.PASS)
        else:
            self._record("no_network_git_github_requirement",
                         AlphaCheckSeverity.WARNING,
                         "profile does not assert no-network/no-Git constraints")

    def _check_no_feeder_autostart(self) -> None:
        from .safety import AlphaResearchSafetyValidator

        v = AlphaResearchSafetyValidator()
        self._record("no_feeder_auto_start",
                     AlphaCheckSeverity.PASS if not v.can_start_feeders()
                     else AlphaCheckSeverity.BLOCKER,
                     "feeder auto-start is impossible by design")

    def _check_bounded(self, profile: Any) -> None:
        max_runtime = getattr(profile, "max_runtime_s", 0)
        if max_runtime and max_runtime > 0:
            self._record("bounded_runtime", AlphaCheckSeverity.PASS,
                         f"max_runtime_s={max_runtime}")
        else:
            self._record("bounded_runtime", AlphaCheckSeverity.BLOCKER,
                         "profile has no positive runtime bound")

    def _check_no_unsupported_claims(self, profile: Any) -> None:
        from .safety import AlphaResearchSafetyValidator

        text = " ".join(getattr(profile, "limitations", []) or [])
        report = AlphaResearchSafetyValidator().validate_claim_text(text)
        self._record("no_unsupported_claim_text",
                     AlphaCheckSeverity.PASS if report.safe
                     else AlphaCheckSeverity.BLOCKER,
                     "; ".join(report.violations) or "profile text is claim-safe")

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _guess_repo_root() -> Optional[str]:
        # alpha_system/ -> solaris_ai_nn/ -> src/ -> repo root
        here = os.path.dirname(os.path.abspath(__file__))
        root = os.path.abspath(os.path.join(here, "..", "..", ".."))
        return root if os.path.isdir(root) else None

    def _fixture_path(self, repo_root: Optional[str]) -> Optional[str]:
        root = repo_root or self._guess_repo_root()
        if not root:
            return None
        return os.path.join(root, "examples", "fixtures",
                            "alpha_fixture_stream.jsonl")

    # -- summary ------------------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        blockers = [r for r in self.results if r.severity ==
                    AlphaCheckSeverity.BLOCKER]
        warnings = [r for r in self.results if r.severity ==
                    AlphaCheckSeverity.WARNING]
        return {
            "check_count": len(self.results),
            "pass_count": sum(1 for r in self.results
                              if r.severity == AlphaCheckSeverity.PASS),
            "warning_count": len(warnings),
            "blocker_count": len(blockers),
            "passed": not blockers,
            "results": [r.to_dict() for r in self.results],
            "note": "read-only doctor checks; nothing is executed and no live "
                    "mode, network, Git/GitHub, or feeder access is required",
        }
