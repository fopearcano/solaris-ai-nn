"""Stream adapters -- read-only readers that turn feeder output into envelopes.

Each adapter reads one kind of local stream (JSONL, CSV, watched folder, appended
text log, fixture-replay folder) and produces :class:`SensoryEventEnvelope`
objects. Adapters are strictly read-only: they never write, delete, modify, run a
shell, touch the network, or access hardware, and they tail/sample large files
within bounds. Every event carries provenance.
"""

from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .event_envelope import AnnotationStatus, SensoryEventEnvelope, TrustLevel
from .external_feeders import ExternalFeederDescriptor
from .modality import family_for_hint

_MAX_LINES = 500


def _trust_for(feeder: ExternalFeederDescriptor) -> str:
    if feeder.trust_level == "fixture":
        return TrustLevel.FIXTURE
    if feeder.trust_level in ("manual", "low"):
        return TrustLevel.LOW
    if feeder.trust_level == "medium":
        return TrustLevel.MEDIUM
    if feeder.trust_level == "high":
        return TrustLevel.HIGH
    return TrustLevel.UNTRUSTED


def _modality(feeder: ExternalFeederDescriptor,
              record: Optional[Dict[str, Any]] = None) -> str:
    if record and isinstance(record, dict) and record.get("modality"):
        fam = family_for_hint(str(record["modality"]))
        if fam != "unknown_field":
            return fam
        return str(record["modality"])
    return family_for_hint(feeder.modality_hint)


def _envelope(feeder: ExternalFeederDescriptor, modality: str,
              features: Dict[str, Any], *, raw_ref: str,
              annotation: Any = None,
              annotation_status: str = AnnotationStatus.NONE,
              timestamp: Optional[float] = None,
              line_no: int = 0) -> SensoryEventEnvelope:
    provenance = {"source_id": feeder.feeder_id,
                  "source_kind": feeder.source_type,
                  "feeder_trust": feeder.trust_level,
                  "raw_ref": raw_ref, "line_no": line_no,
                  "is_real_world": feeder.is_real_world}
    kwargs: Dict[str, Any] = dict(
        source_id=feeder.feeder_id, source_kind=feeder.source_type,
        modality=modality, features=features, raw_ref=raw_ref,
        annotation=annotation, annotation_status=annotation_status,
        provenance=provenance, trust_level=_trust_for(feeder))
    if timestamp is not None:
        kwargs["timestamp"] = float(timestamp)
    return SensoryEventEnvelope(**kwargs)


@dataclass
class StreamReadResult:
    events: List[SensoryEventEnvelope] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"event_count": len(self.events),
                "errors": list(self.errors)}


def _annotation_status(record: Dict[str, Any]) -> str:
    status = record.get("annotation_status")
    if status in AnnotationStatus.ALL:
        return status
    if record.get("annotation") is not None or record.get("label") is not None:
        # A label supplied in the stream is external, non-ground-truth.
        return AnnotationStatus.EXTERNAL_NON_GROUND_TRUTH
    return AnnotationStatus.NONE


