"""Spec compliance: satisfied/partial/missing, no satisfied without evidence."""

from __future__ import annotations

from solaris_ai_nn.implementation_intake import SpecComplianceAudit
from solaris_ai_nn.implementation_intake.spec_compliance import (
    SpecComplianceStatus,
)


def _statuses(result):
    return {i["requirement"]: i["status"] for i in result["items"]}


def test_satisfied_partial_missing_statuses():
    result = SpecComplianceAudit().audit(
        spec={"proposed_changes": ["src/solaris_ai_nn/foo/bar.py"],
              "tests_required": ["tests/test_foo_bar.py"],
              "docs_required": ["docs/MISSING.md"]},
        changed_files=["src/solaris_ai_nn/foo/bar.py", "tests/test_foo_bar.py"],
        test_results={"passed": 5, "failed": 1})
    statuses = _statuses(result)
    assert statuses["src/solaris_ai_nn/foo/bar.py"] == \
        SpecComplianceStatus.SATISFIED
    assert statuses["tests/test_foo_bar.py"] == \
        SpecComplianceStatus.PARTIALLY_SATISFIED
    assert statuses["docs/MISSING.md"] == SpecComplianceStatus.NOT_SATISFIED


def test_no_satisfaction_without_evidence():
    result = SpecComplianceAudit().audit(
        spec={"proposed_changes": ["src/solaris_ai_nn/foo/bar.py"]},
        changed_files=[])  # no change set -> cannot be satisfied
    assert result["spec_satisfied_count"] == 0
    statuses = {i["status"] for i in result["items"]}
    assert SpecComplianceStatus.SATISFIED not in statuses


def test_safety_requirement_blocking():
    result = SpecComplianceAudit().audit(
        spec={"safety_gates": ["no_source_self_rewrite"]},
        changed_files=["src/x.py"],
        test_results={"by_category": {"safety": {"passed": False}}})
    safety = next(i for i in result["items"] if i["category"] == "safety_gate")
    assert safety["blocking"] is True
    assert safety["status"] == SpecComplianceStatus.BLOCKED
    assert result["blocking_failure_count"] >= 1


def test_unknown_allowed():
    result = SpecComplianceAudit().audit(spec={})
    assert result["item_count"] >= 1
    assert any(i["status"] == SpecComplianceStatus.UNKNOWN
               for i in result["items"])
