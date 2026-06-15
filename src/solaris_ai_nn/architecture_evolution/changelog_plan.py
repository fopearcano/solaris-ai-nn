"""Changelog planning -- proposed changes, explicitly not applied.

The :class:`ChangelogPlan` lists proposed removals, promotions, revisions,
experiments, and doc/test updates, plus compatibility risks. It is a *plan*, not
applied release notes, and it states clearly that no code change was applied.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List


class ChangelogImpact:
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    UNKNOWN = "unknown"

    ALL = (NONE, LOW, MODERATE, HIGH, UNKNOWN)


@dataclass
class ChangelogItem:
    """One proposed (not applied) changelog entry."""

    category: str  # removal | promotion | revision | experiment | docs_tests
    summary: str
    target_modules: List[str] = field(default_factory=list)
    compatibility_impact: str = ChangelogImpact.UNKNOWN
    applied: bool = False  # always False -- planning only

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "applied": False}


@dataclass
class ChangelogPlan:
    """A planning changelog; nothing here is applied."""

    base_dir: str = ".solaris_ai_nn_architecture"
    items: List[ChangelogItem] = field(default_factory=list)

    def add(self, category: str, summary: str, **kwargs: Any) -> ChangelogItem:
        item = ChangelogItem(category=category, summary=summary, **kwargs)
        self.items.append(item)
        return item

    def _by_category(self, category: str) -> List[ChangelogItem]:
        return [i for i in self.items if i.category == category]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "applied": False,
            "proposed_removals": [i.to_dict() for i in
                                  self._by_category("removal")],
            "proposed_promotions": [i.to_dict() for i in
                                    self._by_category("promotion")],
            "proposed_revisions": [i.to_dict() for i in
                                   self._by_category("revision")],
            "proposed_experiments": [i.to_dict() for i in
                                     self._by_category("experiment")],
            "proposed_docs_tests": [i.to_dict() for i in
                                    self._by_category("docs_tests")],
            "compatibility_risks": [
                {"summary": i.summary, "impact": i.compatibility_impact}
                for i in self.items
                if i.compatibility_impact in (ChangelogImpact.HIGH,
                                              ChangelogImpact.MODERATE)],
            "not_implemented_note": "This is a plan. No code change has been "
                                    "applied; these are proposals for operator "
                                    "review.",
        }

    def render_markdown(self) -> str:
        d = self.to_dict()
        lines = ["# Changelog Plan (NOT APPLIED)", "",
                 "_This is a plan, not applied release notes. **No code change "
                 "has been applied.** Each item is a proposal for operator "
                 "review._", ""]
        for key, heading in (("proposed_removals", "Proposed removals"),
                             ("proposed_promotions", "Proposed promotions"),
                             ("proposed_revisions", "Proposed revisions"),
                             ("proposed_experiments", "Proposed experiments"),
                             ("proposed_docs_tests", "Proposed docs/tests")):
            lines.append(f"## {heading}")
            group = d[key]
            lines += [f"- {i['summary']} (not applied)" for i in group] or \
                ["- none"]
            lines.append("")
        lines += ["## Compatibility risks"]
        lines += [f"- [{r['impact']}] {r['summary']}"
                  for r in d["compatibility_risks"]] or ["- none recorded"]
        lines += ["", f"## Not implemented", f"- {d['not_implemented_note']}"]
        return "\n".join(lines)

    def write(self) -> Dict[str, str]:
        os.makedirs(self.base_dir, exist_ok=True)
        md_path = os.path.join(self.base_dir, "CHANGELOG_PLAN.md")
        json_path = os.path.join(self.base_dir, "CHANGELOG_PLAN.json")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(self.render_markdown())
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path}
