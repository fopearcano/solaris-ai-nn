"""Validators -- reject or quarantine envelopes that break the contract.

:class:`EnvelopeValidator`, :class:`SchemaValidator`, and
:class:`FeederOutputValidator` check the required fields, provenance, privacy and
safety flags, annotation status, read-only guarantees, and the absence of
command-as-input, ground-truth human labels, executable payloads, and decoded
private content. Each :class:`ValidationIssue` explains *why* an event failed;
validation never deletes source data.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .contract import FeederSDKAnnotationStatus, FeederSDKModality
from .schemas import get_schema, schema_for_modality

_EXEC_KEYS = ("__exec__", "command", "shell", "eval", "system", "subprocess")
_DECODE_KEYS = ("decoded_message", "plaintext", "transcript", "raw_audio",
                "raw_video", "private_content")


@dataclass
class ValidationIssue:
    field: str
    reason: str
    severity: str = "error"  # "error" | "warning"

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ValidationResult:
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    def to_dict(self) -> Dict[str, Any]:
        return {"valid": self.valid,
                "issues": [i.to_dict() for i in self.issues]}


@dataclass
class EnvelopeValidator:
    """Validates one envelope dict against the contract's hard rules."""

    def validate(self, record: Dict[str, Any]) -> ValidationResult:
        issues: List[ValidationIssue] = []
        if not isinstance(record, dict):
            return ValidationResult(False, [ValidationIssue(
                "envelope", "record is not an object")])

        for required in ("feeder_id", "source_id", "modality", "timestamp",
                         "provenance"):
            if record.get(required) in (None, ""):
                issues.append(ValidationIssue(required,
                                              f"missing required field "
                                              f"{required!r}"))
        # Timestamp must be numeric.
        ts = record.get("timestamp")
        if ts is not None:
            try:
                float(ts)
            except (TypeError, ValueError):
                issues.append(ValidationIssue("timestamp",
                                              "timestamp is not numeric"))
        # Provenance must carry source_id + feeder_id.
        prov = record.get("provenance") or {}
        if not (isinstance(prov, dict) and prov.get("source_id")
                and prov.get("feeder_id")):
            issues.append(ValidationIssue("provenance",
                                          "provenance must include source_id "
                                          "and feeder_id"))
        # Read-only guarantees.
        if record.get("read_only") is False:
            issues.append(ValidationIssue("read_only",
                                          "read_only must be true"))
        if record.get("source_mutable_by_solaris") is True:
            issues.append(ValidationIssue("source_mutable_by_solaris",
                                          "source_mutable_by_solaris must be "
                                          "false"))
        # Modality must be known.
        if record.get("modality") not in FeederSDKModality.ALL:
            issues.append(ValidationIssue("modality",
                                          f"unknown modality "
                                          f"{record.get('modality')!r}",
                                          severity="warning"))
        # Features are primary: features dict or numeric content required.
        features = record.get("features")
        if not isinstance(features, dict) or not features:
            if record.get("annotation") is None:
                issues.append(ValidationIssue("features",
                                              "features are primary; none found"))
        # No human label as ground truth.
        if record.get("annotation_status") == "ground_truth":
            issues.append(ValidationIssue("annotation_status",
                                          "human labels are never ground truth"))
        # No executable payload / command-as-input.
        if any(k in record for k in _EXEC_KEYS):
            issues.append(ValidationIssue("features",
                                          "executable/command payload rejected"))
        if isinstance(features, dict) and any(k in features
                                              for k in _EXEC_KEYS):
            issues.append(ValidationIssue("features",
                                          "executable payload in features "
                                          "rejected"))
        # No decoded private communication content. We inspect actual keys
        # (top-level and feature keys), not the serialized blob, so a benign
        # flag like "no_raw_private_content" never triggers a false positive.
        candidate_keys = set(record) | set(
            features if isinstance(features, dict) else {})
        for key in _DECODE_KEYS:
            if key in candidate_keys:
                issues.append(ValidationIssue("privacy",
                                              f"decoded/private content key "
                                              f"{key!r} rejected"))
                break
        return ValidationResult(valid=not any(i.severity == "error"
                                              for i in issues), issues=issues)


@dataclass
class SchemaValidator:
    """Validates an envelope's features against its modality schema."""

    def validate(self, record: Dict[str, Any]) -> ValidationResult:
        modality = record.get("modality")
        event_type = (record.get("metadata") or {}).get("event_type")
        schema = (get_schema(event_type) if event_type
                  else schema_for_modality(modality))
        if schema is None:
            return ValidationResult(True, [ValidationIssue(
                "schema", f"no schema for modality {modality!r}; "
                "feature check skipped", severity="warning")])
        feature_issues = schema.validate_features(record.get("features") or {})
        issues = [ValidationIssue("features", reason, severity="warning")
                  for reason in feature_issues]
        return ValidationResult(valid=True, issues=issues)


@dataclass
class FeederOutputValidator:
    """Validates a feeder output JSONL file (read-only; never deletes source)."""

    def validate_file(self, path: str, *,
                      max_lines: int = 5000) -> Dict[str, Any]:
        envelope_validator = EnvelopeValidator()
        valid = invalid = 0
        issues: List[Dict[str, Any]] = []
        if not os.path.isfile(path):
            return {"valid": False, "path": path, "valid_count": 0,
                    "invalid_count": 0, "reason": "output path missing"}
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh):
                if i >= max_lines:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    invalid += 1
                    issues.append({"line": i, "reason": "invalid json"})
                    continue
                result = envelope_validator.validate(record)
                if result.valid:
                    valid += 1
                else:
                    invalid += 1
                    issues.append({"line": i,
                                   "reasons": [x.reason for x in result.errors]})
        return {"valid": invalid == 0, "path": path, "valid_count": valid,
                "invalid_count": invalid, "issues": issues[:50]}
