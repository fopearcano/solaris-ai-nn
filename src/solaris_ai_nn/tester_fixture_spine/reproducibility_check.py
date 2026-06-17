"""Reproducibility check -- did this fixture run reproduce the known-good shape?

:class:`TesterReproducibilityCheck` compares a finished tester run against the expected
output spec and (optionally) a golden manifest: the same fixture hash, the expected
artifact structure, the expected safety invariants, the expected quarantine behavior,
the expected membrane impression count range and receptor coverage, the operator-pulse
attenuation, the source-pressure summary, the generated reports, optional-stage skip
consistency, no raw-event bypass, and no unsupported claims. It ignores timestamps and
run ids; it fails on missing required artifacts, safety-invariant violations, or
unsupported claims, and warns on missing optional modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ReproducibilityStatus:
    PASS = "pass"
    PASS_WITH_WARNINGS = "pass_with_warnings"
    FAIL = "fail"
    BLOCKED = "blocked"
    INCONCLUSIVE = "inconclusive"

    ALL = (PASS, PASS_WITH_WARNINGS, FAIL, BLOCKED, INCONCLUSIVE)


@dataclass
class ReproducibilityFinding:
    """One reproducibility finding."""

    check: str
    passed: bool
    severity: str = "warning"  # info | warning | fail
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"check": self.check, "passed": self.passed,
                "severity": self.severity, "detail": self.detail}


@dataclass
class ReproducibilityCheckResult:
    """The aggregate reproducibility result."""

    status: str = ReproducibilityStatus.INCONCLUSIVE
    findings: List[ReproducibilityFinding] = field(default_factory=list)

    @property
    def fail_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "fail"
                   and not f.passed)

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "warning"
                   and not f.passed)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reproducibility_status": self.status,
            "finding_count": len(self.findings),
            "fail_count": self.fail_count,
            "warning_count": self.warning_count,
            "findings": [f.to_dict() for f in self.findings],
            "ignores_timestamps_and_run_ids": True,
            "note": "reproducibility ignores timestamps/run ids; it fails on "
                    "missing required artifacts, safety violations, or "
                    "unsupported claims, and warns on missing optional modules",
        }


@dataclass
class TesterReproducibilityCheck:
    """Checks whether a finished tester run reproduced the known-good shape."""

    def check(self, *, context: Dict[str, Any], expected_spec,
              golden_manifest: Optional[Any] = None,
              expected_fixture_hash: str = "") -> ReproducibilityCheckResult:
        result = ReproducibilityCheckResult()
        F = ReproducibilityFinding

        # Fixture hash stability (ignores run ids/timestamps).
        current_hash = context.get("fixture_hash", "")
        baseline_hash = expected_fixture_hash or (
            golden_manifest.fixture_hash if golden_manifest else "")
        if baseline_hash:
            ok = current_hash == baseline_hash
            result.findings.append(F("same_fixture_pack_hash", ok,
                                     "fail" if not ok else "info",
                                     f"current={current_hash[:12]} "
                                     f"baseline={baseline_hash[:12]}"))

        # Expected invariants (structure + safety).
        spec_result = expected_spec.evaluate(context)
        for finding in spec_result["findings"]:
            sev = "fail" if finding["required"] else "warning"
            result.findings.append(F(
                finding["name"], finding["passed"], sev, finding["detail"]))

        # Required artifacts present (from golden manifest, if available).
        if golden_manifest is not None:
            for art in golden_manifest.required_artifacts:
                present = bool(context.get("present_artifacts", {}).get(
                    art.artifact_type, art.present))
                result.findings.append(F(
                    f"required_artifact:{art.artifact_type}", present,
                    "fail" if not present else "info"))
            for art in golden_manifest.artifacts:
                # Conditional markers are present only when a stage was skipped;
                # their absence on a clean run is correct, not a warning.
                if art.required or art.artifact_type.endswith("_marker"):
                    continue
                present = bool(context.get("present_artifacts", {}).get(
                    art.artifact_type, art.present))
                if not present:
                    result.findings.append(F(
                        f"optional_artifact:{art.artifact_type}", False,
                        "warning", "optional artifact missing (skipped honestly)"))

        # Optional-stage skip consistency.
        result.findings.append(F(
            "optional_stage_skip_consistency",
            not context.get("hidden_skips", False), "fail",
            "skipped optional stages are explicitly marked"))

        # No raw-event bypass / no unsupported claims (hard safety).
        result.findings.append(F(
            "no_raw_event_bypass", not context.get("raw_bypass_detected", False),
            "fail", "no raw event bypassed the membrane downstream"))
        result.findings.append(F(
            "no_unsupported_claims", bool(context.get("claims_safe", True)),
            "fail", "no consciousness/life/agency claim is made"))

        if context.get("blocked"):
            result.status = ReproducibilityStatus.BLOCKED
        elif result.fail_count:
            result.status = ReproducibilityStatus.FAIL
        elif result.warning_count:
            result.status = ReproducibilityStatus.PASS_WITH_WARNINGS
        else:
            result.status = ReproducibilityStatus.PASS
        return result
