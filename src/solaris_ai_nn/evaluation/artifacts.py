"""ArtifactCollector -- gather the file evidence a run left behind.

All artifacts are optional: a missing file becomes a warning, never a crash
(protocols that *require* an artifact assert on it themselves).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Canonical artifact names -> filename within a state dir.
KNOWN_ARTIFACTS = {
    "telemetry": "telemetry.json",
    "continuity_log": "continuity_log.jsonl",
    "trace_events": "trace_events.jsonl",
    "inner_map": "inner_map.json",
    "session_report": "session_report.md",
    "plasticity_audit": "plasticity_audit.jsonl",
    "embodiment_state": "embodiment_state.json",
    "substrate_manifest": "substrate_manifest.json",
    "benchmark_result": "benchmark_result.json",
    "benchmark_result_md": "benchmark_result.md",
}


@dataclass
class ArtifactCollector:
    """Collects existing artifact paths from a run's state directory."""

    state_dir: Union[str, Path]
    warnings: List[str] = field(default_factory=list)

    def collect(self, required: Optional[List[str]] = None) -> Dict[str, str]:
        """Return name -> path for artifacts that exist; warn on the rest."""
        base = Path(self.state_dir)
        found: Dict[str, str] = {}
        required = required or []
        for name, filename in KNOWN_ARTIFACTS.items():
            path = base / filename
            if path.exists():
                found[name] = str(path)
            else:
                message = f"artifact {name!r} missing ({path})"
                self.warnings.append(message)
                if name in required:
                    raise FileNotFoundError(message)
        return found

    def to_dict(self) -> Dict[str, Any]:
        return {"state_dir": str(self.state_dir),
                "artifacts": self.collect(),
                "warnings": list(self.warnings)}
