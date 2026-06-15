#!/usr/bin/env python3
"""Feeder pack manifest demo: supported modalities, safety/privacy notes.

    python examples/run_feeder_pack_manifest_demo.py --state-dir .solaris_ai_nn_feeders/test_manifest

Builds the feeder pack manifest + README. The packager starts no feeder, installs
no hardware dependency, and calls no network. Solaris reads only validated event
envelopes at the feeder output paths.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.feeder_sdk import FeederPackBuilder


def main():
    parser = argparse.ArgumentParser(description="Feeder pack manifest demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_feeders/test_manifest")
    args = parser.parse_args()

    out = FeederPackBuilder(state_dir=args.state_dir).write()
    manifest = out["manifest"]

    print("=== Feeder pack manifest demo ===")
    print(f"feeders catalogued    : {len(manifest.feeders)}")
    print(f"supported modalities  : {manifest.supported_modalities}")
    print(f"schema version        : {manifest.schema_version}")
    print(f"schema coverage       : {manifest.schema_coverage}")
    print(f"blueprints            : {manifest.blueprint_count}")
    print("safety notes:")
    for n in manifest.safety_notes:
        print(f"  - {n}")
    print("privacy notes:")
    for n in manifest.privacy_notes:
        print(f"  - {n}")
    print(f"what Solaris can read : {manifest.what_solaris_can_read}")
    print(f"manifest              : {out['json']}")
    print("note                  : the packager starts no feeder, installs no "
          "hardware dependency, and calls no network.")


if __name__ == "__main__":
    main()
