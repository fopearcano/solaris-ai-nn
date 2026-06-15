"""Fixture feeders -- write external-feeder-style files Solaris then reads.

These helpers turn an :class:`OrganismicDemoScenario`'s generated events into
JSONL files that look like real external-feeder output, under a fixtures
directory. The cross-modal *debug-truth* file is written separately and is
**never** placed in the sensory roots: it is for the evaluator only, and Solaris
must not read it during the main run.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..plural_sensorium import ExternalFeederDescriptor, FeederSourceType
from .scenario import (
    DEBUG_TRUTH_FILE,
    FEEDER_FILES,
    OrganismicDemoScenario,
)

# Map a feeder file to a representative source type (still read-only fixtures).
_SOURCE_TYPE = {
    "human_text_log.jsonl": FeederSourceType.MANUAL_LOG,
    "light_temperature_stream.jsonl": FeederSourceType.SENSOR_LOGGER,
    "rf_feature_stream.jsonl": FeederSourceType.SDR_FEATURE_EXPORTER,
    "echo_feature_stream.jsonl": FeederSourceType.RADAR_METADATA_EXPORTER,
    "vibration_stream.jsonl": FeederSourceType.VIBRATION_LOGGER,
    "magnetic_stream.jsonl": FeederSourceType.MAGNETIC_LOGGER,
    "absence_schedule.jsonl": FeederSourceType.MANUAL_LOG,
}


@dataclass
class FixtureFeederSet:
    """The result of writing the fixtures: feeders, dir, and the debug path."""

    fixtures_dir: str
    feeders: List[ExternalFeederDescriptor] = field(default_factory=list)
    debug_truth_path: str = ""
    feeder_paths: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fixtures_dir": self.fixtures_dir,
            "feeders": [f.to_dict() for f in self.feeders],
            "debug_truth_path": self.debug_truth_path,
            "feeder_count": len(self.feeders),
        }


def write_fixtures(scenario: OrganismicDemoScenario,
                   state_dir: str) -> FixtureFeederSet:
    """Generate the scenario and write feeder files (fixtures, read-only style).

    Returns a :class:`FixtureFeederSet` whose ``feeders`` are *fixture-replay*
    descriptors (forced non-real-world so the demo runs without governance) and
    excludes the debug-truth file from the sensory roots.
    """
    streams, debug = scenario.generate()
    fixtures_dir = os.path.join(state_dir, "fixtures")
    os.makedirs(fixtures_dir, exist_ok=True)

    feeders: List[ExternalFeederDescriptor] = []
    feeder_paths: List[str] = []
    for file_name, records in streams.items():
        path = os.path.join(fixtures_dir, file_name)
        records = sorted(records, key=lambda r: r["ts"])
        with open(path, "w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec) + "\n")
        modality_hint = FEEDER_FILES[file_name][0]
        # Fixture-replay so the demo is governance-free and clearly non-real.
        feeder = ExternalFeederDescriptor(
            feeder_id=file_name.replace(".jsonl", ""),
            source_type=FeederSourceType.FIXTURE_REPLAY,
            path=path, modality_hint=modality_hint,
            metadata={"imitates": _SOURCE_TYPE.get(file_name, "manual_log"),
                      "fixture": True})
        feeders.append(feeder)
        feeder_paths.append(path)

    # The debug-truth file lives OUTSIDE the fixtures dir so it can never be
    # swept into the sensory roots.
    debug_path = os.path.join(state_dir, DEBUG_TRUTH_FILE)
    with open(debug_path, "w", encoding="utf-8") as fh:
        for rec in debug:
            fh.write(json.dumps(rec) + "\n")

    return FixtureFeederSet(fixtures_dir=fixtures_dir, feeders=feeders,
                            debug_truth_path=debug_path,
                            feeder_paths=feeder_paths)
