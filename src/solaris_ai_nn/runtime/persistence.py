"""Persistent runtime state for long-running, restartable experiments.

This module is the storage layer for Solaris-AI-NN's continuity machinery. It is
deliberately a flat directory of plain JSON / JSONL files -- no database, no
binary blobs -- so a running "brain" is fully inspectable with ``cat`` and a
text editor. State directory layout (under ``state_dir``):

    manifest.json          -- cross-restart identity + lifecycle flags
    latest_checkpoint.json -- the full substrate snapshot (reservoir/readout/...)
    telemetry.json         -- latest telemetry counters
    continuity_log.jsonl   -- append-only birth/heartbeat/death/... event log
    trace_events.jsonl     -- append-only, replayable input-signal trace

Note on format: the substrate (reservoir state, readout weights, habit weights)
is stored as JSON arrays rather than NumPy ``.npz``. The substrate is list-based
and pure-stdlib by design (see README / RESEARCH_NOTES), so JSON round-trips it
exactly and stays human-inspectable. ``.npz`` is reserved for a future
NumPy-backed reservoir backend (ROADMAP Phase 4) where binary arrays earn their
keep; it would add a dependency and reduce inspectability with no benefit today.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Union

if TYPE_CHECKING:  # Only for type hints; avoids an import cycle with bridges.
    from ..bridges.neural_bridge import SolarisNeuralBridge


# --------------------------------------------------------------------------- #
# JSON-lines writer / reader                                                  #
# --------------------------------------------------------------------------- #


@dataclass
class JsonlWriter:
    """Append-only JSON-lines writer.

    Args:
        path: Destination file.
        append: If True, open in append mode (preserve prior rows across
            restarts). If False (default), truncate -- the legacy behaviour used
            for single-session in-memory mirrors.
    """

    path: Union[str, Path]
    append: bool = False
    _fh: Any = field(default=None, repr=False, init=False)

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(self.path, "a" if self.append else "w", encoding="utf-8")

    def write(self, record: Dict[str, Any]) -> None:
        """Append one record as a JSON line and flush."""
        if self._fh is None:
            raise RuntimeError("writer is closed")
        self._fh.write(json.dumps(record, default=str) + "\n")
        self._fh.flush()

    def close(self) -> None:
        """Close the underlying file handle (idempotent)."""
        if self._fh is not None:
            self._fh.close()
            self._fh = None

    def __enter__(self) -> "JsonlWriter":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


def read_jsonl(path: Union[str, Path]) -> Iterator[Dict[str, Any]]:
    """Yield records from a JSONL file written by :class:`JsonlWriter`."""
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


# --------------------------------------------------------------------------- #
# Continuity log                                                              #
# --------------------------------------------------------------------------- #

# Canonical continuity event types. Kept as constants so callers don't pass
# free-form strings that silently diverge.
BIRTH = "birth"
HEARTBEAT = "heartbeat"
CHECKPOINT = "checkpoint"
GRACEFUL_DEATH = "graceful_death"
UNEXPECTED_DEATH = "unexpected_death_detected"
RESTART = "restart"
BRAIN_DEATH_GAP = "brain_death_gap"
SOAK_START = "soak_start"
SOAK_STOP = "soak_stop"
REACTION_FEEDBACK = "reaction_feedback"
SYNTHESIS_PRUNING = "synthesis_pruning"
HABIT_REINFORCEMENT = "habit_reinforcement"

EVENT_TYPES = frozenset(
    {
        BIRTH,
        HEARTBEAT,
        CHECKPOINT,
        GRACEFUL_DEATH,
        UNEXPECTED_DEATH,
        RESTART,
        BRAIN_DEATH_GAP,
        SOAK_START,
        SOAK_STOP,
        REACTION_FEEDBACK,
        SYNTHESIS_PRUNING,
        HABIT_REINFORCEMENT,
    }
)


@dataclass
class ContinuityLog:
    """Append-only JSONL log of lifecycle / continuity events.

    The log persists across restarts (append mode). Each row records the
    timestamp, run/session ids, event type, message, step counters, a graceful
    flag, and arbitrary metadata. ``run_id`` / ``session_id`` are mutable so the
    owning runner can stamp the current session onto every row.
    """

    path: Union[str, Path]
    run_id: str = ""
    session_id: str = ""
    _writer: JsonlWriter = field(default=None, repr=False, init=False)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self._writer = JsonlWriter(self.path, append=True)

    def log(
        self,
        event_type: str,
        message: str = "",
        step: int = 0,
        lifetime_step: int = 0,
        graceful: bool = True,
        **metadata: Any,
    ) -> Dict[str, Any]:
        """Append one continuity row; returns the written record."""
        if event_type not in EVENT_TYPES:
            raise ValueError(f"unknown continuity event type: {event_type!r}")
        record = {
            "timestamp": time.time(),
            "run_id": self.run_id,
            "session_id": self.session_id,
            "event_type": event_type,
            "message": message,
            "step": step,
            "lifetime_step": lifetime_step,
            "graceful": graceful,
            "metadata": metadata,
        }
        self._writer.write(record)
        return record

    def read_all(self) -> List[Dict[str, Any]]:
        """Return every row in the log (empty if the file does not exist)."""
        if not Path(self.path).exists():
            return []
        return list(read_jsonl(self.path))

    def tail(self, n: int) -> List[Dict[str, Any]]:
        """Return the last ``n`` rows."""
        return self.read_all()[-n:]

    def count(self) -> int:
        """Number of rows currently in the log."""
        return len(self.read_all())

    def close(self) -> None:
        self._writer.close()


# --------------------------------------------------------------------------- #
# State checkpoint                                                            #
# --------------------------------------------------------------------------- #


@dataclass
class StateCheckpoint:
    """A full, serialisable snapshot of the neural substrate's state.

    Captures everything needed to resume a bridge after restart: reservoir
    state, readout weights, habit weights/counts, pruning history, telemetry
    counters, and step/identity metadata. Reservoir *weights* (``W``/``W_in``)
    are NOT stored -- they are regenerated deterministically from the seed in
    ``reservoir_config``, so only the evolving state vector needs saving.
    """

    run_id: str
    session_id: str
    session_step: int
    lifetime_step: int
    timestamp: float
    last_heartbeat_ts: float
    reservoir_state: List[float]
    reservoir_config: Dict[str, Any]
    readout_weights: List[List[float]]
    readout_labels: List[str]
    habit_weights: List[List[Any]]  # [[pattern_key, action_label, weight], ...]
    habit_counts: List[List[Any]]  # [[pattern_key, action_label, count], ...]
    pruning_history: List[Dict[str, Any]] = field(default_factory=list)
    telemetry: Dict[str, Any] = field(default_factory=dict)
    # Controlled-plasticity state (Prompt 5): current mutable parameter values so
    # plasticity effects survive a restart, plus the engine's summary.
    mutable_params: List[List[Any]] = field(default_factory=list)
    plasticity: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateCheckpoint":
        valid = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})

    @classmethod
    def capture(
        cls,
        bridge: "SolarisNeuralBridge",
        *,
        run_id: str,
        session_id: str,
        session_step: int,
        lifetime_step: int,
        last_heartbeat_ts: float,
        pruning_history: Optional[List[Dict[str, Any]]] = None,
        mutable_params: Optional[List[List[Any]]] = None,
        plasticity: Optional[Dict[str, Any]] = None,
    ) -> "StateCheckpoint":
        """Build a checkpoint by reading the live state out of ``bridge``."""
        esn = bridge.esn
        config = {
            "n_inputs": esn.n_inputs,
            "n_reservoir": esn.n_reservoir,
            "spectral_radius": esn.spectral_radius,
            "leak_rate": esn.leak_rate,
            "input_scaling": esn.input_scaling,
            "sparsity": esn.sparsity,
            "seed": esn.seed,
        }
        habit_weights = [[k[0], k[1], v] for k, v in bridge.habit.weights.items()]
        habit_counts = [[k[0], k[1], v] for k, v in bridge.habit.counts.items()]
        return cls(
            run_id=run_id,
            session_id=session_id,
            session_step=session_step,
            lifetime_step=lifetime_step,
            timestamp=time.time(),
            last_heartbeat_ts=last_heartbeat_ts,
            reservoir_state=list(esn.state),
            reservoir_config=config,
            readout_weights=[list(row) for row in bridge.readout.weights],
            readout_labels=list(bridge.readout.labels),
            habit_weights=habit_weights,
            habit_counts=habit_counts,
            pruning_history=list(pruning_history or []),
            telemetry=dict(bridge.telemetry.to_dict()),
            mutable_params=list(mutable_params or []),
            plasticity=dict(plasticity or {}),
        )

    def restore_into(self, bridge: "SolarisNeuralBridge") -> None:
        """Apply this checkpoint's state onto a freshly-constructed ``bridge``.

        The bridge must be built with the same seed/shape (the runner guarantees
        this), so the regenerated reservoir matrices match; only the evolving
        state and learned weights are restored here.
        """
        esn = bridge.esn
        if len(self.reservoir_state) != esn.n_reservoir:
            raise ValueError(
                "checkpoint reservoir size "
                f"{len(self.reservoir_state)} != bridge {esn.n_reservoir}"
            )
        esn.reset(self.reservoir_state)
        if len(self.readout_weights) == len(bridge.readout.weights):
            bridge.readout.weights = [list(row) for row in self.readout_weights]
            if self.readout_labels:
                bridge.readout.labels = list(self.readout_labels)
        bridge.habit.weights = {(k[0], k[1]): k[2] for k in self.habit_weights}
        bridge.habit.counts = {(k[0], k[1]): int(k[2]) for k in self.habit_counts}


# --------------------------------------------------------------------------- #
# Persistence manager                                                         #
# --------------------------------------------------------------------------- #


@dataclass
class PersistenceManager:
    """Owns a state directory and reads/writes its manifest, checkpoint, logs.

    All file IO for continuity lives here. Higher-level startup logic (deciding
    whether a death was graceful, computing the brain-death gap) lives in the
    :class:`~solaris_ai_nn.runtime.continuous_runner.ContinuousRunner`, which
    uses this manager plus the continuity log.
    """

    state_dir: Union[str, Path] = ".solaris_ai_nn_state"

    def __post_init__(self) -> None:
        self.state_dir = Path(self.state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    # -- paths --------------------------------------------------------------

    @property
    def manifest_path(self) -> Path:
        return self.state_dir / "manifest.json"

    @property
    def checkpoint_path(self) -> Path:
        return self.state_dir / "latest_checkpoint.json"

    @property
    def telemetry_path(self) -> Path:
        return self.state_dir / "telemetry.json"

    @property
    def continuity_log_path(self) -> Path:
        return self.state_dir / "continuity_log.jsonl"

    @property
    def trace_path(self) -> Path:
        return self.state_dir / "trace_events.jsonl"

    @property
    def inner_map_path(self) -> Path:
        return self.state_dir / "inner_map.json"

    @property
    def plasticity_audit_path(self) -> Path:
        return self.state_dir / "plasticity_audit.jsonl"

    # -- manifest -----------------------------------------------------------

    def has_previous_state(self) -> bool:
        """True if a manifest from a prior session exists."""
        return self.manifest_path.exists()

    def load_manifest(self) -> Optional[Dict[str, Any]]:
        if not self.manifest_path.exists():
            return None
        with open(self.manifest_path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def save_manifest(self, manifest: Dict[str, Any]) -> None:
        manifest = dict(manifest)
        manifest["updated_at"] = time.time()
        self._write_json(self.manifest_path, manifest)

    @staticmethod
    def new_run_id() -> str:
        """Generate a stable identity id for a fresh brain."""
        return uuid.uuid4().hex[:12]

    @staticmethod
    def new_session_id() -> str:
        """Generate a per-process session id."""
        return uuid.uuid4().hex[:12]

    # -- checkpoint / telemetry --------------------------------------------

    def save_checkpoint(self, checkpoint: StateCheckpoint) -> None:
        self._write_json(self.checkpoint_path, checkpoint.to_dict())
        self.save_telemetry(checkpoint.telemetry)

    def load_checkpoint(self) -> Optional[StateCheckpoint]:
        if not self.checkpoint_path.exists():
            return None
        with open(self.checkpoint_path, "r", encoding="utf-8") as fh:
            return StateCheckpoint.from_dict(json.load(fh))

    def save_telemetry(self, telemetry: Dict[str, Any]) -> None:
        self._write_json(self.telemetry_path, telemetry)

    def load_telemetry(self) -> Optional[Dict[str, Any]]:
        if not self.telemetry_path.exists():
            return None
        with open(self.telemetry_path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    # -- inner map ----------------------------------------------------------

    def save_inner_map(self, inner_map: Dict[str, Any]) -> None:
        """Persist the Inner MAP self-model as ``inner_map.json``."""
        self._write_json(self.inner_map_path, inner_map)

    def load_inner_map(self) -> Optional[Dict[str, Any]]:
        if not self.inner_map_path.exists():
            return None
        with open(self.inner_map_path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    # -- continuity log -----------------------------------------------------

    def continuity_log(self, run_id: str = "", session_id: str = "") -> ContinuityLog:
        """Open (append) the continuity log for this state directory."""
        return ContinuityLog(self.continuity_log_path, run_id=run_id, session_id=session_id)

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _write_json(path: Path, data: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, default=str)
        tmp.replace(path)  # atomic-ish swap so a crash mid-write can't corrupt
