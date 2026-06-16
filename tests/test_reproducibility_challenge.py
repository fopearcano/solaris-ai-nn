"""Reproducibility challenge: generated, missing prereq unavailable, no exec."""

from __future__ import annotations

from solaris_ai_nn.independent_review import (
    ChallengeStatus,
    ChallengeType,
    ReproducibilityChallengeBuilder,
)


def test_challenge_generated():
    ch = ReproducibilityChallengeBuilder().build({
        "research_baseline": {"x": 1}, "scientific_claims": {"x": 1},
        "falsification": {"x": 1}, "replication": {"x": 1}, "soak": {"x": 1},
        "safety": {"x": 1}}).to_dict()
    assert ch["reproducibility_challenge_count"] == len(ChallengeType.ALL)
    assert ch["available_challenge_count"] == len(ChallengeType.ALL)


def test_missing_prerequisite_unavailable():
    ch = ReproducibilityChallengeBuilder().build({
        "research_baseline": {"x": 1}}).to_dict()
    by_type = {s["challenge_type"]: s for s in ch["steps"]}
    # soak-dependent challenges are unavailable without a soak dossier.
    assert by_type[ChallengeType.SHUFFLED_EVENT_ORDER]["status"] == \
        ChallengeStatus.UNAVAILABLE
    assert by_type[ChallengeType.GROWTH_VS_ACCUMULATION]["status"] == \
        ChallengeStatus.UNAVAILABLE
    # fixture demo (needs baseline) is available.
    assert by_type[ChallengeType.FIXTURE_DEMO]["status"] == \
        ChallengeStatus.AVAILABLE


def test_no_command_execution():
    ch = ReproducibilityChallengeBuilder().build({
        "research_baseline": {"x": 1}}).to_dict()
    assert all(s["executed"] is False for s in ch["steps"])


def test_every_challenge_has_expected_and_failure_interpretation():
    ch = ReproducibilityChallengeBuilder().build({"soak": {"x": 1}}).to_dict()
    for s in ch["steps"]:
        assert s["expected"]["expected_artifact"]
        assert s["expected"]["failure_interpretation"]
