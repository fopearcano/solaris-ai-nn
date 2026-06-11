"""LLM audit log -- every adapter call on the record, hashed by default.

Each event stores the task, adapter, model, input/output hashes, the
grounding and ClaimGuard verdicts, and whether fallback fired. Full
prompts/outputs are NOT stored unless debug mode is explicitly enabled --
hashes are enough to prove what happened without retaining content.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def text_hash(text: str) -> str:
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()[:16]


@dataclass
class LLMAuditEvent:
    """One adapter call, content-free by default."""

    request_id: str = ""
    task_type: str = ""
    adapter_type: str = ""
    model_name: str = ""
    input_hash: str = ""
    output_hash: str = ""
    grounding_passed: Optional[bool] = None
    claim_guard_passed: Optional[bool] = None
    fallback_used: bool = False
    refusal_reason: str = ""
    safety_decision: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class LLMAuditLog:
    """Bounded in memory, append-only JSONL on disk."""

    state_dir: Optional[Union[str, Path]] = None
    debug_store_content: bool = False
    max_events: int = 500
    events: List[LLMAuditEvent] = field(default_factory=list, init=False)
    rows_written: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.path = (Path(self.state_dir) / "llm_audit.jsonl"
                     if self.state_dir else None)

    def record(self, request: Any = None, response: Any = None,
               grounding_passed: Optional[bool] = None,
               claim_guard_passed: Optional[bool] = None,
               fallback_used: bool = False,
               safety_decision: str = "",
               adapter_type: str = "",
               metadata: Optional[Dict[str, Any]] = None,
               ) -> LLMAuditEvent:
        input_text = str(getattr(request, "input_text", "") or "")
        output_text = str(getattr(response, "output_text", "") or "")
        event = LLMAuditEvent(
            request_id=str(getattr(request, "request_id", "") or ""),
            task_type=str(getattr(request, "task_type", "") or ""),
            adapter_type=adapter_type
            or str(getattr(response, "raw_model_name", "") or ""),
            model_name=str(getattr(response, "raw_model_name", "") or ""),
            input_hash=text_hash(input_text) if input_text else "",
            output_hash=text_hash(output_text) if output_text else "",
            grounding_passed=grounding_passed,
            claim_guard_passed=claim_guard_passed,
            fallback_used=fallback_used,
            refusal_reason=str(getattr(response, "refusal_reason", "")
                               or ""),
            safety_decision=safety_decision,
            evidence_refs=list(getattr(response, "used_context_refs", [])
                               or [])[:8],
            metadata=dict(metadata or {}))
        if self.debug_store_content:
            event.metadata["debug_input"] = input_text[:400]
            event.metadata["debug_output"] = output_text[:400]
        self.events.append(event)
        self.events = self.events[-self.max_events:]
        self._write(event)
        return event

    def _write(self, event: LLMAuditEvent) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict(), default=str) + "\n")
        self.rows_written += 1

    # -- views --------------------------------------------------------------------

    def fallback_count(self) -> int:
        return sum(1 for e in self.events if e.fallback_used)

    def grounding_failure_count(self) -> int:
        return sum(1 for e in self.events
                   if e.grounding_passed is False)

    def claim_guard_failure_count(self) -> int:
        return sum(1 for e in self.events
                   if e.claim_guard_passed is False)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "events_in_memory": len(self.events),
            "rows_written": self.rows_written,
            "path": str(self.path) if self.path else None,
            "fallback_count": self.fallback_count(),
            "grounding_failure_count": self.grounding_failure_count(),
            "claim_guard_failure_count":
                self.claim_guard_failure_count(),
            "debug_store_content": self.debug_store_content,
            "recent": [e.to_dict() for e in self.events[-5:]],
        }
