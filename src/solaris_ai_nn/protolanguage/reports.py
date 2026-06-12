"""Proto-language reports and queries -- cautious words for emergent signs.

The report covers symbol counts, the newest/strongest/ambiguous/extinct
symbols, repeated sequences, proto-syntactic regularities, compression
and prediction utility, grounding stability, and example utterances, with
mandatory limitations. The query interface answers seven fixed questions
-- including "is this human language?" with the only honest answer: no.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Union

from ..language.query import normalize
from ..language.reporting import ExperimentReportBuilder, SessionReport
from ..language.schemas import QueryResult

PROTO_LANGUAGE_LIMITATIONS = [
    "Proto-symbols are internal operational signs grounded in recorded "
    "structure; they are not human language and imply no understanding.",
    "Symbol utility is measured (compression, prediction, grounding "
    "stability); a useless or ambiguous symbol is a finding, not a "
    "failure to hide.",
    "Proto-syntactic regularities are tested statistical patterns over "
    "internal symbols, never human grammar.",
    "Translations are inspection-only renderings that create no facts "
    "and mark their own uncertainty.",
    "No LLM and no human feedback shaped these symbols; repetition and "
    "utility did. No consciousness claim is made.",
]

HUMAN_LANGUAGE_ANSWER = (
    "No. It is an internal proto-symbolic system. It can be translated "
    "for inspection, but it is not human language.")


class ProtoLanguageReportBuilder:
    """Builds the proto-language report from a ProtoLanguageLayer."""

    def __init__(self, layer: Any) -> None:
        self.layer = layer

    def build(self) -> SessionReport:
        layer = self.layer
        snap = layer.snapshot()
        summary = snap["summary"]
        symbols = sorted(layer.registry.symbols.values(),
                         key=lambda s: -s.confidence)
        newest = sorted(layer.registry.symbols.values(),
                        key=lambda s: -s.created_at)[:5]
        extinct = [s for s in layer.registry.symbols.values()
                   if s.status in ("extinct", "stale", "merged")]
        mysterium = layer.registry.find_by_type("unknown_symbol")
        milestones = layer.registry.find_by_type("milestone_symbol")
        examples = ([layer.utterances.last_utterance.to_dict()]
                    if layer.utterances.last_utterance else
                    ["no proto-utterances built yet"])
        report = (
            ExperimentReportBuilder(title="Proto-language report")
            .add_metadata(symbol_count=summary["symbol_count"],
                          stable=summary["stable_symbol_count"],
                          rules=summary["proto_syntax_rule_count"])
            .add_section("symbol_count_by_type",
                         snap["registry"]["by_type"]
                         or {"none": "no symbols yet"})
            .add_section("newest_symbols",
                         [s.token for s in newest]
                         or ["no symbols yet"])
            .add_section("strongest_symbols",
                         [{"token": s.token,
                           "confidence": s.confidence,
                           "observations": s.observation_count}
                          for s in symbols[:5]]
                         or ["no symbols yet"])
            .add_section("ambiguous_symbols",
                         [s.token for s in layer.registry.ambiguous()]
                         or ["none marked ambiguous"])
            .add_section("extinct_or_decayed_symbols",
                         [s.token for s in extinct]
                         or ["none extinct yet"])
            .add_section("repeated_symbol_sequences",
                         snap["combinator"]["top_sequences"]
                         or ["no repeated sequences yet"])
            .add_section("proto_syntactic_regularities",
                         snap["syntax"]["top_rules"]
                         or ["no regularities inferred yet"])
            .add_section("compression_utility", snap["compression"])
            .add_section("prediction_utility", snap["prediction"])
            .add_section("grounding_stability", snap["grounding"])
            .add_section("mysterium_related_symbols",
                         [s.token for s in mysterium]
                         or ["none yet"])
            .add_section("milestones_as_symbols",
                         [s.token for s in milestones]
                         or ["none yet"])
            .add_section("example_proto_utterances", examples)
        )
        for limitation in PROTO_LANGUAGE_LIMITATIONS:
            report.add_limitation(limitation)
        return report.build()

    def to_dict(self) -> Dict[str, Any]:
        return self.build().to_dict()

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    def to_markdown(self) -> str:
        return self.build().to_markdown()

    def save(self, json_path: Union[str, Any],
             md_path: Union[str, Any]) -> Dict[str, Any]:
        from ..language.serialization import save_report

        scan = save_report(self.build(), json_path, md_path)
        self.layer.report_path = str(md_path)
        return {"json": str(json_path), "markdown": str(md_path),
                "claim_guard": scan.to_dict()}


class ProtoLanguageQueryInterface:
    """Seven fixed queries answered in cautious vocabulary."""

    def __init__(self, layer: Any) -> None:
        self.layer = layer
        self._handlers: Dict[str, Callable[[], "tuple[str, float]"]] = {
            "what symbols emerged": self._emerged,
            "what does this symbol mean": self._meaning,
            "show proto-utterances": self._utterances,
            "did symbols improve prediction": self._prediction,
            "what symbols are ambiguous": self._ambiguous,
            "what is the first stable symbol": self._first_stable,
            "is this human language": self._human_language,
        }

    def supported_queries(self) -> List[str]:
        return sorted(self._handlers)

    def answer(self, query: str, token: str = "") -> QueryResult:
        handler = self._handlers.get(normalize(query))
        if handler is None:
            return QueryResult(
                query=query, answered=False, confidence=0.0,
                text=("The system does not know how to answer that "
                      "query. Supported queries: "
                      + "; ".join(self.supported_queries()) + "."))
        text, confidence = (handler(token)
                            if handler == self._meaning else handler())
        return QueryResult(query=query, answered=confidence > 0.0,
                           text=text, confidence=confidence)

    # -- handlers ---------------------------------------------------------------

    def _emerged(self) -> "tuple[str, float]":
        registry = self.layer.registry.snapshot()
        if not registry["symbol_count"]:
            return ("No symbols emerged yet; repetition has not crossed "
                    "the naming threshold.", 0.6)
        newest = sorted(self.layer.registry.symbols.values(),
                        key=lambda s: -s.created_at)[:5]
        return (f"The registry holds {registry['symbol_count']} "
                f"internally generated symbol(s) "
                f"({registry['stable_count']} stable). Newest: "
                + ", ".join(s.token for s in newest)
                + ". Each is grounded in recorded evidence.", 0.9)

    def _meaning(self, token: str = "") -> "tuple[str, float]":
        if not token:
            return ("Name a token to look up; meaning here is "
                    "operational grounding, not human understanding.",
                    0.5)
        symbol = self.layer.registry.find_by_token(token)
        if symbol is None:
            return (f"No symbol with token {token!r} exists.", 0.6)
        refs = [g.reference for g in symbol.grounding_refs[:3]]
        return (f"{symbol.token} is grounded in: "
                + "; ".join(refs)
                + f" (observed {symbol.observation_count}x, ambiguity "
                  f"{symbol.ambiguity_score}). This is operational "
                  "grounding, not human understanding.", 0.85)

    def _utterances(self) -> "tuple[str, float]":
        last = self.layer.utterances.last_utterance
        if last is None:
            return ("No proto-utterances have been built yet.", 0.6)
        translation = (last.human_debug_translation
                       or self.layer.translator.translate_utterance(
                           last))
        return (f"The latest proto-utterance is {last.render()} "
                f"(purpose: {last.purpose}). Debug translation: "
                f"{translation}", 0.85)

    def _prediction(self) -> "tuple[str, float]":
        comparison = self.layer.prediction.compare_with_baseline()
        if comparison["predictions_scored"] == 0:
            return ("No symbol predictions have been scored yet; there "
                    "is no evidence either way.", 0.6)
        improvement = comparison["improvement_over_baseline"]
        if improvement and improvement > 0:
            return (f"Symbol-conditioned prediction scored "
                    f"{comparison['symbolic_accuracy']} vs baseline "
                    f"{comparison['baseline_accuracy']} "
                    f"(improvement {improvement:+}). The improvement "
                    "is measured, not proof of understanding.", 0.85)
        return (f"Symbols did not improve prediction this window "
                f"(symbolic {comparison['symbolic_accuracy']} vs "
                f"baseline {comparison['baseline_accuracy']}). That is "
                "reported honestly as a finding.", 0.85)

    def _ambiguous(self) -> "tuple[str, float]":
        ambiguous = self.layer.registry.ambiguous()
        if not ambiguous:
            return ("No symbols are currently marked ambiguous.", 0.7)
        return ("Ambiguous symbols (kept ambiguous, not resolved by "
                "fiat): " + ", ".join(s.token for s in ambiguous[:6])
                + ".", 0.85)

    def _first_stable(self) -> "tuple[str, float]":
        first = self.layer.first_stable_symbol
        if first is None:
            return ("No symbol has reached stability yet.", 0.6)
        return (f"The first stable symbol was {first}; stability means "
                "repeated, consistently grounded observation -- nothing "
                "more.", 0.9)

    def _human_language(self) -> "tuple[str, float]":
        from .reports import HUMAN_LANGUAGE_ANSWER

        return (HUMAN_LANGUAGE_ANSWER, 0.95)
