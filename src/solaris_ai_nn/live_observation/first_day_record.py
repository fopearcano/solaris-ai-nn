"""First-day live record -- a plain account of Solaris's first observed day.

:class:`FirstDayRecordBuilder` writes ``FIRST_DAY_RECORD_<run_id>.md`` / ``.json``: a
plain, honest account of the first bounded hours of live read-only observation --
which sources spoke, which were silent, the source diet, the rhythm and absence
picture, the load (overload/deprivation) status, the report-only metabolism
calibration, and the advisory stability decision.

The record carries a mandatory disclaimer: this is an operational observation log of
a bounded read-only exposure. It is not a birth in any biological sense and makes no
claim of consciousness, sentience, life, personhood, agency, free will, emotion,
feeling, understanding, self-awareness, or subjective experience.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_DISCLAIMER = (
    "This first-day record is an operational observation log of a bounded, "
    "local, read-only exposure to environmental events. It is not a birth in any "
    "biological sense. It makes no claim of consciousness, sentience, biological "
    "life, personhood, agency, free will, emotion, feeling, understanding, "
    "self-awareness, or subjective experience. Nothing was learned, no concept "
    "was formed, no sign was born, and no feeder, hardware, network, or source "
    "was controlled or modified.")


@dataclass
class FirstDayRecordBuilder:
    """Builds the first-day live observation record (Markdown + JSON)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.observation_status()
        record = {
            "run_id": rt.run_id,
            "disclaimer": _DISCLAIMER,
            "status": status,
            "windows": rt.windows,
            "source_health": rt.source_health_summary,
            "source_diet": rt.source_diet,
            "rhythm": rt.rhythm,
            "absence": rt.absence,
            "load": rt.load,
            "metabolism_calibration": rt.metabolism,
            "stability_gate": rt.stability,
            "blocked": rt.blocked,
            "blockers": list(rt.blockers),
            "operator_note": rt.operator_note,
        }
        markdown = self._render(record)
        return {"record": record, "markdown_text": markdown,
                "claim_guard_safe": _claim_guard_safe(markdown)}

    def _render(self, record: Dict[str, Any]) -> str:
        s = record["status"]
        health = record["source_health"]
        diet = record["source_diet"]
        lines = [
            "# First-Day Live Observation Record", "",
            f"_{_DISCLAIMER}_", "",
            f"- run id: {record['run_id']}",
            f"- blocked: {record['blocked']}",
            f"- observation windows: {s['live_observation_window_count']}",
            f"- accepted events: {s['live_observation_accepted_event_count']}",
            f"- quarantine rate: {s['live_observation_quarantine_rate']:.0%}",
            f"- live sources: {health.get('live_source_count', 0)} "
            f"(healthy {health.get('live_healthy_source_count', 0)}, "
            f"noisy {health.get('live_noisy_source_count', 0)}, "
            f"silent {health.get('live_silent_source_count', 0)})",
            f"- source diet balance: {diet.get('balance')} "
            f"(dominant {diet.get('dominant_source') or 'none'})",
            f"- load status: {record['load'].get('load_status')}",
            f"- metabolism calibration confidence: "
            f"{record['metabolism_calibration'].get('calibration_confidence')}",
            f"- stability status: "
            f"{record['stability_gate'].get('live_stability_status')}",
            f"- recommended next phase: "
            f"{s['live_recommended_next_phase']}",
            "",
        ]
        if record["blockers"]:
            lines += ["## Blockers", ""]
            lines += [f"- {b}" for b in record["blockers"]]
            lines.append("")
        lines += ["## Who spoke, who was silent", ""]
        for src in health.get("sources", []):
            lines.append(f"- {src['source_id']}: {src['status']} "
                         f"({src['event_count']} event(s))")
        lines += ["", "## Absence (a valid signal)", "",
                  f"- absence windows: "
                  f"{record['absence'].get('live_absence_window_count', 0)}; "
                  f"deprivation windows: "
                  f"{record['absence'].get('deprivation_window_count', 0)}", ""]
        lines += ["## Corrections to make first (advisory)", ""]
        corrections = record["stability_gate"].get("corrections", []) or \
            ["none -- continue observation"]
        lines += [f"- {c}" for c in corrections]
        lines += ["", "_Operational observation only; not learning, not a "
                  "biological birth, no inner-state claim._"]
        return "\n".join(lines)

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        built = self.build()
        base = os.path.join(state_dir or self.runtime.state_dir, "observation",
                            "first_day")
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, f"FIRST_DAY_RECORD_{self.runtime.run_id}.md")
        json_path = os.path.join(base,
                                 f"FIRST_DAY_RECORD_{self.runtime.run_id}.json")
        markdown = built["markdown_text"]
        if not built["claim_guard_safe"]:
            markdown = _guard(markdown)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(built["record"], fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path}


def _claim_guard_safe(text: str) -> bool:
    try:
        from ..governance.compliance import ClaimGuard

        return ClaimGuard().scan_text(text).safe
    except Exception:
        return True


def _guard(text: str) -> str:
    try:
        from ..governance.compliance import ClaimGuard

        guard = ClaimGuard()
        if not guard.scan_text(text).safe:
            return guard.rewrite(text)
    except Exception:
        pass
    return text
