#!/usr/bin/env python3
"""Run the Pilot-0 read-only stream deployment.

    python examples/run_pilot_stream.py \
        --input examples/sample_streams/sensory_events.jsonl --format jsonl
    python examples/run_pilot_stream.py \
        --input examples/sample_streams/text_stream.txt --format text

Only the explicitly named input file is read (never modified, never
executed, never followed); each validated line becomes a sensory Stimulus.
``--tail`` reads the file in bounded tail mode first to show what the
ingestor accepts/rejects.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.pilot import (
    PilotDeploymentRunner,
    PilotManifest,
    ReadOnlyStreamIngestor,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pilot-0 read-only stream (bounded)")
    parser.add_argument("--input", type=str, required=True,
                        help="explicit path to ONE local jsonl/text file")
    parser.add_argument("--format", type=str, default=None,
                        choices=["jsonl", "text"],
                        help="defaults from the file suffix")
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/pilot_stream")
    parser.add_argument("--artifact-dir", type=str,
                        default=".solaris_ai_nn_pilots")
    parser.add_argument("--operator", type=str, default="local-operator")
    parser.add_argument("--tail", action="store_true",
                        help="preview the file in bounded tail mode first")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    if args.tail:
        ingestor = ReadOnlyStreamIngestor()
        preview = list(ingestor.tail_bounded(args.input, max_lines=5,
                                             fmt=args.format))
        print(f"tail preview ({len(preview)} events):")
        for event in preview:
            print(f"  [{event['modality']}] {str(event['payload'])[:60]!r}")

    manifest = PilotManifest(
        profile="read_only_stream", operator=args.operator,
        state_dir=args.state_dir, artifact_dir=args.artifact_dir,
        input_sources=[args.input], max_steps=args.steps, seed=args.seed,
        notes=f"Pilot-0 read-only stream example over {args.input}")
    # The operator passed these directories explicitly: that is the approval.
    runner = PilotDeploymentRunner(
        manifest=manifest,
        approved_output_roots=[args.state_dir, args.artifact_dir])
    for name in runner.acknowledge_risks(
            note="reviewed in run_pilot_stream example"):
        print(f"operator {args.operator!r} acknowledged risk: {name}")

    snapshot = runner.run()
    entry = snapshot["registry_entry"] or {}
    sensors = (snapshot["input_summary"] or {}).get("sensors") or []
    ingestion = ((sensors[0].get("source") or {}).get("ingestion")
                 if sensors else {})
    print("=" * 70)
    print("Solaris-AI-NN -- Pilot-0 read-only stream deployment")
    print("=" * 70)
    print(f"pilot_id:        {manifest.pilot_id}")
    print(f"input:           {args.input} (read-only)")
    print(f"status:          {entry.get('status')}")
    print(f"events accepted: {(ingestion or {}).get('events_accepted')}")
    print(f"events rejected: {(ingestion or {}).get('events_rejected')}")
    print(f"validity rate:   {(ingestion or {}).get('validity_rate')}")
    print(f"recommendation:  {entry.get('final_recommendation')}")
    print(f"pilot report:    {entry.get('report_path')}")
    if snapshot["refused"]:
        print("refused because:")
        for reason in snapshot["refusal_reasons"]:
            print(f"  - {reason}")


if __name__ == "__main__":
    main()
