"""Live feature extraction -- feature evidence from validated read-only events.

:class:`LiveFeatureExtractor` turns each accepted live event into a
:class:`LiveFeatureVector`: source/modality/channel, a coarse timestamp bucket,
bucketed scalar payload values, categorical payload keys, a payload shape signature,
absence/noise/confidence/reliability markers, and (when available) rhythm and
overload/deprivation context. Debug gloss is stored only as a non-ground-truth
annotation; human text is represented as source/type/length/rhythm rather than
semantic truth; the operator pulse must not dominate the feature space; and raw
private or secret-bearing events are never extracted.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..live_observation.observation_window import parse_timestamp

_OPERATOR_PULSE = "operator_pulse"
_HUMAN_TEXT_SOURCES = ("operator_pulse", "local_environment_manual")


def _scalar_bucket(value: float) -> str:
    """Bucket a scalar into a coarse range label (descriptive, not exact)."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "nan"
    for hi in (0.0, 0.1, 0.25, 0.5, 1.0, 5.0, 10.0, 100.0, 1000.0):
        if v <= hi:
            return f"<= {hi}"
    return "> 1000"


@dataclass
class LiveFeatureVector:
    """One feature vector extracted from one accepted live event."""

    event_id: str
    source_id: str
    modality: str
    channel: str
    timestamp_bucket: str = ""
    scalar_values: Dict[str, str] = field(default_factory=dict)
    categorical_keys: List[str] = field(default_factory=list)
    payload_shape: str = ""
    feature_signature: str = ""
    is_absence: bool = False
    is_noisy: bool = False
    noise: float = 0.0
    completeness: float = 1.0
    is_human_text_source: bool = False
    is_operator_pulse: bool = False
    rhythm_marker: str = ""
    load_context: str = ""
    debug_gloss_annotation: str = ""  # NON-ground-truth annotation only
    # Whether the *source event* attempted to assert ground truth (recorded so
    # the contamination filter can reject it; it is never honoured as truth).
    attempted_human_label_ground_truth: bool = False
    attempted_debug_gloss_ground_truth: bool = False
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id, "source_id": self.source_id,
            "modality": self.modality, "channel": self.channel,
            "timestamp_bucket": self.timestamp_bucket,
            "scalar_values": dict(self.scalar_values),
            "categorical_keys": list(self.categorical_keys),
            "payload_shape": self.payload_shape,
            "feature_signature": self.feature_signature,
            "is_absence": self.is_absence, "is_noisy": self.is_noisy,
            "noise": round(self.noise, 3), "completeness": self.completeness,
            "is_human_text_source": self.is_human_text_source,
            "is_operator_pulse": self.is_operator_pulse,
            "rhythm_marker": self.rhythm_marker,
            "load_context": self.load_context,
            "debug_gloss_annotation": self.debug_gloss_annotation,
            # Ground truth is never honoured; we only record whether the event
            # *attempted* to assert it, so contamination can reject it.
            "debug_gloss_is_ground_truth": False,
            "human_label_is_ground_truth": False,
            "attempted_human_label_ground_truth":
                self.attempted_human_label_ground_truth,
            "attempted_debug_gloss_ground_truth":
                self.attempted_debug_gloss_ground_truth,
            "limitations": list(self.limitations),
        }


@dataclass
class FeatureExtractionResult:
    """The aggregate feature-extraction result."""

    vectors: List[LiveFeatureVector] = field(default_factory=list)
    skipped_count: int = 0
    skipped_reasons: Dict[str, int] = field(default_factory=dict)

    @property
    def feature_vector_count(self) -> int:
        return len(self.vectors)

    def to_dict(self) -> Dict[str, Any]:
        sources: Dict[str, int] = {}
        modalities: Dict[str, int] = {}
        for v in self.vectors:
            sources[v.source_id] = sources.get(v.source_id, 0) + 1
            modalities[v.modality] = modalities.get(v.modality, 0) + 1
        return {
            "live_feature_vector_count": self.feature_vector_count,
            "by_source": sources, "by_modality": modalities,
            "skipped_count": self.skipped_count,
            "skipped_reasons": dict(self.skipped_reasons),
            "vectors": [v.to_dict() for v in self.vectors],
            "note": "debug gloss is stored only as a non-ground-truth "
                    "annotation; human text is represented structurally, not "
                    "semantically; the operator pulse must not dominate; raw "
                    "private/secret events are never extracted",
        }


