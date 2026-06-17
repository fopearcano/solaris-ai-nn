"""Live stability scoring: stable > noisy single-source; counterevidence lowers."""

from __future__ import annotations

from solaris_ai_nn.live_ontogenesis import (
    LiveProtoConceptCandidate,
    StabilityScorer,
)


def _cand(cid, source, recurrence, noisy=0, counter=0):
    c = LiveProtoConceptCandidate(candidate_id=cid, feature_signature="s")
    c.source_distribution = {source: recurrence}
    c.modality_distribution = {"scalar": recurrence}
    c.recurrence_count = recurrence
    c.first_seen = "2026-06-18T08:00:00Z"
    c.last_seen = "2026-06-18T09:00:00Z"
    for i in range(recurrence):
        c.add_support(f"{cid}_e{i}", source, "noisy" if i < noisy else "")
    for i in range(counter):
        c.add_counter(f"{cid}_x{i}", source, "divergent")
    return c


def test_stable_pattern_scores_higher_than_noisy_single_source():
    stable = StabilityScorer().score(
        candidate=_cand("ok", "machine_body", 6), recurrence_strength="strong",
        source_reliability=0.9)
    noisy = StabilityScorer().score(
        candidate=_cand("bad", "machine_body", 4, noisy=4),
        recurrence_strength="unstable", source_reliability=0.5)
    assert stable.score > noisy.score


def test_noisy_single_source_downgraded():
    s = StabilityScorer().score(
        candidate=_cand("n", "machine_body", 4, noisy=4),
        recurrence_strength="unstable")
    assert s.score < 0.6


def test_contradictory_evidence_lowers_score():
    clean = StabilityScorer().score(
        candidate=_cand("c", "machine_body", 6), recurrence_strength="strong")
    contradicted = StabilityScorer().score(
        candidate=_cand("d", "machine_body", 6, counter=8),
        recurrence_strength="strong")
    assert contradicted.score < clean.score
