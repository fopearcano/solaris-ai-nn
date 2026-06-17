"""Live tester checklist -- a local, non-executing checklist for the tester.

:class:`TesterLiveChecklist` is documentation, not automation: it lists the steps a
tester performs before, during, and after a live-read-only run, and it clearly marks
the stop conditions. The checklist never executes any step.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class TesterChecklistStatus:
    TODO = "todo"
    STOP_CONDITION = "stop_condition"

    ALL = (TODO, STOP_CONDITION)


@dataclass
class TesterChecklistItem:
    """One checklist item (never executed)."""

    text: str
    command: str = ""
    stop_condition: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text, "command": self.command,
                "status": (TesterChecklistStatus.STOP_CONDITION
                           if self.stop_condition else TesterChecklistStatus.TODO)}


_SECTIONS = (
    ("A. Before live test", [
        ("Run the fixture tester demo first and confirm it passes.",
         "python -m solaris_ai_nn tester-demo --profile fixture_tester_v0", False),
        ("Read the safety boundaries (Solaris never starts/controls feeders).",
         "", False),
        ("Initialize the live tester state + templates.",
         "python -m solaris_ai_nn tester-live-init", False),
        ("Copy the governance template into governance/ (done by init).", "",
         False),
        ("Edit governance MANUALLY: set live_readonly_enabled + operator_approved.",
         "", True),
        ("Copy the feeder registry template (done by init).", "", False),
        ("Review allowed sources; do NOT approve a source you do not understand.",
         "", True),
        ("Run the live tester doctor and resolve every blocker.",
         "python -m solaris_ai_nn tester-live-doctor", True),
    ]),
    ("B. Event preparation", [
        ("Run the safe event pack validation (all accept).",
         "python -m solaris_ai_nn tester-live-samples", False),
        ("Run the unsafe event quarantine test (all quarantine).", "", False),
        ("Manually run external feeders if desired (Solaris never runs them).",
         "python tools/external_feeders/chronos_absence_feeder.py --out "
         ".solaris_ai_nn_live/inbox/chronos_absence.jsonl", False),
        ("Inspect the inbox before any live run.", "", False),
    ]),
    ("C. Live read-only run", [
        ("Run Live Birth over the local inbox.", "", False),
        ("Run the Environmental Membrane.", "", False),
        ("Run the Membrane Integration audit.", "", False),
        ("Run Live Observation over impressions.", "", False),
        ("Generate the tester live reports.",
         "python -m solaris_ai_nn tester-live-run --run-birth --run-membrane "
         "--run-integration --run-observation", False),
    ]),
    ("D. After live run", [
        ("Inspect the quarantine.", "", False),
        ("Inspect the membrane report.", "", False),
        ("Inspect the source pressure summary.", "", False),
        ("Inspect the observation report.", "", False),
        ("Generate the tester live bundle.",
         "python -m solaris_ai_nn tester-live-bundle", False),
        ("Fill in the tester feedback form (not used as training).", "", False),
        ("STOP if any membrane bypass or unsupported claim appears.", "", True),
    ]),
)


@dataclass
class TesterLiveChecklist:
    """The local, non-executing tester live-read-only checklist."""

    sections: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def build(cls) -> "TesterLiveChecklist":
        sections = []
        for title, items in _SECTIONS:
            sections.append({
                "title": title,
                "items": [TesterChecklistItem(t, c, stop).to_dict()
                          for (t, c, stop) in items]})
        return cls(sections=sections)

    def stop_conditions(self) -> List[str]:
        out = []
        for section in self.sections:
            for item in section["items"]:
                if item["status"] == TesterChecklistStatus.STOP_CONDITION:
                    out.append(item["text"])
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checklist": "tester_live_readonly_v0",
            "executes_steps": False,
            "section_count": len(self.sections),
            "stop_conditions": self.stop_conditions(),
            "sections": self.sections,
            "note": "this checklist is documentation only; it never executes any "
                    "step. Stop conditions are marked explicitly.",
        }

    def to_markdown(self) -> str:
        lines = ["# Tester Live-Read-Only Checklist", "",
                 "_This checklist is documentation only; it never executes any "
                 "step. Items marked **STOP** are stop conditions._", ""]
        for section in self.sections:
            lines.append(f"## {section['title']}")
            for item in section["items"]:
                box = "STOP" if item["status"] == "stop_condition" else " "
                line = f"- [{box}] {item['text']}"
                if item["command"]:
                    line += f"\n      `{item['command']}`"
                lines.append(line)
            lines.append("")
        return "\n".join(lines)
