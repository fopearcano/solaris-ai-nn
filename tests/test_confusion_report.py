"""Confusion report: validates, area classified, no training signal."""

from __future__ import annotations

from solaris_ai_nn.tester_feedback import ConfusionArea, TesterConfusionReport


def test_confusion_report_validates():
    c = TesterConfusionReport.from_dict(
        {"confusion_id": "cf1", "area": "membrane_concept",
         "description": "unclear"})
    d = c.to_dict()
    assert d["confusion_id"] == "cf1"
    assert d["area"] == "membrane_concept"


def test_confusion_area_classified():
    c = TesterConfusionReport.from_dict(
        {"confusion_id": "cf2", "area": "not_a_real_area"})
    assert c.area == ConfusionArea.UNKNOWN


def test_no_training_signal_created():
    d = TesterConfusionReport.from_dict({"confusion_id": "cf3"}).to_dict()
    assert d["is_teaching_signal"] is False
    assert d["modifies_system_concepts"] is False
