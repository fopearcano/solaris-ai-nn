"""World model: a transparent, persistent graph of observed structure.

The first neuro-symbolic memory layer: the neural substrate keeps reacting
continuously while this package distils recurring stimuli, entities,
actions, reactions, contexts, boundaries, and candidate causal relations
into a plain-dict KnowledgeGraph -- inspectable, serializable, prunable by
synthesis-through-subtraction, and honestly hedged. Not a vector database,
not an LLM memory, and not "understanding" in any human sense.
"""

from .associations import (  # noqa: F401
    ASSOCIATION_KINDS,
    Association,
    AssociationLearner,
)
from .builder import WorldModelBuilder  # noqa: F401
from .causal_model import CausalAssociationModel, CausalCandidate  # noqa: F401
from .context import CONTEXTS, ContextState, ContextTracker  # noqa: F401
from .edges import EdgeType, GraphEdge, edge_id_for  # noqa: F401
from .extractors import (  # noqa: F401
    EmbodimentGraphExtractor,
    LanguageGraphExtractor,
    LatentGraphExtractor,
    PilotStreamGraphExtractor,
    SignalGraphExtractor,
)
from .graph import KnowledgeGraph  # noqa: F401
from .nodes import GraphNode, NodeType, node_id_for, slug  # noqa: F401
from .prediction import WorldModelPredictor, WorldPrediction  # noqa: F401
from .pruning import GraphSynthesisPruner  # noqa: F401
from .query import WorldModelQueryInterface  # noqa: F401
from .reports import WORLD_MODEL_LIMITATIONS, WorldModelReportBuilder  # noqa: F401
from .safety import WorldModelSafety, WorldModelSafetyReport  # noqa: F401
from .serialization import (  # noqa: F401
    load_graph,
    load_graph_jsonl,
    save_graph,
    save_graph_exports,
    save_graph_jsonl,
)

__all__ = [
    "KnowledgeGraph", "GraphNode", "GraphEdge", "NodeType", "EdgeType",
    "node_id_for", "edge_id_for", "slug",
    "WorldModelBuilder",
    "SignalGraphExtractor", "EmbodimentGraphExtractor",
    "LanguageGraphExtractor", "LatentGraphExtractor",
    "PilotStreamGraphExtractor",
    "AssociationLearner", "Association", "ASSOCIATION_KINDS",
    "CausalAssociationModel", "CausalCandidate",
    "ContextTracker", "ContextState", "CONTEXTS",
    "WorldModelPredictor", "WorldPrediction",
    "GraphSynthesisPruner",
    "save_graph", "load_graph", "save_graph_jsonl", "load_graph_jsonl",
    "save_graph_exports",
    "WorldModelSafety", "WorldModelSafetyReport",
    "WorldModelReportBuilder", "WORLD_MODEL_LIMITATIONS",
    "WorldModelQueryInterface",
]
