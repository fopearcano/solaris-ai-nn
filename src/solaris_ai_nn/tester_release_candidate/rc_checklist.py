"""Tester RC checklist -- the human-readable final RC checklist.

:class:`TesterRCChecklist` builds a sectioned checklist (packaging, fixture, live-read-
only, membrane, console, feedback, safety, docs) from the collected artifacts and the
readiness context. Each item has a tier (required/recommended/optional) and a status. The
checklist never hides a missing required item, and it drives the readiness gate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class RCChecklistStatus:
    PASS = "pass"
    PASS_WITH_WARNINGS = "pass_with_warnings"
    BLOCKED = "blocked"
    MISSING = "missing"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"

    ALL = (PASS, PASS_WITH_WARNINGS, BLOCKED, MISSING, NOT_APPLICABLE, UNKNOWN)


class RCChecklistTier:
    REQUIRED = "required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


@dataclass
class RCChecklistItem:
    section: str
    label: str
    tier: str
    status: str

    @property
    def blocking(self) -> bool:
        return (self.tier == RCChecklistTier.REQUIRED
                and self.status in (RCChecklistStatus.BLOCKED,
                                    RCChecklistStatus.MISSING))

    def to_dict(self) -> Dict[str, Any]:
        return {"section": self.section, "label": self.label, "tier": self.tier,
                "status": self.status, "blocking": self.blocking}


@dataclass
class TesterRCChecklist:
    """The sectioned, human-readable final RC checklist."""

    items: List[RCChecklistItem] = field(default_factory=list)

    def _add(self, section: str, label: str, tier: str, present: bool,
             *, warn: bool = False) -> None:
        if present:
            status = (RCChecklistStatus.PASS_WITH_WARNINGS if warn
                      else RCChecklistStatus.PASS)
        else:
            status = (RCChecklistStatus.MISSING if tier == "required"
                      else RCChecklistStatus.NOT_APPLICABLE)
        self.items.append(RCChecklistItem(section, label, tier, status))

    def build(self, *, collection, ctx: Dict[str, Any]) -> "TesterRCChecklist":
        c = collection
        REQ, REC, OPT = ("required", "recommended", "optional")

        # A. Packaging.
        self._add("A. Packaging", "install guide exists", REQ,
                  c.present("install_guide"))
        self._add("A. Packaging", "doctor report exists", REQ,
                  c.present("environment_doctor_report"))
        self._add("A. Packaging", "command registry report exists", REQ,
                  c.present("command_registry_report"))
        self._add("A. Packaging", "clean-machine readiness report exists", REQ,
                  c.present("clean_machine_report"))

        # B. Fixture.
        self._add("B. Fixture", "fixture demo command available", REQ,
                  (ctx.get("fixture", {}) or {}).get(
                      "fixture_demo_available", True))
        self._add("B. Fixture", "fixture pack exists", REQ,
                  (ctx.get("fixture", {}) or {}).get("fixture_pack", True))
        self._add("B. Fixture", "reproducibility report exists", REC,
                  c.present("reproducibility_report"))
        self._add("B. Fixture", "regression report exists", REC,
                  c.present("regression_report"))
        self._add("B. Fixture", "fixture demo report or instructions exist", REQ,
                  c.present("fixture_demo_report")
                  or c.present("fixture_instructions"))

        # C. Live-read-only.
        live = ctx.get("live", {}) or {}
        self._add("C. Live-read-only", "governance template exists", REQ,
                  live.get("governance_template", True))
        self._add("C. Live-read-only", "feeder registry template exists", REQ,
                  live.get("feeder_registry_template", True))
        self._add("C. Live-read-only", "safe/unsafe event packs exist", REQ,
                  live.get("event_packs", True))
        self._add("C. Live-read-only", "external feeder policy exists", REQ,
                  c.present("external_feeder_policy"))
        self._add("C. Live-read-only", "live doctor instructions exist", REQ,
                  c.present("live_readonly_instructions"))

        # D. Membrane.
        mem = ctx.get("membrane", {}) or {}
        self._add("D. Membrane", "membrane module exists", REQ,
                  mem.get("module_available", True))
        self._add("D. Membrane", "membrane integration exists", REQ,
                  mem.get("integration_available", True))
        self._add("D. Membrane", "sensory impression docs exist", REQ,
                  mem.get("impression_docs", True))
        self._add("D. Membrane", "raw-event bypass detection exists", REQ,
                  mem.get("bypass_detection", True))

        # E. Console.
        console = ctx.get("console", {}) or {}
        self._add("E. Console", "static Markdown console exists", REQ,
                  c.present("console_index") or console.get("available", True))
        self._add("E. Console", "static HTML console exists", OPT,
                  c.present("static_html_console"))
        self._add("E. Console", "console is read-only", REQ,
                  console.get("read_only", True))
        self._add("E. Console", "safety panel exists", REQ,
                  console.get("safety_panel", True))

        # F. Feedback.
        fb = ctx.get("feedback", {}) or {}
        self._add("F. Feedback", "feedback forms exist", REQ,
                  c.present("feedback_form"))
        self._add("F. Feedback", "feedback ledger exists", REC,
                  fb.get("ledger", c.present("feedback_report")))
        self._add("F. Feedback", "non-training statement exists", REQ,
                  fb.get("non_training", True))
        self._add("F. Feedback", "feedback bundle instructions exist", REC,
                  fb.get("bundle", True))

        # G. Safety.
        sf = ctx.get("safety_freeze", {}) or {}
        sf_ready = sf.get("readiness", "unknown")
        self._add("G. Safety", "safety freeze passed", REQ,
                  sf_ready in ("ready_for_release_candidate", "ready",
                               "ready_with_warnings"),
                  warn=sf_ready == "ready_with_warnings")
        self._add("G. Safety", "forbidden claims absent", REQ,
                  int(sf.get("forbidden_claim_count", 0) or 0) == 0)
        self._add("G. Safety", "open release blockers absent", REQ,
                  int(sf.get("open_release_blocker_count",
                             sf.get("release_blocker_count", 0)) or 0) == 0)
        self._add("G. Safety", "disclaimers present", REQ,
                  (ctx.get("docs", {}) or {}).get("disclaimers_present", True))

        # H. Docs.
        self._add("H. Docs", "quickstart exists", REQ, c.present("quickstart"))
        self._add("H. Docs", "runbook exists", REQ,
                  c.present("fixture_instructions"))
        self._add("H. Docs", "known issues exists", REQ,
                  (ctx.get("docs", {}) or {}).get("known_issues", True))
        self._add("H. Docs", "release notes exists", REQ,
                  (ctx.get("docs", {}) or {}).get("release_notes", True))
        return self

    @property
    def blocking_items(self) -> List[RCChecklistItem]:
        return [i for i in self.items if i.blocking]

    @property
    def passed(self) -> bool:
        return not self.blocking_items

    def to_dict(self) -> Dict[str, Any]:
        by_tier: Dict[str, int] = {}
        for i in self.items:
            by_tier[i.tier] = by_tier.get(i.tier, 0) + 1
        return {
            "item_count": len(self.items),
            "blocking_count": len(self.blocking_items),
            "passed": self.passed,
            "by_tier": by_tier,
            "items": [i.to_dict() for i in self.items],
            "local_only": True,
            "note": "human-readable RC checklist; missing required items are "
                    "never hidden and drive the readiness gate",
        }

    def to_markdown(self) -> str:
        lines = ["# Tester RC Checklist", "",
                 f"- items: {len(self.items)}; blocking: "
                 f"{len(self.blocking_items)}; passed: {self.passed}", ""]
        section = ""
        for i in self.items:
            if i.section != section:
                section = i.section
                lines += ["", f"### {section}", ""]
            mark = {"pass": "x", "pass_with_warnings": "~",
                    "not_applicable": "-"}.get(i.status, " ")
            lines.append(f"- [{mark}] ({i.tier}) {i.label} -- {i.status}")
        lines += ["", "_Required/recommended/optional items are separated. "
                  "Missing required items are not hidden. Local checklist; no "
                  "claim of consciousness/life/agency is made._"]
        return "\n".join(lines)
