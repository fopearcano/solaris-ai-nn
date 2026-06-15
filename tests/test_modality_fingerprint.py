"""ModalityFingerprint: generated; structurally weak modality reported."""

from __future__ import annotations

from solaris_ai_nn.sensorium_lab import (
    ModalityFingerprint,
    SensoriumDifferentiationRunner,
    SensoriumStudyArm,
    SensoriumStudyCondition,
    SensoriumStudyDesign,
)
from solaris_ai_nn.sensorium_lab.sensorium_profiles import SensoriumProfileType as P


def test_fingerprint_generated(tmp_path):
    design = SensoriumStudyDesign(ticks=50, max_events=300)
    design.add_arm(SensoriumStudyArm(
        arm_id="mixed", condition=SensoriumStudyCondition.MIXED_PLURAL_SENSORIUM,
        profile_type=P.MIXED_HUMAN_NONHUMAN))
    runner = SensoriumDifferentiationRunner(state_dir=str(tmp_path / "lab"),
                                            design=design)
    runner.prepare_study(design)
    runner.run_all()
    fingerprints = runner.arm_results["mixed"].fingerprints
    assert fingerprints
    assert all(isinstance(f, ModalityFingerprint) for f in fingerprints)
    assert all(f.event_count >= 0 for f in fingerprints)


def test_structurally_weak_reported_honestly():
    # A modality with many events but no structural effect is flagged weak.
    weak = ModalityFingerprint(modality="radio_frequency", event_count=10,
                               invariants=0, proto_symbols=0, baseline_shifts=0,
                               absences=0, rhythms=0)
    assert weak.structurally_weak is True
    strong = ModalityFingerprint(modality="radio_frequency", event_count=10,
                                 invariants=3)
    assert strong.structurally_weak is False


def test_fingerprint_records_contributions():
    fp = ModalityFingerprint(modality="vibration", event_count=5, invariants=2,
                             rhythms=1, proto_symbols=1)
    d = fp.to_dict()
    assert d["structural_effect"] == 4
    assert d["modality"] == "vibration"
