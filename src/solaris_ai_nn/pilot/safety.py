"""PilotSafetyValidator -- the gate every pilot passes before it exists.

Pure inspection: it reads a manifest/profile/event and returns a
:class:`SafetyReport`. It never repairs, never downgrades silently, and the
deployment runner refuses to run on an unsafe report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import data_contracts as DC
from .pilot_manifest import PilotManifest
from .profiles import (
    UNIVERSALLY_FORBIDDEN_OUTPUTS,
    PilotProfile,
    PilotProfileRegistry,
    PilotProfileType,
)

# Default roots a pilot may write under. Anything else needs to be passed
# explicitly as an approved root (e.g. a pytest tmp_path).
DEFAULT_APPROVED_OUTPUT_ROOTS = (
    ".solaris_ai_nn_state", ".solaris_ai_nn_pilots", ".solaris_ai_nn_ops",
    ".solaris_ai_nn_runs", ".solaris_ai_nn_governance",
    ".solaris_ai_nn_benchmarks",
)

# Feature flags that must never appear enabled in a pilot manifest.
FORBIDDEN_FEATURES = frozenset({
    "real_world", "real_world_actuation", "network", "network_effectors",
    "os_automation", "browser", "browser_automation", "robotics",
    "action_authority", "commit_actions",
})


@dataclass
class SafetyReport:
    """Result of one pilot safety validation."""

    safe: bool
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checks: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "violations": list(self.violations),
                "warnings": list(self.warnings), "checks": self.checks}


@dataclass
class PilotSafetyValidator:
    """Validates pilot manifests, profiles, and input events."""

    profile_registry: PilotProfileRegistry = field(
        default_factory=PilotProfileRegistry.default)
    approved_output_roots: List[str] = field(
        default_factory=lambda: list(DEFAULT_APPROVED_OUTPUT_ROOTS))

    def _path_approved(self, path: str,
                       extra_roots: Optional[List[str]] = None) -> bool:
        candidate = Path(path).resolve()
        roots = list(self.approved_output_roots) + list(extra_roots or [])
        for root in roots:
            resolved = Path(root).resolve()
            try:
                candidate.relative_to(resolved)
                return True
            except ValueError:
                continue
        return False

    # -- manifest -----------------------------------------------------------------

    def validate_manifest(self, manifest: PilotManifest,
                          context: Optional[Dict[str, Any]] = None,
                          ) -> SafetyReport:
        ctx = context or {}
        violations: List[str] = []
        warnings: List[str] = []
        checks: List[Dict[str, Any]] = []

        def check(name: str, ok: bool, detail: str = "",
                  warn_only: bool = False) -> None:
            checks.append({"name": name, "passed": ok, "detail": detail})
            if not ok:
                (warnings if warn_only else violations).append(detail or name)

        # 1. Profile known + its own safety holds.
        try:
            profile = self.profile_registry.get(manifest.profile)
        except ValueError as exc:
            check("known_profile", False, str(exc))
            return SafetyReport(safe=False, violations=violations,
                                warnings=warnings, checks=checks)
        profile_report = self.validate_profile(profile)
        check("profile_safety", profile_report.safe,
              "; ".join(profile_report.violations))

        # 2. The safety contract is intact (the manifest enforces this at
        #    construction; dicts loaded from disk get re-checked here).
        check("contract_intact", manifest.contract.is_intact(),
              f"weakened safety contract: {manifest.contract.violations()}")

        # 3. Bounded, or explicitly approved through governance.
        check("bounded_or_approved",
              manifest.is_bounded() or bool(manifest.governance_approval_ids),
              "unbounded pilot without governance approval ids")

        # 4. Emergency stop path configured. The simulated profile is fully
        #    internal, so a missing path is a warning there; profiles that
        #    touch anything external treat it as a violation.
        has_stop = bool(manifest.emergency_stop_path)
        check("emergency_stop_configured", has_stop,
              "emergency stop sentinel path is not configured",
              warn_only=(manifest.profile == PilotProfileType.SIMULATED))

        # 5. No forbidden feature flags.
        enabled = [k for k, v in manifest.enabled_features.items() if v]
        bad = sorted(set(enabled) & FORBIDDEN_FEATURES)
        check("no_forbidden_features", not bad,
              f"forbidden features enabled: {bad}")
        if manifest.enabled_features.get("plasticity") \
                and not manifest.enabled_features.get("plasticity_dry_run"):
            warnings.append("active plasticity in a pilot requires "
                            "governance approval (dry-run is the pilot "
                            "default)")

        # 6. Output dirs under approved roots only.
        extra_roots = ctx.get("approved_output_roots")
        for label, path in (("state_dir", manifest.state_dir),
                            ("artifact_dir", manifest.artifact_dir)):
            check(f"{label}_approved", self._path_approved(path, extra_roots),
                  f"{label} {path!r} is outside the approved output roots")

        # 7. Input sources: explicit existing files, read-only by design.
        if manifest.profile == PilotProfileType.READ_ONLY_STREAM:
            check("has_input_sources", bool(manifest.input_sources),
                  "read_only_stream pilot needs explicit input sources")
            for source in manifest.input_sources:
                if any(c in source for c in "*?["):
                    check("explicit_input_paths", False,
                          f"input source {source!r} is a glob; pass explicit "
                          "file paths")
                elif not Path(source).is_file():
                    check("input_exists", False,
                          f"input source {source!r} is not an existing file")

        # 8. Sidecar action authority stays off; publishing needs approval.
        if manifest.profile == PilotProfileType.SOLARIS_SIDECAR_OBSERVE \
                or manifest.enabled_features.get("sidecar"):
            check("no_action_authority",
                  not ctx.get("sidecar_action_authority", False),
                  "sidecar action authority is forbidden in pilots")
            if ctx.get("sidecar_publish") \
                    and not manifest.governance_approval_ids:
                check("publish_requires_approval", False,
                      "publishing suggestions requires a governance approval "
                      "id on the manifest")

        # 9. Output policy never points outward.
        check("output_policy_internal",
              manifest.output_policy in ("artifacts_only", "suggestions_local"),
              f"output policy {manifest.output_policy!r} is not an "
              "internal-only policy")

        return SafetyReport(safe=not violations, violations=violations,
                            warnings=warnings, checks=checks)

    # -- profile -----------------------------------------------------------------

    def validate_profile(self, profile: PilotProfile) -> SafetyReport:
        violations: List[str] = []
        missing = [o for o in UNIVERSALLY_FORBIDDEN_OUTPUTS
                   if not profile.forbids(o)]
        if missing:
            violations.append(
                f"profile {profile.profile_type!r} fails to forbid {missing}")
        for action in profile.allowed_actions:
            problems = DC._payload_problems(action)
            if problems:
                violations.append(
                    f"profile allows a command-shaped action {action!r}")
        if profile.profile_type != PilotProfileType.SIMULATED \
                and profile.allowed_actions:
            violations.append(
                f"profile {profile.profile_type!r} must not allow external "
                "actions")
        return SafetyReport(safe=not violations, violations=violations)

    # -- events --------------------------------------------------------------------

    def validate_input_event(self, event: Any) -> SafetyReport:
        """Re-check one stream event (raw dict or text line)."""
        if isinstance(event, str):
            result = DC.validate_text_line(event)
        else:
            result = DC.validate_jsonl_event(event)
        return SafetyReport(safe=result.valid, violations=list(result.reasons))
