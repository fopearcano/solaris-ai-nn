"""ResearchMetricsSuite: metrics computed; no mind score; limitations."""

from __future__ import annotations

from solaris_ai_nn.research_lab import METRIC_GROUPS, ResearchMetricsSuite


def test_metrics_computed():
    suite = ResearchMetricsSuite()
    groups = suite.compute({"metrics": {"prediction_accuracy": 0.6,
                                        "proto_symbol_count": 4}})
    assert groups["world_model"]["prediction_accuracy"] == 0.6
    assert groups["proto_language"]["proto_symbol_count"] == 4
    for group in METRIC_GROUPS:
        assert group in groups


def test_no_consciousness_life_sentience_score():
    suite = ResearchMetricsSuite()
    assert suite.has_forbidden_metric() is False
    names = " ".join(suite.metric_names()).lower()
    for forbidden in ("consciousness", "sentience", "life_score", "personhood",
                      "free_will", "soul", "qualia"):
        assert forbidden not in names
    assert suite.compute({})["has_consciousness_score"] is False


def test_limitations_included():
    groups = ResearchMetricsSuite().compute({})
    joined = " ".join(groups["limitations"]).lower()
    assert "operational development proxies" in joined
    assert "not consciousness" in joined


def test_group_scalar():
    suite = ResearchMetricsSuite()
    scalar = suite.group_scalar({"a": 1.0, "b": 3.0, "c": "x"})
    assert scalar == 2.0


def test_ten_metric_groups():
    assert len(METRIC_GROUPS) == 10
