"""Tests for the bounded novelty generator."""

from __future__ import annotations

import random

from solaris_ai_nn.ecology.novelty import NoveltyGenerator


def test_propose_mints_traceable_patterns():
    gen = NoveltyGenerator(rng=random.Random(1))
    proposal = gen.propose(step=5)
    assert proposal is not None
    assert proposal["pattern_id"].startswith("NOV_")
    assert proposal["novelty_hint"] == 1.0


def test_novelty_is_bounded():
    gen = NoveltyGenerator(rng=random.Random(1), max_novel_patterns=10)
    for step in range(50):
        gen.propose(step)
    assert len(gen.novel_patterns) == 10
    assert gen.capped > 0
    assert gen.propose(99) is None


def test_recurrence_promotes_to_stable():
    gen = NoveltyGenerator(rng=random.Random(1), familiarity_threshold=3)
    proposal = gen.propose(step=0)
    pid = proposal["pattern_id"]
    assert gen.observe_recurrence(pid) is False
    assert gen.observe_recurrence(pid) is False
    assert gen.observe_recurrence(pid) is True  # now familiar
    assert gen.is_stable(pid) is True


def test_recurrence_of_unknown_pattern_is_noop():
    gen = NoveltyGenerator(rng=random.Random(1))
    assert gen.observe_recurrence("NOV_9999") is False


def test_altered_pattern_id_form():
    gen = NoveltyGenerator(rng=random.Random(1))
    proposal = gen.propose(step=0, altered_of="pattern_a")
    assert proposal["pattern_id"].startswith("ALT_pattern_a_")
    assert proposal["altered_of"] == "pattern_a"
