"""Post-pilot baseline comparator: deltas, count-not-growth, sim/real labels."""

from __future__ import annotations

from solaris_ai_nn.post_pilot import BaselineComparator


def test_compares_initial_final():
    cmp = BaselineComparator().compare_dicts(
        "initial", {"compression_ratio": 1.0, "prediction_score": 0.4},
        "final", {"compression_ratio": 1.4, "prediction_score": 0.6})
    assert cmp.deltas["compression_ratio"] == 0.4
    assert "compression_ratio" in cmp.improved_dimensions


def test_count_increase_not_growth():
    cmp = BaselineComparator().compare_dicts(
        "b", {"proto_symbol_count": 2}, "a", {"proto_symbol_count": 50})
    assert "proto_symbol_count" in cmp.count_only_increases
    assert "proto_symbol_count" not in cmp.improved_dimensions


def test_lower_is_better_dimensions():
    cmp = BaselineComparator().compare_dicts(
        "b", {"ambiguous_symbol_ratio": 0.6},
        "a", {"ambiguous_symbol_ratio": 0.3})
    assert "ambiguous_symbol_ratio" in cmp.improved_dimensions


def test_simulated_vs_real_labels_preserved():
    cmp = BaselineComparator().compare_dicts(
        "dry_run", {"structural_change_score": 0.1},
        "real", {"structural_change_score": 0.2},
        before_simulated=True, after_simulated=False)
    assert cmp.simulated_mismatch is True
    assert any("simulated" in n for n in cmp.notes)


def test_identity_continuity_tracked():
    comparator = BaselineComparator()
    before = comparator.snapshot_from("b", {}, is_simulated=False)
    after = comparator.snapshot_from("a", {})
    after.identity_continuous = False
    cmp = comparator.compare(before, after)
    assert cmp.identity_continuous is False
