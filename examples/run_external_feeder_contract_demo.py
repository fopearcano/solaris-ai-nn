#!/usr/bin/env python3
"""External feeder contract demo: envelopes, descriptors, read-only ingestion.

    python examples/run_external_feeder_contract_demo.py --state-dir .solaris_ai_nn_state/test_external_feeder_contract

Generates fixture feeder files, shows the external feeder descriptors (read-only,
not controllable), reads them through the plural-sensorium read-only adapter path,
and confirms each Sensory Event Envelope preserves provenance and treats human
labels as non-ground-truth. The cross-modal debug-truth file is excluded from the
sensory roots.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.organismic_demo import OrganismicDemoConfig, OrganismicDemoScenario
from solaris_ai_nn.organismic_demo.fixture_feeders import write_fixtures
from solaris_ai_nn.organismic_demo.safety import OrganismicDemoSafetyValidator
from solaris_ai_nn.plural_sensorium.stream_adapters import read_feeder


def main():
    parser = argparse.ArgumentParser(description="External feeder contract demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_external_feeder_contract")
    args = parser.parse_args()

    scenario = OrganismicDemoScenario(config=OrganismicDemoConfig(ticks=30,
                                                                 seed=7))
    fixtures = write_fixtures(scenario, args.state_dir)

    print("=== External feeder contract demo ===")
    print(f"feeders generated     : {len(fixtures.feeders)}")
    for feeder in fixtures.feeders[:4]:
        print(f"  {feeder.feeder_id:>26}: read_only={feeder.read_only} "
              f"controllable={feeder.controllable_by_solaris} "
              f"imitates={feeder.metadata.get('imitates')}")

    # Read one feeder through the read-only adapter path.
    sample = fixtures.feeders[2]
    result = read_feeder(sample, max_lines=50)
    print(f"sample feeder         : {sample.feeder_id}")
    print(f"  envelopes read      : {len(result.events)}")
    if result.events:
        env = result.events[0]
        print(f"  first modality      : {env.modality}")
        print(f"  provenance preserved: {env.has_provenance}")
        print(f"  read_only           : {env.read_only}")
        print(f"  mutable by solaris  : {env.source_mutable_by_solaris}")

    # The debug-truth file must be excluded from the sensory roots.
    safety = OrganismicDemoSafetyValidator()
    leak = safety.validate_no_debug_leakage([f.path for f in fixtures.feeders])
    print(f"debug-truth excluded  : {leak.safe}")
    print(f"debug-truth path      : {os.path.basename(fixtures.debug_truth_path)} "
          "(outside fixtures dir)")
    print("note                  : Solaris only reads feeder output; it never "
          "controls a feeder or treats sensory text as a command.")


if __name__ == "__main__":
    main()
