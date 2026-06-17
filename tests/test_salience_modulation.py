"""Membrane salience: novelty raises it, contamination lowers it, operator capped."""

from __future__ import annotations

from solaris_ai_nn.environmental_membrane import MembraneSalienceModulator


def test_novelty_increases_salience():
    mod = MembraneSalienceModulator()
    high = mod.modulate(novelty=0.9, source_reliability=0.9, source_count=2)
    low = mod.modulate(novelty=0.1, source_reliability=0.9, source_count=2)
    assert high.score > low.score


def test_contamination_lowers_usable_salience():
    mod = MembraneSalienceModulator()
    clean = mod.modulate(novelty=0.9, source_reliability=0.9, source_count=2)
    dirty = mod.modulate(novelty=0.9, source_reliability=0.9, source_count=2,
                         contamination=0.8)
    assert dirty.score < clean.score
    assert any("contamination" in n for n in dirty.notes)


def test_operator_salience_capped():
    mod = MembraneSalienceModulator(operator_pulse_cap=0.4)
    s = mod.modulate(novelty=0.95, source_reliability=0.9, source_count=2,
                     operator_weight=1.0)
    assert s.score <= 0.4
    assert s.capped is True


def test_human_text_salience_capped():
    mod = MembraneSalienceModulator(human_text_cap=0.5)
    s = mod.modulate(novelty=0.95, source_reliability=0.9, source_count=2,
                     human_text_weight=1.0)
    assert s.score <= 0.5
    assert s.capped is True
