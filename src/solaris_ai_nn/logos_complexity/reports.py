"""LOGOS reports -- what tensions exist, what was synthesized, what is kept.

The report describes the complexity band, a tension summary, top/recurring/
preserved tensions, synthesis candidates and outcomes, the Esc state, and the
relations to Mysterium / proto-language / world model / hypotheses /
auto-regeneration, plus structural change from tension -- with mandatory
limitations and a ClaimGuard pass before any Markdown is written.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Union

from ..language.reporting import ExperimentReportBuilder, SessionReport

LOGOS_LIMITATIONS = [
    "LOGOS is a tension engine, not an authority: it exposes fracture and "
    "proposes bounded resolution paths; it does not decide truth.",
    "A tension is not an error by default -- some contradictions are "
    "preserved as productive, unresolved evidence.",
    "Synthesis is proposed, not assumed true; it is reversible and "
    "low-risk where possible, and safety/governance/executive remain "
    "authoritative.",
    "Complexity has inert / productive / overloaded bands; this is an "
    "operational regulation signal, not a consciousness or life score.",
    "Esc is an instability signal, not an emotion; offline/counterfactual "
    "evidence is never treated as real, and no truth claim is made without "
    "evidence.",
]


class LogosComplexityReportBuilder:
    """Builds the LOGOS report from an engine snapshot."""

    def __init__(self, engine: Any) -> None:
        self.engine = engine

    def build(self) -> SessionReport:
        from .tension import TensionSeverity

        snap = self.engine.snapshot()
        complexity = snap.get("complexity") or {}
        opposition = snap.get("opposition_memory") or {}
        tensions = list(getattr(self.engine.opposition_memory, "tensions",
                               {}).values()) if hasattr(
            self.engine, "opposition_memory") else []
        top = sorted(tensions,
                     key=lambda t: TensionSeverity.ORDER.get(t.severity, 0),
                     reverse=True)[:5]
        esc_state = (snap.get("esc") or {}).get("last_state")
        builder = (
            ExperimentReportBuilder(title="LOGOS complexity report")
            .add_metadata(
                complexity_band=complexity.get("band"),
                tension_count=opposition.get("tension_count"),
                esc_triggered=(esc_state.get("triggered")
                               if isinstance(esc_state, dict) else None))
            .add_section("current_complexity_band", complexity)
            .add_section("tension_summary",
                         opposition.get("counts_by_status")
                         or {"none": "no tensions yet"})
            .add_section("top_active_tensions",
                         [self._brief(t) for t in top])
            .add_section("recurring_tensions", {
                "recurring_count": opposition.get("recurring_count")})
            .add_section("preserved_tensions", {
                "preserved_count": opposition.get("preserved_count")})
            .add_section("synthesis_candidates", snap.get("synthesis"))
            .add_section("synthesis_applied", {
                "applied": (snap.get("synthesis") or {}).get(
                    "applied_total"),
                "successful": opposition.get("successful_synthesis")})
            .add_section("synthesis_refused", {
                "refused": (snap.get("synthesis") or {}).get("refused_total"),
                "failed": opposition.get("failed_synthesis")})
            .add_section("esc_state", snap.get("esc"))
            .add_section("relation_to_mysterium", {
                "note": "Mysterium feeds unresolved-tension pressure; LOGOS "
                        "does not resolve the unknown by fiat"})
            .add_section("relation_to_proto_language", {
                "became_symbols": opposition.get("became_symbols")})
            .add_section("relation_to_world_model", {
                "note": "world-model contradictions feed tensions; "
                        "contradiction evidence is preserved"})
            .add_section("relation_to_hypotheses", {
                "became_hypotheses": opposition.get("became_hypotheses")})
            .add_section("relation_to_auto_regeneration", {
                "note": "overload/complexity tensions may request "
                        "auto-regeneration diagnostics"})
            .add_section("structural_change_from_tension", {
                "tension_to_growth_delta": snap.get(
                    "tension_to_growth_delta")})
        )
        for limitation in LOGOS_LIMITATIONS:
            builder.add_limitation(limitation)
        return builder.build()

    @staticmethod
    def _brief(t: Any) -> Dict[str, Any]:
        return {"id": t.tension_id, "type": t.tension_type,
                "poles": f"{t.polarity_a} vs {t.polarity_b}",
                "severity": t.severity, "status": t.status}

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
        return {"json": str(json_path), "markdown": str(md_path),
                "claim_guard": scan.to_dict()}


class LogosComplexityQueryInterface:
    """Fixed queries about LOGOS dynamics, in safe, grounded wording."""

    CONTRADICTION_ANSWER = (
        "No. A contradiction is preserved as unresolved evidence, not "
        "treated as truth. No truth claim is made without evidence.")

    def __init__(self, engine: Any) -> None:
        self.engine = engine
        self._handlers = {
            "what tensions are active": self._active,
            "what is the current complexity band": self._band,
            "what was synthesized": self._synthesized,
            "what tension was preserved": self._preserved,
            "why was synthesis refused": self._refused,
            "what triggered esc": self._esc,
            "is contradiction being treated as truth": self._contradiction,
            "did logos produce structural change": self._structural,
        }

    def supported_queries(self):
        return sorted(self._handlers)

    def answer(self, query: str):
        from ..language.query import normalize
        from ..language.schemas import QueryResult

        handler = self._handlers.get(normalize(query))
        if handler is None:
            return QueryResult(
                query=query, answered=False, confidence=0.0,
                text=("The system does not know how to answer that query. "
                      "Supported queries: "
                      + "; ".join(self.supported_queries()) + "."))
        text, confidence, refs = handler()
        return QueryResult(query=query, answered=confidence > 0.0,
                           text=text, data={"evidence_refs": refs},
                           confidence=confidence)

    def _snap(self):
        return self.engine.snapshot()

    def _active(self):
        opp = self._snap().get("opposition_memory") or {}
        return (f"There are {opp.get('unresolved_count', 0)} unresolved and "
                f"{opp.get('tension_count', 0)} total tension(s). A tension "
                "was detected between opposed internal poles.", 0.8,
                ["field:opposition_memory"])

    def _band(self):
        band = (self._snap().get("complexity") or {}).get("band")
        return (f"The current complexity band is {band!r} (an operational "
                "regulation signal, not a consciousness or life score).", 0.8,
                ["field:complexity.band"])

    def _synthesized(self):
        syn = self._snap().get("synthesis") or {}
        return (f"{syn.get('applied_total', 0)} synthesis candidate(s) were "
                "applied. The synthesis candidate proposes a bounded "
                "resolution; it is not assumed true.", 0.7,
                ["field:synthesis.applied_total"])

    def _preserved(self):
        opp = self._snap().get("opposition_memory") or {}
        return (f"{opp.get('preserved_count', 0)} tension(s) are preserved as "
                "productive, unresolved evidence.", 0.7,
                ["field:opposition_memory.preserved_count"])

    def _refused(self):
        results = (self.engine.opposition_memory.synthesis_results
                   if hasattr(self.engine, "opposition_memory") else [])
        refused = [r for r in results if r.get("refused")]
        if refused:
            return (f"The last synthesis was refused because: "
                    f"{refused[-1].get('refused_reason')}.", 0.8,
                    ["field:synthesis_results"])
        return ("No synthesis is currently refused.", 0.5, [])

    def _esc(self):
        esc = (self._snap().get("esc") or {}).get("last_state") or {}
        if esc.get("triggered"):
            return (f"Esc triggered by: {esc.get('triggers')}. Esc is an "
                    "instability signal, not an emotion.", 0.8,
                    ["field:esc.last_state"])
        return ("Esc is not currently triggered. Esc is an instability "
                "signal, not an emotion.", 0.6, ["field:esc"])

    def _contradiction(self):
        return (self.CONTRADICTION_ANSWER, 0.95,
                ["field:safety.logos_has_authority"])

    def _structural(self):
        delta = self._snap().get("tension_to_growth_delta")
        if delta is None:
            return ("Structural change from tension has not been measured "
                    "yet.", 0.4, [])
        return (f"The tension-to-structural-change delta is {delta}.", 0.6,
                ["field:tension_to_growth_delta"])
