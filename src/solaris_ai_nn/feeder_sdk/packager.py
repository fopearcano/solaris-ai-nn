"""Feeder packager -- a local manifest of the feeders Solaris may read.

:class:`FeederPackBuilder` writes a :class:`FeederPackManifest` describing the
available feeder scripts, their modalities and output paths, schema versions,
privacy/safety notes, validation status, example commands, and what Solaris can
read. The packager never starts feeders, never installs hardware dependencies,
and never calls the network.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .blueprints import FeederBlueprintRegistry
from .contract import SCHEMA_VERSION
from .schemas import all_event_types, schema_coverage


@dataclass
class FeederPack:
    """One catalogued feeder script + its modality and output path."""

    feeder_id: str
    script: str
    modality: str
    output_path: str
    privacy_notes: List[str] = field(default_factory=list)
    safety_notes: List[str] = field(default_factory=list)
    example_command: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


# The standalone feeder scripts shipped under feeders_sdk/.
_STANDALONE_FEEDERS = (
    ("manual_log_feeder", "human_textual",
     ".solaris_ai_nn_feeders/out/manual.jsonl",
     ["contains human text; observation only, never command"]),
    ("folder_rhythm_feeder", "machine_rhythm",
     ".solaris_ai_nn_feeders/out/folder.jsonl",
     ["file metadata only; never modifies watched folder"]),
    ("system_rhythm_feeder", "machine_rhythm",
     ".solaris_ai_nn_feeders/out/sys.jsonl",
     ["harmless local rhythm; no privileged data"]),
    ("feature_file_feeder", "unknown_field",
     ".solaris_ai_nn_feeders/out/features.jsonl",
     ["normalizes external feature files; never modifies source"]),
    ("simulated_rf_feeder", "radio_frequency",
     ".solaris_ai_nn_feeders/out/rf.jsonl",
     ["simulated; not a real sensor; never decodes communications"]),
    ("simulated_echo_feeder", "ultrasound_echo",
     ".solaris_ai_nn_feeders/out/echo.jsonl", ["simulated; reflection metadata"]),
    ("simulated_vibration_feeder", "vibration",
     ".solaris_ai_nn_feeders/out/vibration.jsonl", ["simulated; rhythm features"]),
    ("simulated_magnetic_feeder", "magnetic",
     ".solaris_ai_nn_feeders/out/magnetic.jsonl", ["simulated; field features"]),
    ("simulated_thermal_feeder", "thermal_gradient",
     ".solaris_ai_nn_feeders/out/thermal.jsonl", ["simulated; gradient summary"]),
    ("multimodal_feeder_demo", "unknown_field",
     ".solaris_ai_nn_feeders/out/multimodal.jsonl",
     ["simulated multimodal; jitter/silence/drift/noise"]),
)


@dataclass
class FeederPackManifest:
    feeders: List[FeederPack] = field(default_factory=list)
    supported_modalities: List[str] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION
    schema_coverage: float = 0.0
    event_types: List[str] = field(default_factory=list)
    blueprint_count: int = 0
    safety_notes: List[str] = field(default_factory=list)
    privacy_notes: List[str] = field(default_factory=list)
    what_solaris_can_read: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feeders": [f.to_dict() for f in self.feeders],
            "supported_modalities": list(self.supported_modalities),
            "schema_version": self.schema_version,
            "schema_coverage": self.schema_coverage,
            "event_types": list(self.event_types),
            "blueprint_count": self.blueprint_count,
            "safety_notes": list(self.safety_notes),
            "privacy_notes": list(self.privacy_notes),
            "what_solaris_can_read": self.what_solaris_can_read,
            "created_at": self.created_at,
        }


@dataclass
class FeederPackBuilder:
    """Builds the feeder pack manifest + README (starts no feeder)."""

    state_dir: str = ".solaris_ai_nn_feeders"

    def build(self) -> FeederPackManifest:
        feeders = [
            FeederPack(feeder_id=fid, script=f"feeders_sdk/{fid}.py",
                       modality=modality, output_path=out, privacy_notes=notes,
                       safety_notes=["Solaris reads only; it does not start "
                                     "this feeder"],
                       example_command=f"python feeders_sdk/{fid}.py "
                                       f"--out {out}")
            for fid, modality, out, notes in _STANDALONE_FEEDERS]
        registry = FeederBlueprintRegistry()
        return FeederPackManifest(
            feeders=feeders,
            supported_modalities=sorted({f.modality for f in feeders}),
            schema_coverage=schema_coverage(),
            event_types=all_event_types(),
            blueprint_count=len(registry.blueprints),
            safety_notes=[
                "Solaris does not start, stop, configure, or command feeders.",
                "Feeders write local files; Solaris reads them read-only.",
                "Hardware-specific feeders are external/manual (blueprints)."],
            privacy_notes=[
                "Feeders emit feature summaries, never raw private content.",
                "Human text is observation, never a command, never ground "
                "truth."],
            what_solaris_can_read=("validated event-envelope JSONL files at the "
                                   "feeder output paths; nothing else"))

    def write(self) -> Dict[str, Any]:
        manifest = self.build()
        os.makedirs(self.state_dir, exist_ok=True)
        json_path = os.path.join(self.state_dir, "FEEDER_PACK_MANIFEST.json")
        readme_path = os.path.join(self.state_dir, "FEEDER_PACK_README.md")
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(manifest.to_dict(), fh, indent=2, default=str)
        with open(readme_path, "w", encoding="utf-8") as fh:
            fh.write(self._render_readme(manifest))
        return {"json": json_path, "readme": readme_path, "manifest": manifest}

    def _render_readme(self, manifest: FeederPackManifest) -> str:
        lines = [
            "# Feeder Pack", "",
            "These feeders are **outside Solaris**. They write local event "
            "envelopes; Solaris reads them read-only. Solaris does not start, "
            "stop, configure, or command any feeder or any hardware.", "",
            f"- schema version: {manifest.schema_version}",
            f"- schema coverage: {manifest.schema_coverage}",
            f"- supported modalities: {manifest.supported_modalities}",
            f"- blueprints: {manifest.blueprint_count}",
            "", "## Feeders", "",
        ]
        for f in manifest.feeders:
            lines.append(f"- `{f.feeder_id}` ({f.modality}): "
                         f"`{f.example_command}`")
        lines += ["", "## Safety", ""]
        lines += [f"- {n}" for n in manifest.safety_notes]
        lines += ["", "## Privacy", ""]
        lines += [f"- {n}" for n in manifest.privacy_notes]
        lines += ["", "## What Solaris can read", "",
                  f"- {manifest.what_solaris_can_read}"]
        return "\n".join(lines)
