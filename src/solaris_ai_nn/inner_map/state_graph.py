"""StateGraph -- a dependency-free self-map of the substrate's parts.

A lightweight directed graph (plain dicts/lists, no networkx) describing the
components of Solaris-AI-NN and how they relate. It is the NN analogue of the
assembled topology in Solaris_Ai's ``conscience.py``: a visual self-map the Inner
MAP can export. ``to_dot`` / ``to_mermaid`` render it without any dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class StateGraph:
    """A tiny directed graph of nodes and labelled edges."""

    nodes: Dict[str, Dict[str, str]] = field(default_factory=dict)
    edges: List[Tuple[str, str, str]] = field(default_factory=list)

    def add_node(self, name: str, role: str = "") -> None:
        """Add (or update) a node with an optional human role label."""
        self.nodes[name] = {"role": role}

    def add_edge(self, src: str, dst: str, label: str = "") -> None:
        """Add a directed edge ``src -> dst`` with a relationship label.

        Endpoints are auto-created as bare nodes if not already present.
        """
        self.nodes.setdefault(src, {"role": ""})
        self.nodes.setdefault(dst, {"role": ""})
        self.edges.append((src, dst, label))

    def to_dict(self) -> Dict[str, object]:
        return {
            "nodes": [{"name": n, **attrs} for n, attrs in self.nodes.items()],
            "edges": [{"src": s, "dst": d, "label": lbl} for s, d, lbl in self.edges],
        }

    def to_dot(self) -> str:
        """Render as Graphviz DOT."""
        lines = ["digraph solaris_ai_nn {", "  rankdir=LR;"]
        for name, attrs in self.nodes.items():
            role = attrs.get("role", "")
            label = f"{name}\\n({role})" if role else name
            lines.append(f'  "{name}" [label="{label}"];')
        for src, dst, lbl in self.edges:
            lines.append(f'  "{src}" -> "{dst}" [label="{lbl}"];')
        lines.append("}")
        return "\n".join(lines)

    def to_mermaid(self) -> str:
        """Render as a Mermaid flowchart."""
        lines = ["flowchart LR"]
        for name, attrs in self.nodes.items():
            role = attrs.get("role", "")
            text = f"{name}<br/>{role}" if role else name
            lines.append(f'  {name}["{text}"]')
        for src, dst, lbl in self.edges:
            arrow = f"-- {lbl} -->" if lbl else "-->"
            lines.append(f"  {src} {arrow} {dst}")
        return "\n".join(lines)


def build_default_state_graph() -> StateGraph:
    """Build the canonical Solaris-AI-NN self-map (nodes + relationships)."""
    g = StateGraph()
    for name, role in [
        ("runtime", "session loop"),
        ("bridge", "signal substrate"),
        ("reservoir", "ESN temporal state"),
        ("readout", "action tendencies"),
        ("memory", "trace + consolidation"),
        ("habit", "reinforced pathways"),
        ("synthesis", "subtractive pruning"),
        ("telemetry", "observable metrics"),
        ("continuity", "lifecycle + persistence"),
        ("boundaries", "operating limits"),
        ("tendencies", "suggested action/desire"),
        ("unknown", "drift / novelty"),
    ]:
        g.add_node(name, role)

    g.add_edge("bridge", "reservoir", "updates")
    g.add_edge("reservoir", "readout", "feeds")
    g.add_edge("readout", "tendencies", "produces")
    g.add_edge("habit", "tendencies", "biases")
    g.add_edge("synthesis", "readout", "prunes weak pathways")
    g.add_edge("synthesis", "habit", "prunes weak pathways")
    g.add_edge("bridge", "memory", "records")
    g.add_edge("reservoir", "memory", "snapshots")
    g.add_edge("telemetry", "runtime", "observes")
    g.add_edge("continuity", "runtime", "persists")
    g.add_edge("runtime", "boundaries", "respects")
    g.add_edge("reservoir", "unknown", "drift source")
    g.add_edge("inner_map", "runtime", "observes")
    g.add_edge("inner_map", "bridge", "observes")
    g.add_edge("inner_map", "memory", "observes")
    g.add_edge("inner_map", "habit", "observes")
    g.add_edge("inner_map", "synthesis", "observes")
    g.add_edge("inner_map", "boundaries", "checks")
    g.nodes["inner_map"]["role"] = "self-observation"

    # Controlled-plasticity subsystem (Prompt 5).
    for name, role in [
        ("plasticity_engine", "applies mutations"),
        ("policy", "proposes mutations"),
        ("safety_validator", "validates mutations"),
        ("rollback_manager", "undoes mutations"),
        ("audit_log", "records mutations"),
    ]:
        g.add_node(name, role)
    g.add_edge("telemetry", "policy", "informs")
    g.add_edge("inner_map", "policy", "informs")
    g.add_edge("policy", "plasticity_engine", "proposes mutation")
    g.add_edge("safety_validator", "plasticity_engine", "validates mutation")
    g.add_edge("plasticity_engine", "readout", "applies mutation")
    g.add_edge("plasticity_engine", "reservoir", "applies mutation")
    g.add_edge("plasticity_engine", "habit", "applies mutation")
    g.add_edge("plasticity_engine", "synthesis", "applies mutation")
    g.add_edge("rollback_manager", "plasticity_engine", "restores previous state")
    g.add_edge("audit_log", "plasticity_engine", "records every mutation")
    g.add_edge("boundaries", "safety_validator", "defines limits")

    # Substrate laboratory (Prompt 6).
    for name, role in [
        ("substrate_registry", "selectable substrates"),
        ("esn_substrate", "ESN baseline"),
        ("liquid_state_substrate", "liquid-state inspired"),
        ("spiking_recurrent_substrate", "binary spiking"),
        ("substrate_metrics", "shared activity metrics"),
        ("event_encoder", "signal -> vector"),
    ]:
        g.add_node(name, role)
    g.add_edge("substrate_registry", "esn_substrate", "registers")
    g.add_edge("substrate_registry", "liquid_state_substrate", "registers")
    g.add_edge("substrate_registry", "spiking_recurrent_substrate", "registers")
    # "reservoir" is the selected substrate node; it already feeds the readout.
    g.add_edge("event_encoder", "reservoir", "feeds selected substrate")
    g.add_edge("substrate_metrics", "inner_map", "feeds")
    g.add_edge("plasticity_engine", "substrate_registry",
               "may tune substrate parameters within safety bounds")

    # Solaris sidecar integration (Prompt 7). External nodes are Solaris_Ai's;
    # the sidecar only observes them and suggests -- action authority stays out.
    for name, role in [
        ("solaris_conscience_external", "Solaris_Ai organism (external)"),
        ("solaris_bus_external", "Solaris_Ai bus (external)"),
        ("solaris_nn_sidecar", "optional adaptive sidecar"),
        ("bus_connector", "observe-first subscription"),
        ("signal_mirror", "read-only signal mirror"),
        ("suggestion_channel", "suggestions only, never committed"),
    ]:
        g.add_node(name, role)
    g.add_edge("solaris_conscience_external", "solaris_bus_external", "owns")
    g.add_edge("solaris_bus_external", "bus_connector", "emits observed signals")
    g.add_edge("bus_connector", "bridge", "forwards to neural bridge")
    g.add_edge("bridge", "reservoir", "updates substrate")
    g.add_edge("bus_connector", "signal_mirror", "mirrors")
    g.add_edge("bus_connector", "suggestion_channel", "routes suggestions")
    g.add_edge("suggestion_channel", "solaris_bus_external",
               "publishes suggestions (never Actions)")
    g.add_edge("inner_map", "solaris_nn_sidecar", "observes sidecar state")
    g.add_edge("solaris_nn_sidecar", "bus_connector", "owns")
    g.add_edge("solaris_conscience_external", "solaris_conscience_external",
               "remains action authority")

    # Embodiment / sensorimotor sandbox (Prompt 8). Simulation-only.
    for name, role in [
        ("simulated_body", "body in simulation"),
        ("grid_world", "bounded 2D world"),
        ("sensors", "simulated senses"),
        ("effectors", "simulated actions"),
        ("energy_model", "simulated metabolism"),
        ("embodiment_safety", "simulation-only authority"),
        ("sensorimotor_runner", "perceive/act/learn loop"),
    ]:
        g.add_node(name, role)
    g.add_edge("grid_world", "sensors", "produces sensory data")
    g.add_edge("sensors", "bridge", "emit Stimulus")
    g.add_edge("bridge", "reservoir", "updates substrate")
    g.add_edge("bridge", "effectors", "suggests Action")
    g.add_edge("embodiment_safety", "effectors", "validates Action")
    g.add_edge("effectors", "grid_world", "act in simulation")
    g.add_edge("grid_world", "bridge", "feedback emits Reaction")
    g.add_edge("energy_model", "sensors", "internal need Stimulus")
    g.add_edge("sensorimotor_runner", "simulated_body", "drives")
    g.add_edge("inner_map", "simulated_body", "observes body/world state")
    g.add_edge("inner_map", "grid_world", "observes body/world state")

    # Internal language / explainability layer (Prompt 9).
    for name, role in [
        ("language_layer", "cross-module meaning"),
        ("meaning_trace_builder", "events -> atoms"),
        ("causal_trace_builder", "heuristic chains"),
        ("explanation_engine", "grounded explanations"),
        ("structural_summarizer", "counts, not prose"),
        ("query_interface", "deterministic queries"),
        ("report_builder", "JSON/Markdown reports"),
    ]:
        g.add_node(name, role)
    g.add_edge("bridge", "meaning_trace_builder", "signals feed")
    g.add_edge("telemetry", "structural_summarizer", "feeds")
    g.add_edge("inner_map", "explanation_engine", "feeds")
    g.add_edge("simulated_body", "explanation_engine", "embodiment feeds")
    g.add_edge("meaning_trace_builder", "causal_trace_builder", "feeds")
    g.add_edge("explanation_engine", "language_layer", "produces SystemUtterance")
    g.add_edge("query_interface", "explanation_engine", "routes queries")
    g.add_edge("structural_summarizer", "report_builder", "feeds")
    g.add_edge("report_builder", "continuity", "persists session reports")
    return g
