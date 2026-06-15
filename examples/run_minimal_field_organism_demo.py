#!/usr/bin/env python3
"""Minimal field organism demo: continuous flux -> changed future perception.

    python examples/run_minimal_field_organism_demo.py --state-dir .solaris_ai_nn_state/test_minimal_field_organism

Generates fixture external feeders (human-like text/light/temperature and
non-human RF/echo/vibration/magnetic), drives the plural sensorium over a bounded
continuous-flux scenario, lets receptors adapt and the sensory field evolve, runs
the changed-perception probe, and writes the report. No hardware; debug-truth
excluded from perception; this is not consciousness evidence.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.organismic_demo import (
    MinimalFieldOrganismRunner,
    OrganismicDemoConfig,
)


def main():
    parser = argparse.ArgumentParser(description="Minimal field organism demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_minimal_field_organism")
    parser.add_argument("--ticks", type=int, default=120)
    args = parser.parse_args()

    runner = MinimalFieldOrganismRunner(
        state_dir=args.state_dir,
        config=OrganismicDemoConfig(ticks=args.ticks, seed=7))
    result = runner.run()
    status = runner.demo_status()
    out = runner.write_artifacts()
    probe = runner.probe_result

    print("=== Minimal field organism demo ===")
    print(f"ticks run             : {result['ticks_run']}")
    print(f"events ingested       : {result['events_ingested']}")
    print(f"active modalities     : {status['active_modality_count']}")
    print(f"active receptors      : {status['active_receptor_count']}")
    print(f"baseline shifts       : {status['baseline_shift_count']}")
    print(f"absence events        : {status['absence_event_count']}")
    print(f"rhythm signatures     : {status['rhythm_signature_count']}")
    print(f"invariant candidates  : {status['invariant_candidate_count']}")
    print(f"cross-modal relations : {status['cross_modal_relation_count']}")
    print(f"proto-symbols         : {status['proto_symbol_candidate_count']}")
    print(f"changed-perception    : score={probe.changed_perception_score} "
          f"changed={probe.changed}")
    print(f"report                : {out['markdown']}")
    print("note                  : evidence of changed response structure only; "
          "this does not prove consciousness, sentience, life, or understanding.")


if __name__ == "__main__":
    main()
