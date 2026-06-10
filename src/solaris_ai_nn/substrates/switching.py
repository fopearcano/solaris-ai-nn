"""SubstrateSwitcher -- explicit, checkpointed, rollbackable substrate swaps.

Switching the nervous substrate is the most invasive runtime change possible,
so it is governed by strict rules (enforced here and echoed in
``plasticity/safety.py``):

* a switch must be **explicit** (``explicit=True``) -- the plasticity policy can
  never trigger one (substrate parameters are forbidden mutation targets);
* the old substrate's state is **checkpointed before** the switch (never
  discarded) and the new substrate is checkpointed after;
* input compatibility is verified; state is transferred only when dimensions
  match, otherwise the new substrate starts from a safe zero state;
* every switch is recorded in a history, and ``rollback_switch`` can restore
  the previous substrate from its checkpoint.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .base import BaseSubstrate, SubstrateConfig
from .registry import SubstrateRegistry


@dataclass
class SwitchRecord:
    """One recorded substrate switch (with enough data to roll it back)."""

    switch_id: int
    timestamp: float
    old_name: str
    new_name: str
    old_config: Dict[str, Any]
    new_config: Dict[str, Any]
    old_checkpoint: str
    new_checkpoint: str
    state_transferred: bool
    rolled_back: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SubstrateSwitcher:
    """Performs explicit substrate switches with checkpointing and rollback.

    Args:
        state_dir: Where switch checkpoints (``.npz`` + manifest) are written.
        bridge: Optional bridge to update in place (its ``substrate`` is swapped
            and a ``substrate_switches`` history attribute is maintained so the
            Inner MAP can observe switch history).
    """

    state_dir: Union[str, Path] = ".solaris_ai_nn_state/switches"
    bridge: Any = None
    history: List[SwitchRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.state_dir = Path(self.state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    # -- plan / execute -------------------------------------------------------

    def prepare_switch(self, old_substrate: BaseSubstrate, new_name: str,
                       config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate a proposed switch and describe what it would do."""
        config = SubstrateRegistry.validate_config(new_name, config)
        new_state_size = int(config.get("state_size",
                             SubstrateRegistry.default_config(
                                 new_name, old_substrate.input_size).state_size))
        return {
            "old_name": old_substrate.name,
            "new_name": new_name,
            "input_size": old_substrate.input_size,
            "old_state_size": old_substrate.state_size,
            "new_state_size": new_state_size,
            "state_transferable": new_state_size == old_substrate.state_size,
            "config": config,
        }

    def switch(self, old_substrate: BaseSubstrate, new_name: str,
               config: Optional[Dict[str, Any]] = None, *,
               explicit: bool = False,
               transfer_state: bool = True) -> BaseSubstrate:
        """Perform a checkpointed switch; requires ``explicit=True``.

        Returns the new substrate. Raises ``PermissionError`` if not explicit --
        automatic/policy-driven switching is not allowed.
        """
        if not explicit:
            raise PermissionError(
                "substrate switching requires explicit=True; automatic "
                "switching is not allowed")
        plan = self.prepare_switch(old_substrate, new_name, config)
        switch_id = len(self.history) + 1

        # 1. Checkpoint the old substrate BEFORE anything changes.
        old_ckpt = self.state_dir / f"switch_{switch_id}_old_{old_substrate.name}.npz"
        old_substrate.save_npz(old_ckpt)
        self._write_manifest(old_ckpt, old_substrate)

        # 2. Build the new substrate (same input size; seed from config or old).
        cfg = dict(plan["config"])
        new_substrate = SubstrateRegistry.create(
            new_name,
            input_size=old_substrate.input_size,
            state_size=cfg.pop("state_size", None),
            seed=int(cfg.pop("seed", old_substrate.seed)),
            **{k: v for k, v in cfg.items() if k != "input_size"},
        )

        # 3. Transfer state only when dimensions match; else safe zero start.
        transferred = False
        if transfer_state and new_substrate.state_size == old_substrate.state_size:
            new_substrate.set_state(old_substrate.get_state())
            transferred = True

        # 4. Checkpoint the new substrate AFTER the switch.
        new_ckpt = self.state_dir / f"switch_{switch_id}_new_{new_substrate.name}.npz"
        new_substrate.save_npz(new_ckpt)
        self._write_manifest(new_ckpt, new_substrate)

        record = SwitchRecord(
            switch_id=switch_id, timestamp=time.time(),
            old_name=old_substrate.name, new_name=new_substrate.name,
            old_config=old_substrate.config.to_dict(),
            new_config=new_substrate.config.to_dict(),
            old_checkpoint=str(old_ckpt), new_checkpoint=str(new_ckpt),
            state_transferred=transferred,
        )
        self.history.append(record)
        self._update_bridge(new_substrate, record)
        return new_substrate

    def rollback_switch(self, switch_id: Optional[int] = None) -> BaseSubstrate:
        """Restore the previous substrate from its pre-switch checkpoint.

        Defaults to the most recent non-rolled-back switch.
        """
        record = self._find_record(switch_id)
        if record is None:
            raise ValueError("no switch available to roll back")
        old_config = SubstrateConfig.from_dict(record.old_config)
        restored = SubstrateRegistry.create_from_config(old_config)
        restored.load_npz(record.old_checkpoint)
        record.rolled_back = True
        self._update_bridge(restored, record)
        return restored

    # -- helpers --------------------------------------------------------------

    def _find_record(self, switch_id: Optional[int]) -> Optional[SwitchRecord]:
        if switch_id is not None:
            for rec in self.history:
                if rec.switch_id == switch_id:
                    return rec
            return None
        for rec in reversed(self.history):
            if not rec.rolled_back:
                return rec
        return None

    def _update_bridge(self, substrate: BaseSubstrate, record: SwitchRecord) -> None:
        if self.bridge is None:
            return
        self.bridge.attach_substrate(substrate)
        switches = getattr(self.bridge, "substrate_switches", None)
        if switches is None:
            switches = []
            self.bridge.substrate_switches = switches
        switches.append(record.to_dict())

    @staticmethod
    def _write_manifest(npz_path: Path, substrate: BaseSubstrate) -> None:
        manifest = {
            "substrate": substrate.name,
            "config": substrate.config.to_dict(),
            "state_size": substrate.state_size,
            "input_size": substrate.input_size,
            "seed": substrate.seed,
            "saved_at": time.time(),
        }
        with open(npz_path.with_suffix(".json"), "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "switch_count": len(self.history),
            "rolled_back": sum(1 for r in self.history if r.rolled_back),
            "history": [r.to_dict() for r in self.history],
        }
