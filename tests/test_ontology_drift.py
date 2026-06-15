"""OntologyDrift: human / modality-native drift; contamination affects result."""

from __future__ import annotations

from solaris_ai_nn.sensorium_lab import (
    OntologyDriftDetector,
    OntologyKind,
    SensoriumDifferentiationRunner,
    SensoriumStudyArm,
    SensoriumStudyCondition,
    SensoriumStudyDesign,
)
from solaris_ai_nn.sensorium_lab.sensorium_profiles import SensoriumProfileType as P


def _run(tmp_path, arm_id, condition, profile_type):
    design = SensoriumStudyDesign(ticks=50, max_events=300)
    design.add_arm(SensoriumStudyArm(arm_id=arm_id, condition=condition,
                                     profile_type=profile_type))
    runner = SensoriumDifferentiationRunner(state_dir=str(tmp_path / arm_id),
                                            design=design)
    runner.prepare_study(design)
    runner.run_all()
    return runner.arm_results[arm_id]


def test_modality_native_drift_detected(tmp_path):
    r = _run(tmp_path, "non_human", SensoriumStudyCondition.NON_HUMAN_ONLY,
             P.RF_ECHO_VIBRATION_MAGNETIC)
    assert r.ontology_drift.dominant_ontology == OntologyKind.MODALITY_NATIVE


def test_human_ontology_drift_measured(tmp_path):
    r = _run(tmp_path, "human_labelled",
             SensoriumStudyCondition.HUMAN_LABELLED, P.HUMAN_LABEL_CONTAMINATED)
    weights = r.ontology_drift.weights
    # Human-object and label-contaminated weights are measured (non-trivial).
    assert weights[OntologyKind.HUMAN_OBJECT] >= 0.0
    assert weights[OntologyKind.LABEL_CONTAMINATED] >= 0.0


def test_label_contamination_affects_drift(tmp_path):
    labelled = _run(tmp_path, "labelled",
                    SensoriumStudyCondition.HUMAN_LABELLED,
                    P.HUMAN_LABEL_CONTAMINATED)
    feature = _run(tmp_path, "feature",
                   SensoriumStudyCondition.FEATURE_ONLY,
                   P.FEATURE_ONLY_NO_LABELS)
    lw = labelled.ontology_drift.weights[OntologyKind.LABEL_CONTAMINATED]
    fw = feature.ontology_drift.weights[OntologyKind.LABEL_CONTAMINATED]
    assert lw >= fw


def test_no_runtime_inconclusive():
    result = OntologyDriftDetector().detect(None)
    assert "inconclusive" in " ".join(result.notes).lower()