@dataclass
class LiveFeatureExtractor:
    """Extracts feature vectors from accepted live events (read-only)."""

    def extract(self, *, accepted_events: List[Dict[str, Any]],
                rhythm: Optional[Dict[str, Any]] = None,
                load_status: str = "") -> FeatureExtractionResult:
        result = FeatureExtractionResult()
        rhythm_by_source = self._rhythm_by_source(rhythm or {})
        for ev in accepted_events:
            safety = ev.get("safety", {}) or {}
            if safety.get("contains_secret") or safety.get("private_data"):
                result.skipped_count += 1
                result.skipped_reasons["private_or_secret"] = \
                    result.skipped_reasons.get("private_or_secret", 0) + 1
                continue
            result.vectors.append(self._vector(ev, rhythm_by_source,
                                               load_status))
        return result

    def _vector(self, ev: Dict[str, Any], rhythm_by_source: Dict[str, str],
                load_status: str) -> LiveFeatureVector:
        sid = str(ev.get("source_id", ""))
        modality = str(ev.get("modality", ""))
        channel = str(ev.get("channel", ""))
        quality = ev.get("quality", {}) or {}
        payload = ev.get("payload")

        scalar_values: Dict[str, str] = {}
        categorical_keys: List[str] = []
        if isinstance(payload, dict):
            for key, value in sorted(payload.items()):
                if isinstance(value, bool):
                    categorical_keys.append(f"{key}={value}")
                elif isinstance(value, (int, float)):
                    scalar_values[key] = _scalar_bucket(value)
                else:
                    categorical_keys.append(str(key))
        payload_shape = self._payload_shape(payload)

        t = parse_timestamp(ev.get("timestamp_utc", ""))
        ts_bucket = (f"hour:{int(t // 3600)}" if t is not None else "unknown")

        vec = LiveFeatureVector(
            event_id=str(ev.get("event_id", "")), source_id=sid,
            modality=modality, channel=channel, timestamp_bucket=ts_bucket,
            scalar_values=scalar_values, categorical_keys=categorical_keys,
            payload_shape=payload_shape,
            is_absence=bool(quality.get("is_absence")),
            is_noisy=bool(quality.get("is_noisy")),
            noise=float(quality.get("noise", 0.0) or 0.0),
            completeness=float(quality.get("completeness", 1.0) or 0.0),
            is_human_text_source=sid in _HUMAN_TEXT_SOURCES,
            is_operator_pulse=sid == _OPERATOR_PULSE,
            rhythm_marker=rhythm_by_source.get(sid, ""),
            load_context=load_status,
            attempted_human_label_ground_truth=bool(
                ev.get("human_label_is_ground_truth")),
            attempted_debug_gloss_ground_truth=bool(
                ev.get("debug_gloss_is_ground_truth")))
        # Debug gloss is annotation-only; never ground truth.
        gloss = str(ev.get("debug_gloss", "")).strip()
        if gloss:
            vec.debug_gloss_annotation = gloss[:160]
            vec.limitations.append("debug gloss kept as annotation, not truth")
        if vec.is_human_text_source:
            vec.limitations.append(
                "human-text source represented structurally, not semantically")
        vec.feature_signature = self._signature(vec)
        return vec

    @staticmethod
    def _payload_shape(payload: Any) -> str:
        if isinstance(payload, dict):
            return "dict:{" + ",".join(sorted(payload.keys())) + "}"
        if isinstance(payload, list):
            return f"list:{len(payload)}"
        return f"scalar:{type(payload).__name__}"

    @staticmethod
    def _signature(vec: LiveFeatureVector) -> str:
        # A feature signature is built from structural features only -- never
        # from human-text semantics or debug gloss.
        parts = [vec.source_id, vec.modality, vec.channel, vec.payload_shape]
        parts += [f"{k}={v}" for k, v in sorted(vec.scalar_values.items())]
        parts += sorted(vec.categorical_keys)
        if vec.is_absence:
            parts.append("absence")
        raw = "|".join(parts)
        digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
        return f"{vec.source_id}:{vec.modality}:{digest}"

    @staticmethod
    def _rhythm_by_source(rhythm: Dict[str, Any]) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for p in rhythm.get("patterns", []) or []:
            out[p.get("source_id", "")] = p.get("kind", "")
        return out