def _features_from(record: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(record.get("features"), dict):
        return dict(record["features"])
    # Everything that is not metadata becomes a feature.
    skip = {"modality", "annotation", "label", "annotation_status",
            "timestamp", "ts"}
    return {k: v for k, v in record.items() if k not in skip}


def read_jsonl_stream(feeder: ExternalFeederDescriptor, *,
                      max_lines: int = _MAX_LINES) -> StreamReadResult:
    """Read a JSONL event stream (one JSON object per line)."""
    result = StreamReadResult()
    path = feeder.path
    if not os.path.isfile(path):
        result.errors.append(f"missing jsonl stream: {path}")
        return result
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    for i, line in enumerate(lines[-max_lines:]):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            result.errors.append(f"bad json at line {i}")
            continue
        if not isinstance(record, dict):
            continue
        ann = record.get("annotation", record.get("label"))
        result.events.append(_envelope(
            feeder, _modality(feeder, record), _features_from(record),
            raw_ref=f"{path}:{i}", annotation=ann,
            annotation_status=_annotation_status(record),
            timestamp=record.get("timestamp", record.get("ts")), line_no=i))
    return result


def read_csv_stream(feeder: ExternalFeederDescriptor, *,
                    max_lines: int = _MAX_LINES) -> StreamReadResult:
    """Read a CSV numeric stream (header row of feature names)."""
    result = StreamReadResult()
    path = feeder.path
    if not os.path.isfile(path):
        result.errors.append(f"missing csv stream: {path}")
        return result
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for i, row in enumerate(rows[-max_lines:]):
        features: Dict[str, Any] = {}
        for key, value in row.items():
            if key in ("modality", "annotation", "label", "timestamp", "ts"):
                continue
            try:
                features[key] = float(value)
            except (TypeError, ValueError):
                features[key] = value
        result.events.append(_envelope(
            feeder, _modality(feeder, row), features, raw_ref=f"{path}:{i}",
            annotation=row.get("annotation", row.get("label")),
            annotation_status=_annotation_status(row),
            timestamp=row.get("timestamp", row.get("ts")), line_no=i))
    return result


def read_text_log(feeder: ExternalFeederDescriptor, *,
                  max_lines: int = _MAX_LINES) -> StreamReadResult:
    """Read an appended text log; each line becomes a textual feature event."""
    result = StreamReadResult()
    path = feeder.path
    if not os.path.isfile(path):
        result.errors.append(f"missing text log: {path}")
        return result
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    for i, line in enumerate(lines[-max_lines:]):
        line = line.rstrip("\n")
        if not line:
            continue
        features = {"length": float(len(line)),
                    "token_count": float(len(line.split())),
                    "char_entropy_proxy": float(len(set(line)))}
        # The text itself is observation only; never an operator command.
        result.events.append(_envelope(
            feeder, _modality(feeder) or "human_textual", features,
            raw_ref=f"{path}:{i}", annotation=line,
            annotation_status=AnnotationStatus.EXTERNAL_NON_GROUND_TRUTH,
            line_no=i))
    return result


def read_watched_folder(feeder: ExternalFeederDescriptor, *,
                        max_files: int = _MAX_LINES) -> StreamReadResult:
    """Read a watched folder; each file's presence/size becomes an event."""
    result = StreamReadResult()
    root = feeder.path
    if not os.path.isdir(root):
        result.errors.append(f"missing folder: {root}")
        return result
    names = sorted(os.listdir(root))[:max_files]
    for i, name in enumerate(names):
        full = os.path.join(root, name)
        if not os.path.isfile(full):
            continue
        try:
            size = float(os.path.getsize(full))
            mtime = os.path.getmtime(full)
        except OSError:
            result.errors.append(f"unreadable file: {name}")
            continue
        result.events.append(_envelope(
            feeder, _modality(feeder) or "machine_rhythm",
            {"file_size": size, "name_length": float(len(name))},
            raw_ref=full, timestamp=mtime, line_no=i))
    return result


def read_fixture_replay(feeder: ExternalFeederDescriptor, *,
                        max_files: int = _MAX_LINES) -> StreamReadResult:
    """Replay a fixture folder of *.jsonl files in name order."""
    result = StreamReadResult()
    root = feeder.path
    if os.path.isfile(root):
        return read_jsonl_stream(feeder, max_lines=max_files)
    if not os.path.isdir(root):
        result.errors.append(f"missing fixture folder: {root}")
        return result
    for name in sorted(os.listdir(root)):
        if not name.endswith(".jsonl"):
            continue
        sub = ExternalFeederDescriptor(
            feeder_id=feeder.feeder_id, source_type=feeder.source_type,
            path=os.path.join(root, name), modality_hint=feeder.modality_hint,
            trust_level=feeder.trust_level)
        part = read_jsonl_stream(sub, max_lines=max_files)
        result.events.extend(part.events)
        result.errors.extend(part.errors)
    return result


# Dispatch table by feeder source type / adapter kind.
def read_feeder(feeder: ExternalFeederDescriptor, *,
                max_lines: int = _MAX_LINES) -> StreamReadResult:
    """Pick the right read-only adapter for a feeder, by path/source type."""
    path = feeder.path
    if feeder.source_type == "fixture_replay" or os.path.isdir(path):
        if os.path.isdir(path):
            # A folder-drop feeder lists files; a replay folder reads jsonl.
            if feeder.source_type == "folder_drop":
                return read_watched_folder(feeder, max_files=max_lines)
            return read_fixture_replay(feeder, max_files=max_lines)
    if path.endswith(".jsonl"):
        return read_jsonl_stream(feeder, max_lines=max_lines)
    if path.endswith(".csv"):
        return read_csv_stream(feeder, max_lines=max_lines)
    if path.endswith((".txt", ".log")):
        return read_text_log(feeder, max_lines=max_lines)
    # Default: try JSONL.
    return read_jsonl_stream(feeder, max_lines=max_lines)
