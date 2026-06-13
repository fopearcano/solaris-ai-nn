"""Hypothesis reports -- what was wondered, tested, supported, and refused.

The report describes hypotheses by status, the newest and highest-priority
candidates, supported / falsified / inconclusive / unsafe-to-test sets, an
evidence summary, the designs that ran, world-model and proto-language
updates that came from supported hypotheses, and long-lived unknowns -- with
mandatory limitations and a ClaimGuard pass before any Markdown is written.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Union

from ..language.reporting import ExperimentReportBuilder, SessionReport
from .hypotheses import HypothesisStatus

HYPOTHESIS_LIMITATIONS = [
    "Hypotheses are internal research artifacts, not beliefs: the system "
    "does not 'believe', 'want', or 'understand' anything stated here.",
    "Causal language is hedged -- the strongest available label is "
    "'causes candidate'; a supported hypothesis is not a proven cause.",
    "Evidence keeps its source scope; offline and counterfactual evidence "
    "is never treated as a real observation of the running system.",
    "Tests are bounded and safe (simulation / internal / read-only); there "
    "is no real-world experiment, no LLM-generated hypothesis, and no "
    "human feedback in the loop.",
    "Confidence moves in small bounded steps; one success rarely proves a "
    "hypothesis and one failure may only weaken it.",
]


class HypothesisReportBuilder:
    """Builds the hypothesis report from an engine/memory snapshot."""

    def __init__(self, engine: Any) -> None:
        self.engine = engine

    def _memory(self):
        return getattr(self.engine, "memory", None)

    def build(self) -> SessionReport:
        snap = self.engine.snapshot()
        memory = self._memory()
        counts = snap.get("memory", {}).get("counts_by_status", {})
        hyps = list(getattr(memory, "hypotheses", {}).values()) \
            if memory is not None else []
        newest = sorted(hyps, key=lambda h: h.generated_at,
                        reverse=True)[:5]
        top = sorted(hyps, key=lambda h: h.priority, reverse=True)[:5]
        builder = (
            ExperimentReportBuilder(title="Hypothesis engine report")
            .add_metadata(
                hypothesis_count=snap.get("memory", {}).get(
                    "hypothesis_count"),
                tests_run=snap.get("test_runner", {}).get("tests_run"),
                top_priority=(top[0].hypothesis_id if top else None))
            .add_section("hypothesis_count_by_status", counts
                         or {"none": "no hypotheses yet"})
            .add_section("newest_hypotheses",
                         [self._brief(h) for h in newest])
            .add_section("highest_priority_hypotheses",
                         [self._brief(h) for h in top])
            .add_section("supported_hypotheses",
                         self._by_status(memory, HypothesisStatus.SUPPORTED))
            .add_section("falsified_hypotheses",
                         self._by_status(memory, HypothesisStatus.FALSIFIED))
            .add_section("inconclusive_hypotheses",
                         self._by_status(memory,
                                         HypothesisStatus.INCONCLUSIVE))
            .add_section("unsafe_to_test_hypotheses",
                         self._by_status(memory,
                                         HypothesisStatus.UNSAFE_TO_TEST))
            .add_section("evidence_summary",
                         snap.get("test_runner", {}).get("evidence"))
            .add_section("test_designs_run", {
                "tests_run": snap.get("test_runner", {}).get("tests_run"),
                "last_result": snap.get("test_runner", {}).get(
                    "last_result")})
            .add_section("world_model_updates_from_supported", {
                "promoted_to_world_model": snap.get("memory", {}).get(
                    "promoted_to_world_model")})
            .add_section("proto_language_updates_from_supported", {
                "promoted_to_proto_symbol": snap.get("memory", {}).get(
                    "promoted_to_proto_symbol")})
            .add_section("long_lived_unknowns", {
                "count": snap.get("memory", {}).get(
                    "long_lived_unknown_count")})
        )
        for limitation in HYPOTHESIS_LIMITATIONS:
            builder.add_limitation(limitation)
        return builder.build()

    @staticmethod
    def _brief(h: Any) -> Dict[str, Any]:
        return {"id": h.hypothesis_id, "type": h.type,
                "statement": h.statement, "status": h.status,
                "confidence": h.confidence, "priority": h.priority}

    def _by_status(self, memory: Any, status: str) -> List[Dict[str, Any]]:
        if memory is None:
            return []
        return [self._brief(h) for h in memory.by_status(status)][:10]

    # -- outputs ------------------------------------------------------------------

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


class HypothesisQueryInterface:
    """Fixed queries about hypotheses, answered in safe, grounded wording."""

    def __init__(self, engine: Any) -> None:
        self.engine = engine
        self._handlers = {
            "what hypotheses exist": self._exist,
            "what is the top hypothesis": self._top,
            "what was tested": self._tested,
            "what evidence supports this": self._evidence,
            "what was falsified": self._falsified,
            "what remains unknown": self._unknown,
            "why was a test blocked": self._blocked,
            "did testing reduce mysterium": self._mysterium,
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

    def _exist(self):
        snap = self._snap()
        counts = snap.get("memory", {}).get("counts_by_status", {})
        total = snap.get("memory", {}).get("hypothesis_count", 0)
        return (f"There are {total} hypothesis candidate(s) on record "
                f"(by status: {counts}). These are internal research "
                "artifacts, not beliefs.", 0.8, ["field:memory.counts"])

    def _top(self):
        memory = getattr(self.engine, "memory", None)
        hyps = list(getattr(memory, "hypotheses", {}).values()) \
            if memory else []
        if not hyps:
            return ("No hypothesis candidates exist yet.", 0.4, [])
        top = max(hyps, key=lambda h: h.priority)
        return (f"The top hypothesis candidate is {top.hypothesis_id} "
                f"(priority {top.priority}): {top.statement}.", 0.8,
                [f"hypothesis:{top.hypothesis_id}"])

    def _tested(self):
        snap = self._snap()
        runner = snap.get("test_runner", {})
        return (f"{runner.get('tests_run', 0)} bounded test(s) have run; "
                f"{runner.get('inconclusive_count', 0)} were inconclusive.",
                0.7, ["field:test_runner"])

    def _evidence(self):
        snap = self._snap()
        ev = (snap.get("test_runner", {}).get("evidence") or {})
        return (f"Evidence so far: {ev.get('by_type', {})}; "
                f"{ev.get('offline_count', 0)} record(s) are offline and "
                "are not real observations.", 0.7,
                ["field:evidence.by_type"])

    def _falsified(self):
        snap = self._snap()
        counts = snap.get("memory", {}).get("counts_by_status", {})
        return (f"{counts.get('falsified', 0)} hypothesis candidate(s) were "
                "falsified by bounded tests.", 0.7,
                ["field:memory.counts.falsified"])

    def _unknown(self):
        snap = self._snap()
        n = snap.get("memory", {}).get("long_lived_unknown_count", 0)
        return (f"{n} long-lived unknown(s) remain: hypotheses proposed but "
                "not yet resolved. The system has not proven these "
                "relations.", 0.7, ["field:memory.long_lived_unknown_count"])

    def _blocked(self):
        snap = self._snap()
        last = snap.get("test_runner", {}).get("last_result") or {}
        if last.get("blocked"):
            return (f"The last test was blocked: {last.get('blocked_reason')}.",
                    0.8, ["field:last_result.blocked_reason"])
        return ("No test is currently blocked.", 0.5, [])

    def _mysterium(self):
        snap = self._snap()
        delta = snap.get("mysterium_reduction_after_tests")
        if delta is None:
            return ("Mysterium change after testing has not been measured "
                    "yet.", 0.4, [])
        verb = "reduced" if delta > 0 else "did not reduce"
        return (f"Testing {verb} unknown pressure on average "
                f"(delta {delta}).", 0.6, ["field:mysterium_reduction"])
