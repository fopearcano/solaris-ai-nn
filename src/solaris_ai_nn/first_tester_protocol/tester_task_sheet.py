"""First tester task sheet -- a concise required/optional task checklist.

:class:`FirstTesterTaskSheet` is the short, numbered task list for the first tester. It
separates required from optional tasks (live-read-only is clearly optional) and includes a
"stop if unsure" note. It is documentation only.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List


class TesterTaskStatus:
    REQUIRED = "required"
    OPTIONAL = "optional"

    ALL = (REQUIRED, OPTIONAL)


@dataclass
class TesterTask:
    order: int
    text: str
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return {"order": self.order, "text": self.text, "status": self.status}


def _default_tasks() -> List[TesterTask]:
    R, O = TesterTaskStatus.REQUIRED, TesterTaskStatus.OPTIONAL
    rows = [
        ("Install", R),
        ("Run doctor", R),
        ("Run fixture demo", R),
        ("Open console", R),
        ("Generate feedback forms", R),
        ("Record install/CLI/report confusion", R),
        ("Optional: initialize live-read-only", O),
        ("Optional: validate safe/unsafe samples", O),
        ("Optional: run live-read-only birth/membrane/observation", O),
        ("Generate bundles", R),
        ("Complete feedback", R),
        ("Review handoff artifacts", R),
        ("Send manually if requested", R)]
    return [TesterTask(i + 1, text, status)
            for i, (text, status) in enumerate(rows)]


@dataclass
class FirstTesterTaskSheet:
    """The concise first-tester task sheet (required vs optional)."""

    tasks: List[TesterTask] = field(default_factory=_default_tasks)
    stop_if_unsure: str = ("Stop if unsure: if you do not understand what a "
                           "command does, stop and ask before running it. Stop "
                           "conditions override curiosity.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_count": len(self.tasks),
            "required_count": sum(1 for t in self.tasks
                                  if t.status == TesterTaskStatus.REQUIRED),
            "optional_count": sum(1 for t in self.tasks
                                  if t.status == TesterTaskStatus.OPTIONAL),
            "tasks": [t.to_dict() for t in self.tasks],
            "stop_if_unsure": self.stop_if_unsure,
            "local_only": True,
            "note": "concise first-tester task sheet; live-read-only is "
                    "optional; documentation only, no consciousness/life/agency "
                    "claim",
        }

    def build_text(self) -> str:
        lines = ["# First Tester Task Sheet", "",
                 "A concise checklist for the first tester. Required tasks come "
                 "first; live-read-only tasks are **optional**.", ""]
        for t in self.tasks:
            tag = "required" if t.status == TesterTaskStatus.REQUIRED \
                else "optional"
            lines.append(f"{t.order}. [{tag}] {t.text}")
        lines += ["", f"> **{self.stop_if_unsure}**", "",
                  "_Documentation-only task sheet. Solaris controls nothing; it "
                  "is local-only and non-actuating and makes no claim of "
                  "consciousness/life/agency._"]
        return "\n".join(lines)

    def write(self, checklists_dir: str) -> Dict[str, str]:
        os.makedirs(checklists_dir, exist_ok=True)
        md_path = os.path.join(checklists_dir, "FIRST_TESTER_TASK_SHEET.md")
        json_path = os.path.join(checklists_dir, "FIRST_TESTER_TASK_SHEET.json")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(self.build_text())
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
        return {"markdown": md_path, "json": json_path}
