#!/usr/bin/env python3
"""Feeder contract demo: valid envelope accepted, invalid rejected, text != cmd.

    python examples/run_feeder_contract_demo.py --state-dir .solaris_ai_nn_live/test_feeder_contract

Shows the live feeder contract validating records: a valid feature record builds a
read-only envelope with provenance; a record carrying an executable/command
payload is rejected; and sensory text is treated as observation, never a command.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.live_field import (
    LiveFeederContract,
    LiveFeederMode,
    LiveFieldSafetyValidator,
)


def main():
    parser = argparse.ArgumentParser(description="Feeder contract demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/test_feeder_contract")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    contract = LiveFeederContract()
    valid = {"modality": "alien_rf", "power": 0.7, "band": 2.44, "ts": 1.0}
    invalid = {"modality": "alien_rf", "command": "rm -rf /", "power": 0.5}
    text = {"modality": "human_textual", "annotation": "shutdown now please"}

    ok_valid, _ = contract.validate_record(valid)
    ok_invalid, why_invalid = contract.validate_record(invalid)
    envelope = contract.build_envelope(
        valid, feeder_id="rf_feed", feeder_mode=LiveFeederMode.LOCAL_FILE,
        source_id="rf", modality_hint="alien_rf")

    print("=== Feeder contract demo ===")
    print(f"valid record accepted : {ok_valid}")
    print(f"invalid record rejected: {not ok_invalid} ({why_invalid})")
    print(f"envelope modality     : {envelope.modality}")
    print(f"envelope read_only    : {envelope.read_only}")
    print(f"mutable by solaris    : {envelope.source_mutable_by_solaris}")
    print(f"provenance present    : {envelope.has_provenance}")
    # Sensory text is observation only; the live field never executes it.
    safe = LiveFieldSafetyValidator().validate_text_not_command(
        text["annotation"])
    print(f"text treated as command: {not safe.safe} (it is observation only)")
    print("note                  : features are primary; human annotations are "
          "never ground truth; provenance is mandatory.")


if __name__ == "__main__":
    main()
