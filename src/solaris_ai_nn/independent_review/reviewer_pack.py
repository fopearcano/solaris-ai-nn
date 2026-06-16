"""Independent reviewer pack -- a claim-constrained local review package.

:class:`ReviewerPackBuilder` assembles the local reviewer pack: scope, what is and
is not being claimed, the baseline under review, the artifact list, required and
optional commands, fixture/replay instructions, safety boundaries, claim /
counterevidence / limitations tables, falsification tests, control comparisons,
expected outputs, common failure modes, a reviewer checklist, and unresolved
questions. The pack is claim-constrained, includes forbidden-claim disclaimers,
does not imply consciousness/life/agency, hides no negative evidence, and is not
marked review-ready while the sanitizer blocks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_NOT_CLAIMING = (
    "consciousness", "sentience", "biological life", "personhood", "agency",
    "free will", "emotion", "feeling", "understanding", "self-awareness",
    "autonomous self-improvement", "subjective experience",
)
_DISCLAIMER = ("This package makes no claim of consciousness, sentience, "
               "biological life, personhood, agency, free will, emotion, "
               "feeling, understanding, self-awareness, or subjective "
               "experience. It describes operational structures and bounded "
               "evidence only.")


@dataclass
class ReviewerPackSection:
    """One titled section of the reviewer pack."""

    title: str
    body: Any

    def to_dict(self) -> Dict[str, Any]:
        return {"title": self.title, "body": self.body}


@dataclass
class IndependentReviewerPack:
    """The assembled reviewer pack (local; not published)."""

    sections: Dict[str, Any] = field(default_factory=dict)
    sanitizer_blocked: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reviewer_pack_section_count": len(self.sections),
            "sanitizer_blocked": self.sanitizer_blocked,
            "sections": self.sections,
            "published": False, "uploaded": False,
            "note": "claim-constrained local review package; includes "
                    "forbidden-claim disclaimers, hides no negative evidence, and "
                    "is not published or uploaded",
        }


@dataclass
class ReviewerPackBuilder:
    """Builds the claim-constrained reviewer pack from the review material."""

    def build(self, *,
              claim_registry: Dict[str, Any],
              counterevidence: Dict[str, Any],
              limitations: Dict[str, Any],
              manifest: Dict[str, Any],
              challenges: Dict[str, Any],
              questions: Dict[str, Any],
              baseline_status: str = "",
              safety_boundary: str = "",
              sanitizer_blocked: bool = False,
              ) -> IndependentReviewerPack:
        claims = claim_registry.get("claims", [])
        supported = [c for c in claims if c.get("status") in
                     ("supported", "weakly_supported", "partially_supported")]
        not_reviewable = [c for c in claims if c.get("status") in
                          ("unsupported", "contradicted", "falsified",
                           "forbidden")]
        available = [s for s in challenges.get("steps", [])
                     if s.get("status") == "available"]

        sections: Dict[str, Any] = {
            "purpose": ("Allow an external reviewer to inspect, reproduce, and "
                        "critique the bounded evidence locally."),
            "project_scope": ("A bounded recurrent substrate with plural "
                              "sensorium, perceptual metabolism, and a closed "
                              "research/evidence cycle; all evidence is from "
                              "local fixtures or read-only feeds."),
            "what_is_being_claimed": [c.get("text", "") for c in supported]
            or ["No claim reached supported status; see the claim table."],
            "what_is_not_being_claimed": list(_NOT_CLAIMING),
            "baseline_under_review": baseline_status or "see baseline report",
            "artifact_list": [a.get("category") for a in
                              manifest.get("artifacts", [])],
            "required_commands": [s.get("command") for s in available
                                  if s.get("challenge_type") in (
                                      "fixture_demo_reproduction",
                                      "scientific_claim_report_reproduction",
                                      "claimguard_scan",
                                      "safety_invariant_scan")],
            "optional_commands": [s.get("command") for s in available
                                  if s.get("challenge_type") not in (
                                      "fixture_demo_reproduction",
                                      "scientific_claim_report_reproduction",
                                      "claimguard_scan",
                                      "safety_invariant_scan")],
            "fixture_replay_instructions": (
                "Run the bounded fixture demos; nothing reads the network or "
                "controls hardware. Replays are deterministic given the seed."),
            "live_read_only_limitations": (
                "Live-field evidence, where present, is read-only; the system "
                "never controls feeders or actuates anything."),
            "safety_boundaries": safety_boundary or (
                "no actuation, no hardware/feeder/network/shell, no source "
                "self-rewrite, no Git/GitHub automation, no unsupported "
                "consciousness/life/agency claims"),
            "claim_table": claims,
            "counterevidence_table": counterevidence.get("records", []),
            "limitations_table": limitations.get("limitations", []),
            "falsification_tests": [s.get("command") for s in
                                    challenges.get("steps", [])
                                    if "falsif" in s.get("challenge_type", "")],
            "control_comparisons": [s.get("command") for s in
                                    challenges.get("steps", [])
                                    if "control" in s.get("challenge_type", "")],
            "expected_outputs": [s.get("expected", {}).get("expected_artifact")
                                 for s in available],
            "common_failure_modes": [
                "fixture overfit", "log accumulation vs development",
                "passive-parser equivalence", "human-label leakage",
                "missing replication"],
            "reviewer_checklist": [
                "are all critical artifacts present?",
                "do claims map to evidence?",
                "is counterevidence visible?",
                "are limitations specific?",
                "do controls have equal opportunity?",
                "which evidence would falsify the central claim?"],
            "unresolved_questions": [q.get("text") for q in
                                     questions.get("questions", [])],
            "claims_not_reviewable": [c.get("text", "") for c in not_reviewable],
            "disclaimer": _DISCLAIMER,
        }
        return IndependentReviewerPack(sections=sections,
                                       sanitizer_blocked=sanitizer_blocked)
