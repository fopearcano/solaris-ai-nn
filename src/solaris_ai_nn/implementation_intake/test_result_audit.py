"""Test result audit -- read test evidence (not proof of correctness).

:class:`TestResultAudit` reads the provided test-result artifact and assesses it
against the required categories (unit, integration, safety, example, ClaimGuard,
regression, soak-compatibility, replication-compatibility). Missing safety tests
block readiness; failed tests block unless explicitly marked non-blocking in the
spec; skipped required tests are warnings or blockers by category. Test output is
*evidence*, not proof of correctness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Categories whose absence/failure blocks readiness.
_BLOCKING_CATEGORIES = ("safety", "claim_guard")
_REQUIRED_CATEGORIES = ("unit", "integration", "safety", "example",
                        "claim_guard", "regression")


@dataclass
class TestRunRecord:
    """A per-category test summary."""

    __test__ = False  # not a pytest test class

    category: str
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    present: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"category": self.category, "passed": self.passed,
                "failed": self.failed, "skipped": self.skipped,
                "present": self.present}


@dataclass
class TestFailureSummary:
    """One blocking/non-blocking test failure."""

    __test__ = False  # not a pytest test class

    test: str
    category: str = ""
    non_blocking: bool = False
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"test": self.test, "category": self.category,
                "non_blocking": self.non_blocking, "detail": self.detail}


@dataclass
class TestResultAudit:
    """Audits a test-result artifact against required categories."""

    __test__ = False  # not a pytest test class

    records: List[TestRunRecord] = field(default_factory=list)
    failures: List[TestFailureSummary] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    totals: Dict[str, int] = field(default_factory=dict)

    def audit(self, *, test_results: Optional[Dict[str, Any]] = None,
              required_categories: Optional[List[str]] = None,
              ) -> Dict[str, Any]:
        tr = test_results or {}
        required = required_categories or list(_REQUIRED_CATEGORIES)
        self.totals = {
            "passed": int(tr.get("passed", 0) or 0),
            "failed": int(tr.get("failed", 0) or 0),
            "skipped": int(tr.get("skipped", 0) or 0),
            "xfail": int(tr.get("xfail", 0) or 0),
            "timeout": int(tr.get("timeout", 0) or 0)}

        by_cat = tr.get("by_category", {}) or {}
        present_categories = set(by_cat)
        for cat, info in by_cat.items():
            info = info if isinstance(info, dict) else {}
            self.records.append(TestRunRecord(
                category=cat, passed=int(info.get("passed", 0) or 0),
                failed=int(info.get("failed", 0) or 0),
                skipped=int(info.get("skipped", 0) or 0), present=True))

        # Explicit failures (with optional non_blocking marking from the spec).
        for fail in tr.get("failures", []) or []:
            f = TestFailureSummary(
                test=str(fail.get("test", "?")),
                category=str(fail.get("category", "")),
                non_blocking=bool(fail.get("non_blocking", False)),
                detail=str(fail.get("detail", "")))
            self.failures.append(f)
            if f.non_blocking:
                self.warnings.append(f"non-blocking failure: {f.test}")
            else:
                self.blockers.append(f"failed test (blocking): {f.test}")

        # Failures without per-failure detail are treated as blocking; failures
        # explicitly marked non-blocking are handled above and excluded here.
        unexplained = max(0, self.totals["failed"] - len(self.failures))
        if unexplained:
            self.blockers.append(
                f"{unexplained} failed test(s) reported (no per-test detail)")

        if self.totals["timeout"]:
            self.blockers.append(
                f"{self.totals['timeout']} test timeout(s)")

        # Missing / skipped required categories.
        declared_missing = set(tr.get("missing", []) or [])
        for cat in required:
            missing = cat not in present_categories or cat in declared_missing
            if missing:
                self.records.append(TestRunRecord(category=cat, present=False))
                if cat in _BLOCKING_CATEGORIES:
                    self.blockers.append(f"missing required {cat} test(s)")
                else:
                    self.warnings.append(f"missing required {cat} test(s)")
            else:
                rec = next((r for r in self.records if r.category == cat), None)
                if rec and rec.skipped and not rec.passed:
                    if cat in _BLOCKING_CATEGORIES:
                        self.blockers.append(f"required {cat} test(s) skipped")
                    else:
                        self.warnings.append(f"required {cat} test(s) skipped")

        self.findings = list(self.blockers) + list(self.warnings)
        return self.to_dict()

    @property
    def test_failure_count(self) -> int:
        return self.totals.get("failed", 0)

    @property
    def missing_required_test_count(self) -> int:
        return sum(1 for r in self.records if not r.present)

    @property
    def passes(self) -> bool:
        return not self.blockers

    def to_dict(self) -> Dict[str, Any]:
        return {
            "totals": dict(self.totals),
            "records": [r.to_dict() for r in self.records],
            "failures": [f.to_dict() for f in self.failures],
            "test_failure_count": self.test_failure_count,
            "missing_required_test_count": self.missing_required_test_count,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "passes": self.passes,
            "note": "test output is evidence, not proof of correctness; missing "
                    "safety/ClaimGuard tests and blocking failures block "
                    "readiness",
        }
