"""Cross-run alignment: epochs/signs aligned, missing data partial/inconclusive."""

from __future__ import annotations

from solaris_ai_nn.developmental_replication import (
    AlignmentStatus,
    AlignmentTarget,
    CrossRunAlignment,
)


def _run(run_id, epochs=5, concepts=None, signs=None):
    return {
        "run_id": run_id,
        "developmental_profile": {"developmental_epoch_count": epochs,
                                  "composite_growth": 0.6},
        "world_signature": {
            "concept_family_distribution": concepts or {"rf": 3, "vib": 2},
            "sign_family_distribution": signs or {"s1": 2}},
        "source_diet": {"rf": 10},
    }


def test_epochs_aligned():
    out = CrossRunAlignment().align(_run("a"), _run("b"))
    epoch = next(r for r in out["results"]
                 if r["target"] == AlignmentTarget.EPOCH_SEQUENCES)
    assert epoch["status"] == AlignmentStatus.ALIGNED


def test_sign_families_aligned():
    out = CrossRunAlignment().align(_run("a"), _run("b"))
    sign = next(r for r in out["results"]
                if r["target"] == AlignmentTarget.SIGN_FAMILIES)
    assert sign["status"] in (AlignmentStatus.ALIGNED, AlignmentStatus.PARTIAL)


def test_missing_data_partial_or_inconclusive():
    a = _run("a")
    b = {"run_id": "b", "developmental_profile": {}, "world_signature": {}}
    out = CrossRunAlignment().align(a, b)
    assert out["inconclusive_count"] >= 1
    incon = [r for r in out["results"]
             if r["status"] == AlignmentStatus.INCONCLUSIVE]
    assert incon


def test_alignment_note_preserves_differences():
    out = CrossRunAlignment().align(_run("a"), _run("b"))
    assert "preserves run-specific differences" in out["note"]
