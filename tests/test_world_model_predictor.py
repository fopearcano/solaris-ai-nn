"""Tests for the WorldModelPredictor."""

from __future__ import annotations

from solaris_ai_nn.world_model.edges import EdgeType
from solaris_ai_nn.world_model.graph import KnowledgeGraph
from solaris_ai_nn.world_model.nodes import NodeType
from solaris_ai_nn.world_model.prediction import WorldModelPredictor


def _trained_graph():
    g = KnowledgeGraph()
    stimulus = g.upsert_node(NodeType.SIGNAL_TYPE, "Stimulus")
    for _ in range(9):
        g.observe_node(stimulus.node_id)
    g.upsert_node(NodeType.SIGNAL_TYPE, "Reaction")
    action = g.upsert_node(NodeType.ACTION, "approach")
    positive = g.upsert_node(NodeType.REACTION, "valence_positive")
    for _ in range(6):
        g.upsert_edge(action, EdgeType.PRODUCES, positive)
        g.upsert_edge(positive, EdgeType.REINFORCES, action)
    blocked = g.upsert_node(NodeType.ACTION, "move_north")
    wall = g.upsert_node(NodeType.OBJECT, "wall")
    for _ in range(4):
        g.upsert_edge(blocked, EdgeType.BLOCKED_BY, wall)
    g.upsert_node(NodeType.STIMULUS_PATTERN, "absence")
    return g


def test_predicts_next_signal_from_graph():
    predictor = WorldModelPredictor()
    prediction = predictor.predict_next({"context": "awake",
                                         "action": "approach"},
                                        _trained_graph())
    assert prediction.next_signal_type == "Stimulus"
    assert prediction.next_valence_bucket == "positive"
    assert prediction.likely_blocked_action == "move_north"
    assert prediction.likely_useful_action == "approach"
    assert prediction.basis  # every field explains itself


def test_scores_hit_and_miss():
    predictor = WorldModelPredictor()
    graph = _trained_graph()
    prediction = predictor.predict_next({"context": "awake",
                                         "action": "approach"}, graph)
    hit = predictor.score_prediction(prediction, {
        "signal_type": "Stimulus", "valence_bucket": "positive",
        "is_absence": False})
    assert hit["hit"] is True
    prediction = predictor.predict_next({"context": "awake",
                                         "action": "approach"}, graph)
    miss = predictor.score_prediction(prediction, {
        "signal_type": "LogosTension", "valence_bucket": "negative",
        "is_absence": True})
    assert miss["hit"] is False
    assert predictor.prediction_count == 2
    assert predictor.accuracy() == 0.5
    snap = predictor.snapshot()
    assert "never execute" in snap["note"]


def test_handles_insufficient_evidence():
    predictor = WorldModelPredictor()
    prediction = predictor.predict_next({}, KnowledgeGraph())
    assert prediction.next_signal_type is None
    assert "next_signal_type" in prediction.insufficient_evidence
    # An unscoreable prediction is not counted as a hit or a miss.
    score = predictor.score_prediction(prediction, {})
    assert score["scored_fields"] == 0
    assert predictor.prediction_count == 0
    assert predictor.accuracy() is None


def test_silence_predicts_latent_transition():
    predictor = WorldModelPredictor()
    graph = _trained_graph()
    quiet = predictor.predict_next({"silence_duration": 6}, graph)
    assert quiet.likely_context_transition == "quiet"
    asleep = predictor.predict_next({"silence_duration": 15}, graph)
    assert asleep.likely_context_transition == "sleep"
    assert asleep.absence_after_silence is True


def test_feeds_anticipation_and_mysterium():
    from solaris_ai_nn.latent import AnticipationTracker, MysteriumTracker

    anticipation = AnticipationTracker()
    mysterium = MysteriumTracker(pressure=0.5)
    predictor = WorldModelPredictor(anticipation=anticipation,
                                    mysterium=mysterium)
    graph = _trained_graph()
    prediction = predictor.predict_next({"action": "approach"}, graph)
    assert anticipation._pending is not None  # graph prior fed forward
    before = mysterium.pressure
    predictor.score_prediction(prediction, {
        "signal_type": "Stimulus", "valence_bucket": "positive",
        "is_absence": False})
    assert mysterium.pressure <= before  # a hit drains unknown pressure
