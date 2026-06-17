"""Console dashboard -- the structured model rendered to Markdown/HTML.

:class:`TesterDashboardBuilder` assembles a :class:`TesterDashboard` from the discovery
result, status model, summary cards, safety panel, run index, and next actions. The
dashboard is generated from local artifacts only; it never invents successful status,
preserves unknown/missing states, hides nothing safety-relevant, shows no raw private
payloads by default, and implies no consciousness/life/agency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

_SECTION_TITLES = (
    "Release Status", "Quick Safety Status", "Latest Fixture Run",
    "Latest Live Read-Only Run", "Environmental Membrane Status",
    "Quarantine and Safety Blocks", "Source Diet / Source Pressure",
    "Optional Learning Layers", "Claims and Non-Claims", "Artifact Bundles",
    "Missing Artifacts", "Next Recommended Action", "Tester Instructions",
    "Limitations",
)

_WHAT_THIS_CONSOLE_CANNOT_DO = (
    "This console is read-only.",
    "It does not start, stop, schedule, or control feeders.",
    "It does not control hardware.",
    "It does not access network/Git/GitHub/shell/browser/OS.",
    "It does not run a server or open a browser.",
    "It does not publish or upload anything.",
    "It does not execute artifact contents.",
    "It does not treat tester notes as training.",
    "It does not make consciousness/life/agency claims.",
)


@dataclass
class TesterDashboard:
    """The structured dashboard model."""

    sections: Dict[str, Any] = field(default_factory=dict)
    section_titles: List[str] = field(default_factory=lambda:
                                       list(_SECTION_TITLES))

    def to_dict(self) -> Dict[str, Any]:
        return {"section_titles": list(self.section_titles),
                "sections": dict(self.sections),
                "what_this_console_cannot_do": list(
                    _WHAT_THIS_CONSOLE_CANNOT_DO)}


@dataclass
class TesterDashboardBuilder:
    """Builds the dashboard model from the console pieces."""

    def build(self, *, discovery, status, cards, safety_panel, run_index,
              next_actions) -> TesterDashboard:
        from .artifact_discovery import ArtifactKind as K

        card_by_kind = {c.kind: c for c in cards}
        missing = [s.stage for s in status.stages
                   if s.required and not s.ok]
        skipped = [s.stage for s in status.stages
                   if s.health == "skipped_optional"]

        sections = {
            "release_status": {
                "overall_health": status.overall_health,
                "release_ready": status.release_ready,
                "blocker_count": len(status.blockers),
                "warning_count": len(status.warnings)},
            "quick_safety_status": safety_panel.to_dict(),
            "latest_fixture_run": _card(card_by_kind, "fixture_demo"),
            "latest_live_run": _card(card_by_kind, "live_tester"),
            "environmental_membrane": _card(card_by_kind, "membrane"),
            "quarantine_and_safety_blocks": {
                "quarantine": _card(card_by_kind, "quarantine"),
                "blockers": [b.to_dict() for b in status.blockers]},
            "source_diet_pressure": _card(card_by_kind, "source_pressure"),
            "optional_learning_layers": [
                _card(card_by_kind, "ontogenesis"),
                _card(card_by_kind, "semiogenesis"),
                _card(card_by_kind, "cognition")],
            "claims_and_non_claims": _card(card_by_kind, "claims"),
            "artifact_bundles": _card(card_by_kind, "artifact_bundle"),
            "missing_artifacts": missing,
            "skipped_optional_stages": skipped,
            "next_recommended_action": next_actions[0].to_dict()
            if next_actions else {},
            "all_next_actions": [a.to_dict() for a in next_actions],
            "run_index": run_index.to_dict(),
            "cards": [c.to_dict() for c in cards],
            "discovery": {"artifact_count": len(discovery.artifacts),
                          "by_kind": discovery.to_dict()["by_kind"],
                          "warnings": discovery.warnings},
            "tester_instructions": [
                "Start with the fixture tester demo (`tester-demo`).",
                "Prepare live testing with `tester-live-init`, then approve "
                "governance by hand.",
                "Run the live doctor and resolve every blocker before any live "
                "run.",
                "Inspect quarantine and the membrane reports after each run.",
                "This console only summarizes; it never runs or controls "
                "anything."],
            "limitations": _WHAT_THIS_CONSOLE_CANNOT_DO,
        }
        return TesterDashboard(sections=sections)


def _card(card_by_kind: Dict[str, Any], kind: str) -> Dict[str, Any]:
    card = card_by_kind.get(kind)
    return card.to_dict() if card else {"kind": kind, "status": "not_run"}
