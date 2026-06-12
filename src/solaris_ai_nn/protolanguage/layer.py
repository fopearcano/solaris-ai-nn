"""ProtoLanguageLayer -- the wired pipeline from repetition to signs.

One ``process_context(context)``: the emergence engine scans for
patterns worth naming, accepted symbols are grounded, observed symbol
streams fold into sequences, the syntax probe infers and tests
regularities, and compression/prediction utility feed back into symbol
confidence. The layer observes and names; it has no authority anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .combinatorics import SymbolCombinator
from .compression import SymbolCompressionEvaluator
from .prediction_utility import SymbolPredictionEvaluator
from .safety import ProtoLanguageSafetyValidator
from .semantic_grounding import SemanticGroundingEngine
from .symbol_emergence import SymbolEmergenceEngine
from .symbol_memory import SymbolMemory
from .symbol_registry import SymbolRegistry
from .translation import ProtoLanguageTranslator
from .utterance import ProtoUtteranceBuilder

LAYER_NOTE = ("an emergent proto-symbolic layer: internal signs from "
              "repeated experience, utility-tested -- not human "
              "language, not understanding, never authority")


@dataclass
class ProtoLanguageLayer:
    """Owns the proto-language machinery; names things, decides nothing."""

    state_dir: Optional[Union[str, Path]] = None
    min_repetition: int = 3

    def __post_init__(self) -> None:
        self.registry = SymbolRegistry(state_dir=self.state_dir)
        self.emergence = SymbolEmergenceEngine(
            registry=self.registry, min_repetition=self.min_repetition)
        self.combinator = SymbolCombinator()
        from .syntax_probe import SyntaxProbe

        self.syntax = SyntaxProbe()
        self.grounding = SemanticGroundingEngine()
        self.compression = SymbolCompressionEvaluator()
        self.prediction = SymbolPredictionEvaluator()
        self.memory = SymbolMemory(state_dir=self.state_dir)
        self.utterances = ProtoUtteranceBuilder(registry=self.registry)
        self.translator = ProtoLanguageTranslator(registry=self.registry)
        self.safety = ProtoLanguageSafetyValidator()
        self.scans = 0
        self.first_stable_symbol: Optional[str] = None
        self.report_path: Optional[str] = None

    # -- the pipeline -----------------------------------------------------------------

    def process_context(self, context: Dict[str, Any],
                        lifetime_s: float = 0.0) -> Dict[str, Any]:
        """One emergence/grounding/sequence pass over recorded context."""
        self.scans += 1
        candidates = self.emergence.scan_context(context)
        born_before = self.registry.snapshot()["symbol_count"]
        accepted = self.emergence.propose_symbols(candidates)
        for symbol in accepted:
            self.safety.validate_symbol(symbol, context)
            self.grounding.ground_symbol(symbol, {
                "context": context.get("label", "scan"),
                "evidence_kind": ("offline"
                                  if context.get("offline_replay")
                                  else "real"),
                **{k: v for k, v in context.items()
                   if k in ("signal_pattern", "need_state",
                            "action_tendency", "reaction_valence",
                            "world_model_node", "boundary",
                            "mysterium_change")}})
            if symbol.observation_count <= len(candidates):
                self.memory.record("birth", token=symbol.token,
                                   symbol_id=symbol.symbol_id,
                                   detail=symbol.metadata.get(
                                       "trigger", ""),
                                   lifetime_s=lifetime_s)
        # Observed symbol streams fold into sequences + transitions.
        stream = context.get("symbol_stream") or []
        if stream:
            self.combinator.observe_sequence(
                stream, {"label": context.get("label", ""),
                         "outcome_valence":
                             context.get("outcome_valence")})
            self.prediction.train_counts([stream])
        repeated = self.combinator.find_repeated_sequences(
            self.min_repetition)
        for sequence in repeated[:10]:
            self.combinator.score_sequence_utility(sequence)
        new_rules = self.syntax.infer_rules(repeated)
        for rule in new_rules:
            self.memory.record("rule_emergence",
                               detail=">".join(rule.pattern),
                               lifetime_s=lifetime_s)
        # Stable-symbol bookkeeping.
        stable = self.registry.stable()
        if stable and self.first_stable_symbol is None:
            self.first_stable_symbol = stable[0].token
        born = (self.registry.snapshot()["symbol_count"] - born_before)
        return {"candidates": len(candidates), "accepted": len(accepted),
                "born": born, "repeated_sequences": len(repeated),
                "new_rules": len(new_rules)}

    # -- utility passes -----------------------------------------------------------------

    def evaluate_trace(self, trace: List[Any]) -> Dict[str, Any]:
        """Symbolize a trace and feed compression value back."""
        symbolized = self.compression.symbolize_trace(trace,
                                                      self.registry)
        report = self.compression.evaluate_compression(trace, symbolized)
        self.safety.validate_compression(report)
        self.compression.update_symbol_scores(self.registry, report,
                                              symbolized.tokens())
        return report

    def arbitration_support(self) -> Dict[str, Dict[str, float]]:
        """Validated action symbols may *bias* habit support, capped
        small; safety/governance penalties always dominate this."""
        support: Dict[str, float] = {}
        for symbol in self.registry.stable():
            if symbol.type != "action_symbol":
                continue
            if symbol.prediction_score <= 0.0:
                continue  # only utility-validated symbols may bias
            key = str(symbol.metadata.get("grounding_key", "")
                      ).split(":")[-1]
            if key:
                support[key] = round(
                    min(0.3, symbol.prediction_score * 0.3), 4)
        return {"habit_support": support} if support else {}

    # -- views / persistence --------------------------------------------------------------

    def save_state(self) -> None:
        self.registry.save()
        self.memory.save_rules(list(self.syntax.rules.values()))

    def summary(self) -> Dict[str, Any]:
        registry = self.registry.snapshot()
        prediction = self.prediction.compare_with_baseline()
        last_utterance = (self.utterances.last_utterance.render()
                          if self.utterances.last_utterance else None)
        return {
            "enabled": True,
            "symbol_count": registry["symbol_count"],
            "stable_symbol_count": registry["stable_count"],
            "ambiguous_symbol_count": registry["ambiguous_count"],
            "sequence_count": len(self.combinator.sequences),
            "proto_syntax_rule_count": len(self.syntax.rules),
            "validated_rule_count": len(self.syntax.validated_rules()),
            "compression_utility": self.compression.last_ratio,
            "prediction_utility": prediction.get(
                "improvement_over_baseline"),
            "first_stable_symbol": self.first_stable_symbol,
            "latest_proto_utterance": last_utterance,
            "symbol_memory_size": self.memory.snapshot()[
                "records_in_memory"],
            "last_symbol_event": (self.memory.records[-1].event
                                  if self.memory.records else None),
            "scans": self.scans,
            "proto_language_report_path": self.report_path,
            "authority": False,
            "note": LAYER_NOTE,
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "summary": self.summary(),
            "registry": self.registry.snapshot(),
            "emergence": self.emergence.snapshot(),
            "combinator": self.combinator.snapshot(),
            "syntax": self.syntax.snapshot(),
            "grounding": self.grounding.snapshot(),
            "compression": self.compression.snapshot(),
            "prediction": self.prediction.snapshot(),
            "memory": self.memory.snapshot(),
            "utterances": self.utterances.snapshot(),
            "translator": self.translator.snapshot(),
            "safety": self.safety.snapshot(),
        }

    # -- world model feed -------------------------------------------------------------

    def update_world_model(self, graph: Any) -> Dict[str, int]:
        """Proto-symbols become operational graph nodes with grounding
        edges. They are internal signs, not language understanding."""
        added = {"nodes": 0, "edges": 0}
        for symbol in self.registry.active():
            node = graph.upsert_node(
                "proto_symbol", symbol.token, source_module="protolanguage",
                ambiguity=symbol.ambiguity_score,
                stable=symbol.stable,
                note="an internal operational symbol; not language "
                     "understanding")
            added["nodes"] += 1
            for grounding in symbol.grounding_refs[:3]:
                target = graph.upsert_node(
                    "context" if grounding.dimension == "context"
                    else "unknown" if grounding.dimension
                    == "mysterium_change" else "state",
                    grounding.reference[:60],
                    source_module="protolanguage")
                graph.upsert_edge(node, "grounded_in", target,
                                  evidence=grounding.reference,
                                  offline=grounding.evidence_kind
                                  in ("offline", "counterfactual"))
                added["edges"] += 1
        return added
