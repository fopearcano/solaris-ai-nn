"""WorldModelPredictor -- predictions from graph counts, honestly scored.

The predictor walks the graph's strongest edges to predict the likely next
signal type, reaction valence bucket, blocked action, useful GridWorld
action, absence-after-silence, context transition, and Mysterium direction.
Predictions are data: they feed the anticipation tracker and schedulers and
have no execution path. When the graph has no evidence, the prediction says
so instead of guessing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .edges import EdgeType
from .graph import KnowledgeGraph
from .nodes import NodeType, node_id_for


@dataclass
class WorldPrediction:
    """One graph-based prediction with its basis (counts, not certainty)."""

    next_signal_type: Optional[str] = None
    next_valence_bucket: Optional[str] = None
    likely_blocked_action: Optional[str] = None
    likely_useful_action: Optional[str] = None
    absence_after_silence: Optional[bool] = None
    likely_context_transition: Optional[str] = None
    mysterium_direction: Optional[str] = None
    basis: Dict[str, Any] = field(default_factory=dict)
    insufficient_evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class WorldModelPredictor:
    """Graph-count predictions; optionally feeds the anticipation tracker."""

    anticipation: Any = None  # optional latent.AnticipationTracker
    mysterium: Any = None     # optional latent.MysteriumTracker

    prediction_count: int = field(default=0, init=False)
    hit_count: int = field(default=0, init=False)
    miss_count: int = field(default=0, init=False)
    last_score: Optional[Dict[str, Any]] = field(default=None, init=False)
    _pending: Optional[WorldPrediction] = field(default=None, init=False)

    # -- prediction -----------------------------------------------------------

    def predict_next(self, context: Optional[Dict[str, Any]],
                     graph: KnowledgeGraph) -> WorldPrediction:
        ctx = context or {}
        prediction = WorldPrediction()

        def strongest_target(source_id: str, edge_type: str,
                             ) -> Optional[Any]:
            pairs = graph.neighbors(source_id, edge_type=edge_type)
            return pairs[0] if pairs else None

        # Next signal type: from the active context's predicts edges, else
        # the most-observed signal_type node.
        context_label = ctx.get("context", "awake")
        context_id = node_id_for(NodeType.CONTEXT, context_label)
        hit = strongest_target(context_id, EdgeType.PREDICTS)
        if hit is not None and hit[1].type == NodeType.SIGNAL_TYPE:
            prediction.next_signal_type = hit[1].label
            prediction.basis["next_signal_type"] = (
                f"context {context_label!r} predicts it "
                f"(weight {hit[0].weight:.2f})")
        else:
            signal_nodes = graph.find(node_type=NodeType.SIGNAL_TYPE)
            signal_nodes = [n for n in signal_nodes
                            if not n.label.startswith("modality_")]
            if signal_nodes:
                best = max(signal_nodes,
                           key=lambda n: (n.observation_count, n.node_id))
                prediction.next_signal_type = best.label
                prediction.basis["next_signal_type"] = (
                    f"most observed signal type "
                    f"(n={best.observation_count})")
            else:
                prediction.insufficient_evidence.append("next_signal_type")

        # Valence bucket for the last/intended action.
        action_label = ctx.get("action") or ctx.get("last_action")
        if action_label is not None:
            action_id = node_id_for(NodeType.ACTION, action_label)
            best_valence = None
            for edge, node in graph.neighbors(action_id,
                                              edge_type=EdgeType.PRODUCES):
                if node.type == NodeType.REACTION:
                    best_valence = (edge, node)
                    break
            if best_valence is not None:
                prediction.next_valence_bucket = best_valence[1].label.replace(
                    "valence_", "")
                prediction.basis["next_valence_bucket"] = (
                    f"{action_label!r} produced it "
                    f"{best_valence[0].observation_count}x")
            else:
                prediction.insufficient_evidence.append("next_valence_bucket")

        # Likely blocked action: the heaviest blocked_by edge in the graph.
        blocked = graph.strongest_edges(limit=1,
                                        edge_type=EdgeType.BLOCKED_BY)
        if blocked:
            prediction.likely_blocked_action = graph.nodes[
                blocked[0].source_node_id].label
            prediction.basis["likely_blocked_action"] = (
                f"blocked {blocked[0].observation_count}x by "
                f"{graph.nodes[blocked[0].target_node_id].label!r}")

        # Likely useful action: heaviest reinforces edge into an action.
        useful = [e for e in graph.strongest_edges(
            limit=10, edge_type=EdgeType.REINFORCES)
            if graph.nodes[e.target_node_id].type == NodeType.ACTION]
        if useful:
            prediction.likely_useful_action = graph.nodes[
                useful[0].target_node_id].label
            prediction.basis["likely_useful_action"] = (
                f"reinforced (weight {useful[0].weight:.2f})")
        else:
            prediction.insufficient_evidence.append("likely_useful_action")

        # Absence after silence: has the absence pattern been observed?
        absence = graph.get_node(NodeType.STIMULUS_PATTERN, "absence")
        silence = int(ctx.get("silence_duration", 0) or 0)
        if absence is not None:
            prediction.absence_after_silence = silence >= 3
            prediction.basis["absence_after_silence"] = (
                f"absence observed {absence.observation_count}x; "
                f"silence={silence}")
        else:
            prediction.insufficient_evidence.append("absence_after_silence")

        # Likely context transition: silence points latentward.
        if silence >= 10:
            prediction.likely_context_transition = "sleep"
        elif silence >= 5:
            prediction.likely_context_transition = "quiet"
        else:
            prediction.likely_context_transition = context_label

        # Mysterium direction: many unknown nodes + recent misses -> up.
        unknown_count = len(graph.find(node_type=NodeType.UNKNOWN))
        misses = int(ctx.get("miss_streak", 0) or 0)
        prediction.mysterium_direction = (
            "increase" if (misses >= 2 or unknown_count > 5) else
            "decrease" if ctx.get("prediction_hit") else "stable")
        prediction.basis["mysterium_direction"] = (
            f"unknown_nodes={unknown_count}, miss_streak={misses}")

        self._pending = prediction
        # Feed graph-based priors into the anticipation tracker if present.
        if self.anticipation is not None:
            self.anticipation.predict({
                "suggested_action": prediction.likely_useful_action})
        return prediction

    # -- scoring -------------------------------------------------------------------

    def score_prediction(self, prediction: WorldPrediction,
                         actual: Dict[str, Any]) -> Dict[str, Any]:
        fields: Dict[str, bool] = {}
        if prediction.next_signal_type is not None \
                and actual.get("signal_type") is not None:
            fields["signal_type"] = (prediction.next_signal_type
                                     == actual["signal_type"])
        if prediction.next_valence_bucket is not None \
                and actual.get("valence_bucket") is not None:
            fields["valence_bucket"] = (prediction.next_valence_bucket
                                        == actual["valence_bucket"])
        if prediction.absence_after_silence is not None \
                and actual.get("is_absence") is not None:
            fields["absence"] = (prediction.absence_after_silence
                                 == bool(actual["is_absence"]))
        hit = bool(fields) and sum(fields.values()) >= max(
            1, (len(fields) + 1) // 2)
        score = {"hit": hit, "fields": fields,
                 "scored_fields": len(fields)}
        self.update_from_score(score)
        return score

    def update_from_score(self, score: Dict[str, Any]) -> None:
        if not score.get("scored_fields"):
            return  # insufficient evidence: not counted as hit or miss
        self.prediction_count += 1
        if score["hit"]:
            self.hit_count += 1
        else:
            self.miss_count += 1
        self.last_score = score
        if self.mysterium is not None:
            self.mysterium.update({
                "prediction_hit": score["hit"],
                "prediction_miss_streak": 0 if score["hit"] else 3})

    def accuracy(self) -> Optional[float]:
        if self.prediction_count == 0:
            return None
        return round(self.hit_count / self.prediction_count, 4)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "prediction_count": self.prediction_count,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "accuracy": self.accuracy(),
            "last_score": self.last_score,
            "pending": (self._pending.to_dict()
                        if self._pending else None),
            "note": "predictions are based on graph counts; they inform "
                    "trackers and never execute anything",
        }
