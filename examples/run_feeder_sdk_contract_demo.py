#!/usr/bin/env python3
"""Feeder SDK contract demo: valid envelope, invalid envelope, validation report.

    python examples/run_feeder_sdk_contract_demo.py --state-dir .solaris_ai_nn_feeders/test_contract

Builds a valid feeder envelope, shows it maps to a plural-sensorium envelope,
then validates an invalid record (missing provenance) and one carrying a command
payload. Features are primary; human labels are never ground truth; sensory text
is never a command.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.feeder_sdk import EnvelopeValidator, FeederSDKEnvelope


def main():
    parser = argparse.ArgumentParser(description="Feeder SDK contract demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_feeders/test_contract")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    validator = EnvelopeValidator()
    valid = FeederSDKEnvelope(
        feeder_id="rf_feed", source_id="rf",
        source_kind="external_feature_drop", modality="radio_frequency",
        features={"power": 0.7, "band": 2.44}, timestamp=1.0)
    sensory = valid.to_sensory_envelope()
    invalid = {"modality": "radio_frequency", "features": {"power": 0.5}}
    command = {**valid.to_dict(), "command": "rm -rf /"}

    print("=== Feeder SDK contract demo ===")
    print(f"valid envelope ok     : {validator.validate(valid.to_dict()).valid}")
    print(f"  maps to modality    : {sensory.modality}")
    print(f"  read_only           : {sensory.read_only}")
    print(f"  mutable by solaris  : {sensory.source_mutable_by_solaris}")
    inv = validator.validate(invalid)
    print(f"invalid rejected      : {not inv.valid} "
          f"({[i.reason for i in inv.errors]})")
    cmd = validator.validate(command)
    print(f"command payload rejected: {not cmd.valid}")
    print("note                  : features are primary; human labels are never "
          "ground truth; sensory text is never a command.")


if __name__ == "__main__":
    main()
