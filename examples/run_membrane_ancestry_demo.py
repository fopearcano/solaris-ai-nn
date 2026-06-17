#!/usr/bin/env python3
"""Membrane ancestry demo: concept/sign/cognition ancestry back to impressions.

    python examples/run_membrane_ancestry_demo.py --state-dir .solaris_ai_nn_live/ancestry_demo

Stages a clean pipeline and prints the ancestry chains: proto-concept -> impression ->
source event; sign -> concept -> impression; cognition -> sign -> concept -> impression.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.membrane_integration import MembraneIntegrationRuntime
from run_membrane_integration_demo import stage_pipeline


def main():
    parser = argparse.ArgumentParser(description="Membrane ancestry demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/ancestry_demo")
    args = parser.parse_args()

    stage_pipeline(args.state_dir)
    rt = MembraneIntegrationRuntime(args.state_dir, require_impressions=True)
    rt.run()

    print("=== Membrane ancestry demo ===")
    for chain in rt.ancestry.chains:
        d = chain.to_dict()
        print(f"  {d['artifact_type']:<16} {d['artifact_id']:<12} "
              f"impressions={d['impression_ids']} receptors={d['receptor_ids']} "
              f"events={d['source_event_ids']}")
    print("note: ancestry runs cognition_trace -> private_sign -> proto_concept "
          "-> sensory_impression -> receptor -> source_event -> source. Missing "
          "ancestry is visible; contaminated ancestry downgrades promotion.")


if __name__ == "__main__":
    main()
