"""WorldSignature: generated; no subjective-experience claim; comparison works."""

from __future__ import annotations

from solaris_ai_nn.sensorium_lab import (
    SensoriumDifferentiationRunner,
    SensoriumStudyArm,
    SensoriumStudyCondition,
    SensoriumStudyDesign,
    WorldSignatureComparison,
)
from solaris_ai_nn.sensorium_lab.sensorium_profiles import SensoriumProfileType as P


def _runner(tmp_path):
    design = SensoriumStudyDesign(ticks=40, max_events=200)
    design.add_arm(SensoriumStudyArm(
        arm_id="human_like", condition=SensoriumStudyCondition.HUMAN_LIKE_ONLY,
        profile_type=P.HUMAN_LIKE_TEXT_LIGHT_TEMPERATURE))
    design.add_arm(SensoriumStudyArm(
        arm_id="non_human", condition=SensoriumStudyCondition.NON_HUMAN_ONLY,
        profile_type=P.RF_ECHO_VIBRATION_MAGNETIC))
    runner = SensoriumDifferentiationRunner(state_dir=str(tmp_path / "lab"),
                                            design=design)
    runner.prepare_study(design)
    runner.run_all()
    return runner


def test_signature_generated(tmp_path):
    runner = _runner(tmp_path)
    sig = runner.arm_results["non_human"].signature
    assert sig is not None
    assert sig.modality_distribution


def test_no_subjective_experience_claim(tmp_path):
    runner = _runner(tmp_path)
    sig = runner.arm_results["non_human"].signature
    blob = str(sig.to_dict()).lower()
    assert "not subjective experience" in blob
    assert "qualia" not in sig.to_dict()["note"] or "not qualia" in blob


def test_comparison_works(tmp_path):
    runner = _runner(tmp_path)
    a = runner.arm_results["human_like"].signature
    b = runner.arm_results["non_human"].signature
    diff = WorldSignatureComparison().compare(a, b)
    assert "proto_family_jaccard" in diff
    assert "not a ranking" in diff["note"]
