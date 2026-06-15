"""Soak checkpointing -- append-only, checksum-verified, break-preserving.

:class:`CheckpointManager` writes append-only checkpoints (run manifest + module
state summaries + Inner MAP snapshot + developmental-life state + per-module
states + safety state + artifact index + checksum manifest). Old checkpoints are
never auto-deleted; a corrupt checkpoint is *recorded* (not dropped); and
recovery preserves the discontinuity (break) history.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _checksum(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


@dataclass
class SoakCheckpoint:
    """One append-only soak checkpoint (a structural snapshot of the run)."""

    checkpoint_id: str
    tick: int
    run_manifest: Dict[str, Any] = field(default_factory=dict)
    module_state_summaries: Dict[str, Any] = field(default_factory=dict)
    inner_map_snapshot: Dict[str, Any] = field(default_factory=dict)
    developmental_life_state: Dict[str, Any] = field(default_factory=dict)
    sensorium_state: Dict[str, Any] = field(default_factory=dict)
    metabolism_state: Dict[str, Any] = field(default_factory=dict)
    ontogenesis_state: Dict[str, Any] = field(default_factory=dict)
    semiogenesis_state: Dict[str, Any] = field(default_factory=dict)
    cognition_state: Dict[str, Any] = field(default_factory=dict)
    self_boundary_state: Dict[str, Any] = field(default_factory=dict)
    desire_action_state: Dict[str, Any] = field(default_factory=dict)
    safety_state: Dict[str, Any] = field(default_factory=dict)
    artifact_index: List[str] = field(default_factory=list)
    checksum_manifest: Dict[str, str] = field(default_factory=dict)
    corrupt: bool = False
    ts: float = field(default_factory=time.time)

    def _content(self) -> Dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id, "tick": self.tick,
            "run_manifest": self.run_manifest,
            "module_state_summaries": self.module_state_summaries,
            "inner_map_snapshot": self.inner_map_snapshot,
            "developmental_life_state": self.developmental_life_state,
            "sensorium_state": self.sensorium_state,
            "metabolism_state": self.metabolism_state,
            "ontogenesis_state": self.ontogenesis_state,
            "semiogenesis_state": self.semiogenesis_state,
            "cognition_state": self.cognition_state,
            "self_boundary_state": self.self_boundary_state,
            "desire_action_state": self.desire_action_state,
            "safety_state": self.safety_state,
            "artifact_index": list(self.artifact_index),
        }

    def build_checksums(self) -> Dict[str, str]:
        content = self._content()
        self.checksum_manifest = {k: _checksum(v) for k, v in content.items()}
        self.checksum_manifest["__all__"] = _checksum(content)
        return self.checksum_manifest

    def to_dict(self) -> Dict[str, Any]:
        out = self._content()
        out.update({"checksum_manifest": dict(self.checksum_manifest),
                    "corrupt": self.corrupt, "ts": self.ts})
        return out


@dataclass
class CheckpointIntegrityResult:
    """The outcome of verifying a checkpoint against its checksum manifest."""

    checkpoint_id: str
    ok: bool
    mismatches: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"checkpoint_id": self.checkpoint_id, "ok": self.ok,
                "mismatches": list(self.mismatches)}


@dataclass
class CheckpointManager:
    """Append-only checkpoint store; no auto-delete; corruption is recorded."""

    state_dir: str = ".solaris_ai_nn_soak"
    persist: bool = True
    checkpoints: List[SoakCheckpoint] = field(default_factory=list, init=False)
    corruption_records: List[Dict[str, Any]] = field(default_factory=list,
                                                      init=False)
    break_history: List[Dict[str, Any]] = field(default_factory=list,
                                                 init=False)

    @property
    def _path(self) -> str:
        return os.path.join(self.state_dir, "soak_checkpoints.jsonl")

    @property
    def _corruption_path(self) -> str:
        return os.path.join(self.state_dir, "soak_checkpoint_corruption.jsonl")

    def create(self, *, tick: int, run_manifest: Optional[Dict] = None,
               module_states: Optional[Dict[str, Dict]] = None,
               inner_map: Optional[Dict] = None,
               developmental_life: Optional[Dict] = None,
               safety: Optional[Dict] = None,
               artifact_index: Optional[List[str]] = None) -> SoakCheckpoint:
        module_states = module_states or {}
        cp = SoakCheckpoint(
            checkpoint_id=f"cp_{len(self.checkpoints)}_{tick}", tick=tick,
            run_manifest=dict(run_manifest or {}),
            module_state_summaries={k: dict(v) for k, v in
                                    module_states.items()},
            inner_map_snapshot=dict(inner_map or {}),
            developmental_life_state=dict(developmental_life or {}),
            sensorium_state=dict(module_states.get("plural_sensorium", {})),
            metabolism_state=dict(module_states.get("perceptual_metabolism",
                                                    {})),
            ontogenesis_state=dict(module_states.get("perceptual_ontogenesis",
                                                     {})),
            semiogenesis_state=dict(module_states.get("semiogenesis", {})),
            cognition_state=dict(module_states.get("sensorium_cognition", {})),
            self_boundary_state=dict(module_states.get("self_boundary", {})),
            desire_action_state={
                "desire_formation":
                    dict(module_states.get("desire_formation", {})),
                "action_reaction":
                    dict(module_states.get("action_reaction", {}))},
            safety_state=dict(safety or {}),
            artifact_index=list(artifact_index or []))
        cp.build_checksums()
        self.checkpoints.append(cp)
        if self.persist:
            self._append(self._path, cp.to_dict())
        return cp

    def verify(self, checkpoint: SoakCheckpoint) -> CheckpointIntegrityResult:
        recomputed = {k: _checksum(v) for k, v in checkpoint._content().items()}
        recomputed["__all__"] = _checksum(checkpoint._content())
        mismatches = [k for k, v in checkpoint.checksum_manifest.items()
                      if recomputed.get(k) != v]
        ok = not mismatches
        if not ok:
            checkpoint.corrupt = True
            self.record_corruption(checkpoint.checkpoint_id, mismatches)
        return CheckpointIntegrityResult(checkpoint.checkpoint_id, ok,
                                         mismatches)

    def record_corruption(self, checkpoint_id: str,
                          mismatches: List[str]) -> None:
        record = {"checkpoint_id": checkpoint_id, "mismatches": list(mismatches),
                  "ts": time.time()}
        self.corruption_records.append(record)
        if self.persist:
            self._append(self._corruption_path, record)

    def mark_corrupt_payload(self, payload: Dict[str, Any]) -> SoakCheckpoint:
        """Record an externally-detected corrupt checkpoint (never dropped)."""
        cp = SoakCheckpoint(
            checkpoint_id=str(payload.get("checkpoint_id", "corrupt")),
            tick=int(payload.get("tick", 0)), corrupt=True)
        self.checkpoints.append(cp)
        self.record_corruption(cp.checkpoint_id, ["externally detected corrupt"])
        return cp

    def recover(self) -> Dict[str, Any]:
        """Recover from the latest *intact* checkpoint, preserving breaks.

        Recovery never erases the break/discontinuity history; a recovery that
        skips a corrupt checkpoint logs the skip as a continuity break.
        """
        latest_intact: Optional[SoakCheckpoint] = None
        for cp in reversed(self.checkpoints):
            if cp.corrupt:
                self.break_history.append({
                    "kind": "skipped_corrupt_checkpoint",
                    "checkpoint_id": cp.checkpoint_id, "tick": cp.tick,
                    "ts": time.time()})
                continue
            latest_intact = cp
            break
        return {
            "recovered": latest_intact is not None,
            "from_checkpoint": (latest_intact.checkpoint_id if latest_intact
                                else None),
            "break_history": list(self.break_history),
            "break_count": len(self.break_history),
        }

    def _append(self, path: str, record: Dict[str, Any]) -> None:
        os.makedirs(self.state_dir, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, default=str) + "\n")

    def status(self) -> Dict[str, Any]:
        return {
            "checkpoint_count": len(self.checkpoints),
            "checkpoint_corruption_count": len(self.corruption_records),
            "intact_count": sum(1 for c in self.checkpoints if not c.corrupt),
            "break_count": len(self.break_history),
            "latest_checkpoint": (self.checkpoints[-1].checkpoint_id
                                  if self.checkpoints else None),
            "append_only": True,
            "auto_delete": False,
        }
