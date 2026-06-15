"""HumanLabelContaminationAnalyzer: external annotation detected; not truth."""

from __future__ import annotations

from solaris_ai_nn.sensorium_lab import (
    HumanLabelContaminationAnalyzer,
    SensoriumDifferentiationRunner,
    SensoriumStudyArm,
    SensoriumStudyCondition,
    SensoriumStudyDesign,
)
from solaris_ai_nn.sensorium_lab.sensorium_profiles import SensoriumProfileType as P


def _run(tmp_path, condition, profile_type):
    design = SensoriumStudyDesign(ticks=50, max_events=300)
    design.add_arm(SensoriumStudyArm(arm_id="arm", condition=condition,
                                     profile_type=profile_type))
    runner = SensoriumDifferentiationRunner(state_dir=str(tmp_path / "lab"),
                                            design=design)
    runner.prepare_study(design)
    runner.run_all()
    return runner.arm_results["arm"]


def test_external_annotation_detected(tmp_path):
    r = _run(tmp_path, SensoriumStudyCondition.HUMAN_LABELLED,
             P.HUMAN_LABEL_CONTAMINATED)
    assert r.contamination.contaminated is True
    assert r.contamination.contamination_score > 0.0
    assert r.contamination.sources


def test_feature_only_not_contaminated(tmp_path):
    r = _run(tmp_path, SensoriumStudyCondition.FEATURE_ONLY,
             P.FEATURE_ONLY_NO_LABELS)
    assert r.contamination.contamination_score == 0.0


def test_label_as_ground_truth_blocked():
    analyzer = HumanLabelContaminationAnalyzer()
    # Treating a human label as ground truth is never allowed.
    assert analyzer.validate_not_ground_truth(True) is False
    assert analyzer.validate_not_ground_truth(False) is True


def test_contamination_report_generated(tmp_path):
    r = _run(tmp_path, SensoriumStudyCondition.HUMAN_LABELLED,
             P.HUMAN_LABEL_CONTAMINATED)
    data = r.contamination.to_dict()
    assert "contamination_score" in data
    assert "human labels are allowed as annotations" in data["note"]
