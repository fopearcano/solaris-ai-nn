"""Experiment test matrix -- the tests an implementation must satisfy.

:class:`ExperimentTestMatrix` enumerates the tests required for a compiled spec
across categories (unit, integration, safety, example, report, ClaimGuard,
regression, ablation-comparison, soak-compatibility, replication-compatibility).
Safety and ClaimGuard tests are blocking; missing required tests block ready
status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class TestCategory:
    __test__ = False  # not a pytest test class
    UNIT = "unit"
    INTEGRATION = "integration"
    SAFETY = "safety"
    EXAMPLE = "example"
    REPORT = "report"
    CLAIM_GUARD = "claim_guard"
    REGRESSION = "regression"
    ABLATION_COMPARISON = "ablation_comparison"
    SOAK_COMPATIBILITY = "soak_compatibility"
    REPLICATION_COMPATIBILITY = "replication_compatibility"

    ALL = (UNIT, INTEGRATION, SAFETY, EXAMPLE, REPORT, CLAIM_GUARD, REGRESSION,
           ABLATION_COMPARISON, SOAK_COMPATIBILITY, REPLICATION_COMPATIBILITY)

    BLOCKING = (SAFETY, CLAIM_GUARD)


@dataclass
class TestRequirement:
    """A required test category for a spec (with blocking status)."""

    __test__ = False  # not a pytest test class

    category: str
    blocking: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"category": self.category, "blocking": self.blocking}


@dataclass
class TestMatrixRow:
    """One concrete test the implementation must add/pass."""

    __test__ = False  # not a pytest test class

    test_path: str
    category: str
    purpose: str = ""
    required_input: str = ""
    expected_output: str = ""
    failure_meaning: str = ""
    blocking: bool = False
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"test_path": self.test_path, "category": self.category,
                "purpose": self.purpose, "required_input": self.required_input,
                "expected_output": self.expected_output,
                "failure_meaning": self.failure_meaning,
                "blocking": self.blocking,
                "evidence_refs": list(self.evidence_refs)}


@dataclass
class ExperimentTestMatrix:
    """The full set of test rows required for a compiled spec."""

    __test__ = False  # not a pytest test class

    spec_id: str
    rows: List[TestMatrixRow] = field(default_factory=list)

    def add(self, row: TestMatrixRow) -> None:
        self.rows.append(row)

    def blocking_rows(self) -> List[TestMatrixRow]:
        return [r for r in self.rows if r.blocking]

    def categories_present(self) -> List[str]:
        return sorted({r.category for r in self.rows})

    def missing_blocking_categories(self) -> List[str]:
        present = set(self.categories_present())
        return [c for c in TestCategory.BLOCKING if c not in present]

    @property
    def blocks_ready(self) -> bool:
        return bool(self.missing_blocking_categories())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spec_id": self.spec_id, "row_count": len(self.rows),
            "rows": [r.to_dict() for r in self.rows],
            "categories_present": self.categories_present(),
            "blocking_row_count": len(self.blocking_rows()),
            "missing_blocking_categories": self.missing_blocking_categories(),
            "blocks_ready": self.blocks_ready,
        }


def build_test_matrix(spec: Dict[str, Any]) -> ExperimentTestMatrix:
    """Build the standard test matrix for a compiled spec dict."""
    spec_id = spec.get("spec_id", "spec")
    pkg = (spec.get("target_modules") or ["target_module"])[0]
    refs = list(spec.get("evidence_refs", []))
    matrix = ExperimentTestMatrix(spec_id=spec_id)
    rows = [
        TestMatrixRow(f"tests/test_{pkg}_unit.py", TestCategory.UNIT,
                      "unit-test the new behavior", "synthetic inputs",
                      "deterministic structural outputs",
                      "the new behavior is wrong", False, refs),
        TestMatrixRow(f"tests/test_{pkg}_integration.py",
                      TestCategory.INTEGRATION,
                      "verify integration with the existing stack",
                      "stack module statuses", "wired status present",
                      "integration is broken", False, refs),
        TestMatrixRow(f"tests/test_{pkg}_safety.py", TestCategory.SAFETY,
                      "assert no source/branch/PR/actuation capability",
                      "validator", "all forbidden capabilities False",
                      "a safety boundary was crossed", True, refs),
        TestMatrixRow(f"tests/test_{pkg}_examples.py", TestCategory.EXAMPLE,
                      "the bounded demo runs without an infinite loop",
                      "--state-dir", "exit 0", "the demo is broken", False,
                      refs),
        TestMatrixRow(f"tests/test_{pkg}_reports.py", TestCategory.REPORT,
                      "report Markdown/JSON generate", "runtime",
                      "files written", "reporting is broken", False, refs),
        TestMatrixRow(f"tests/test_{pkg}_reports.py::claim_guard",
                      TestCategory.CLAIM_GUARD,
                      "generated Markdown passes ClaimGuard", "report text",
                      "claim_guard_safe is True",
                      "a report makes an unsupported claim", True, refs),
        TestMatrixRow("tests/ (existing suite)", TestCategory.REGRESSION,
                      "the full suite still passes", "pytest", "no regressions",
                      "the change broke existing behavior", False, refs),
    ]
    spec_type = spec.get("spec_type", "")
    if "ablation" in spec_type or "variant" in spec_type:
        rows.append(TestMatrixRow(
            f"tests/test_{pkg}_ablation.py", TestCategory.ABLATION_COMPARISON,
            "compare the variant against the control arm", "control + variant",
            "documented difference", "the variant adds nothing", False, refs))
    rows.append(TestMatrixRow(
        f"tests/test_{pkg}_soak_compat.py", TestCategory.SOAK_COMPATIBILITY,
        "the change is compatible with the soak protocol", "soak runtime",
        "soak runs bounded", "the change breaks the soak", False, refs))
    rows.append(TestMatrixRow(
        f"tests/test_{pkg}_replication_compat.py",
        TestCategory.REPLICATION_COMPATIBILITY,
        "the run registers for cross-run replication", "replication runtime",
        "run registered", "the change breaks replication", False, refs))
    for r in rows:
        matrix.add(r)
    return matrix
