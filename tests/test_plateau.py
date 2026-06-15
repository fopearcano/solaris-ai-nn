"""PlateauDetector: plateau detected; recommendation report-only; not failure."""

from __future__ import annotations

from solaris_ai_nn.developmental_life import PlateauDetector, PlateauReason


def test_plateau_detected_on_flat_growth():
    det = PlateauDetector()
    plateaus = det.detect(composite_history=[0.5, 0.5, 0.5],
                          statuses={"perceptual_metabolism": {}})
    assert plateaus
    assert plateaus[0].reason in PlateauReason.ALL


def test_recommendation_report_only():
    det = PlateauDetector()
    plateaus = det.detect(
        composite_history=[0.2, 0.2, 0.2],
        statuses={"perceptual_metabolism": {"source_diet_diversity": 0.1}})
    assert plateaus[0].reason == PlateauReason.NARROW_SOURCE_DIET
    assert "broaden the source diet" in plateaus[0].recommendation
    assert "report-only" in plateaus[0].to_dict()["note"]


def test_plateau_not_failure():
    det = PlateauDetector()
    plateaus = det.detect(composite_history=[0.5, 0.5, 0.5], statuses={})
    assert "not failure" in plateaus[0].to_dict()["note"]


def test_no_plateau_when_growing():
    det = PlateauDetector()
    plateaus = det.detect(composite_history=[0.2, 0.4, 0.6], statuses={})
    assert plateaus == []
