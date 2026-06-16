"""Spec compliance audit -- did the implementation satisfy the compiled spec?

:class:`SpecComplianceAudit` compares the implementation evidence (changed files,
test results, example results, docs) against the compiled experiment spec /
prompt pack / branch spec requirements (classes/functions, integrations, tests,
examples, docs, reports, safety gates, commands). Each item is satisfied /
partially_satisfied / not_satisfied / blocked / not_applicable / unknown. Nothing
is marked satisfied without evidence; safety requirements are blocking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class SpecComplianceStatus:
    SATISFIED = "satisfied"
    PARTIALLY_SATISFIED = "partially_satisfied"
    NOT_SATISFIED = "not_satisfied"
    BLOCKED = "blocked"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"

    ALL = (SATISFIED, PARTIALLY_SATISFIED, NOT_SATISFIED, BLOCKED,
           NOT_APPLICABLE, UNKNOWN)


@dataclass
class SpecComplianceItem:
    """One requirement compared against evidence."""

    requirement: str
    category: str
    status: str
    evidence: List[str] = field(default_factory=list)
    blocking: bool = False
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"requirement": self.requirement, "category": self.category,
                "status": self.status, "evidence": list(self.evidence),
                "blocking": self.blocking, "note": self.note}


@dataclass
class SpecComplianceAudit:
    """Audits implementation evidence against the compiled spec requirements."""

    items: List[SpecComplianceItem] = field(default_factory=list)

    def audit(self, *, spec: Optional[Dict[str, Any]] = None,
              changed_files: Optional[List[str]] = None,
              test_results: Optional[Dict[str, Any]] = None,
              example_results: Optional[Dict[str, Any]] = None,
              ) -> Dict[str, Any]:
        spec = spec or {}
        changed = [str(p).lower() for p in (changed_files or [])]
        test_results = test_results or {}
        example_results = example_results or {}

        # Required classes/functions / expected behavior.
        for change in spec.get("proposed_changes", []) or \
                spec.get("expected_behavior", []):
            self._add_evidence_item(str(change), "proposed_change", changed)
        # Required tests.
        for t in spec.get("tests_required", []):
            self._add_test_item(str(t), changed, test_results)
        # Required examples.
        for ex in spec.get("examples_required", []):
            self._add_evidence_item(str(ex), "example", changed,
                                    extra_ok=bool(example_results.get("ran")))
        # Required docs.
        for doc in spec.get("docs_required", []):
            self._add_evidence_item(str(doc), "docs", changed)
        # Required safety gates (blocking).
        for gate in spec.get("safety_gates", []):
            self._add_safety_item(str(gate), test_results)
        if not self.items:
            self.items.append(SpecComplianceItem(
                "no spec requirements supplied", "general",
                SpecComplianceStatus.UNKNOWN, note="no compiled spec provided"))
        return self.to_dict()

    @staticmethod
    def _token(text: str) -> str:
        # Extract a path-ish token to look for in the change set.
        for part in text.replace("`", " ").split():
            if "/" in part or part.endswith(".py") or part.endswith(".md"):
                return part.lower().rstrip(".,;:")
        return text.lower()

    def _add_evidence_item(self, requirement: str, category: str,
                           changed: List[str], *,
                           extra_ok: bool = False) -> None:
        token = self._token(requirement)
        found = any(token and (token in c or c in token) for c in changed)
        status = (SpecComplianceStatus.SATISFIED if found or extra_ok
                  else SpecComplianceStatus.NOT_SATISFIED if changed
                  else SpecComplianceStatus.UNKNOWN)
        self.items.append(SpecComplianceItem(
            requirement, category, status,
            evidence=[c for c in changed if token and token in c][:3],
            note="evidence found in change set" if found else
            "no matching changed file" if changed else "no change set supplied"))

    def _add_test_item(self, requirement: str, changed: List[str],
                       test_results: Dict[str, Any]) -> None:
        token = self._token(requirement)
        in_changed = any(token and token in c for c in changed)
        passed = int(test_results.get("passed", 0) or 0)
        failed = int(test_results.get("failed", 0) or 0)
        if in_changed and passed and not failed:
            status = SpecComplianceStatus.SATISFIED
        elif in_changed:
            status = SpecComplianceStatus.PARTIALLY_SATISFIED
        elif test_results:
            status = SpecComplianceStatus.NOT_SATISFIED
        else:
            status = SpecComplianceStatus.UNKNOWN
        self.items.append(SpecComplianceItem(
            requirement, "test", status,
            evidence=[c for c in changed if token and token in c][:3],
            note="test file present and suite green" if status ==
            SpecComplianceStatus.SATISFIED else "incomplete test evidence"))

    def _add_safety_item(self, gate: str,
                         test_results: Dict[str, Any]) -> None:
        by_cat = test_results.get("by_category", {}) or {}
        safety = by_cat.get("safety", {})
        passed = safety.get("passed") if isinstance(safety, dict) else None
        if passed is True:
            status = SpecComplianceStatus.SATISFIED
        elif passed is False:
            status = SpecComplianceStatus.BLOCKED
        else:
            status = SpecComplianceStatus.UNKNOWN
        self.items.append(SpecComplianceItem(
            f"safety gate: {gate}", "safety_gate", status, blocking=True,
            note="safety requirement; missing/failed evidence is blocking"))

    def counts(self) -> Dict[str, int]:
        out = {s: 0 for s in SpecComplianceStatus.ALL}
        for i in self.items:
            out[i.status] = out.get(i.status, 0) + 1
        return out

    @property
    def blocking_failures(self) -> List[SpecComplianceItem]:
        return [i for i in self.items if i.blocking and i.status in (
            SpecComplianceStatus.BLOCKED, SpecComplianceStatus.NOT_SATISFIED)]

    def to_dict(self) -> Dict[str, Any]:
        counts = self.counts()
        return {
            "item_count": len(self.items),
            "items": [i.to_dict() for i in self.items],
            "counts": counts,
            "spec_satisfied_count": counts[SpecComplianceStatus.SATISFIED],
            "spec_unsatisfied_count": (
                counts[SpecComplianceStatus.NOT_SATISFIED]
                + counts[SpecComplianceStatus.BLOCKED]),
            "blocking_failure_count": len(self.blocking_failures),
            "note": "nothing is marked satisfied without evidence; unknown and "
                    "partial are valid; safety requirements are blocking",
        }
