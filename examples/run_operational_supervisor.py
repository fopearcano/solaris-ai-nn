#!/usr/bin/env python3
"""Run a supervised, bounded operational session.

    python examples/run_operational_supervisor.py --steps 300
    python examples/run_operational_supervisor.py --embodied --language
    python examples/run_operational_supervisor.py --status-server

Long-running modes (soak/continuous) require explicit flags in code and are
NOT reachable from this example: it always runs bounded.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.ops import OperationalRunManifest, OperationalSupervisor


def main() -> None:
    parser = argparse.ArgumentParser(description="Operational supervisor (bounded)")
    parser.add_argument("--mode", type=str, default="bounded",
                        choices=["bounded"],
                        help="this example only runs bounded mode")
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--duration", type=float, default=None)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/ops_demo")
    parser.add_argument("--artifact-dir", type=str, default=".solaris_ai_nn_ops")
    parser.add_argument("--substrate", type=str, default="esn",
                        choices=["esn", "liquid_state", "spiking_recurrent"])
    parser.add_argument("--embodied", action="store_true")
    parser.add_argument("--language", action="store_true")
    parser.add_argument("--enable-plasticity", action="store_true")
    parser.add_argument("--status-server", action="store_true",
                        help="opt-in read-only localhost status server")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    manifest = OperationalRunManifest(
        mode="bounded", max_steps=args.steps, max_duration_s=args.duration,
        state_dir=args.state_dir, artifact_dir=args.artifact_dir,
        substrate=args.substrate, seed=args.seed,
        healthcheck_interval_steps=max(25, args.steps // 5),
        enabled_features={
            "plasticity": args.enable_plasticity,
            "embodiment": args.embodied,
            "language": args.language,
            "sidecar": False, "evaluation": False,
            "local_status_server": args.status_server,
        },
        operator_notes="example bounded supervised run")
    supervisor = OperationalSupervisor(manifest=manifest, dry_run=args.dry_run)
    if supervisor.status_server is not None and supervisor.status_server.enabled:
        print(f"status server: {supervisor.status_server.url}")
    status = supervisor.run()

    print("=" * 70)
    print("Solaris-AI-NN -- operational supervisor")
    print("=" * 70)
    print(f"run_id:        {manifest.run_id}")
    print(f"mode:          {manifest.mode} (safety: {manifest.safety_mode})")
    print(f"health:        {(status['health'] or {}).get('level', 'unknown')}")
    print(f"segments:      {supervisor._segments_run}")
    print(f"lifetime steps:{(status['telemetry'] or {}).get('lifetime_steps')}")
    print(f"incidents:     {status['incident_count']}")
    for row in status["incidents"][-3:]:
        print(f"  [{row['severity']}] {row['type']}: {row['message'][:70]}")
    print(f"watchdog stop: {(status['watchdog'] or {}).get('stop_requested')}")
    print(f"checkpoint:    {manifest.state_dir}/latest_checkpoint.json")
    print(f"final status:  {supervisor.ops_dir}/status.md")
    print(f"run registry:  {supervisor.registry.path}")
    print("-" * 70)
    print(supervisor._build_status().compact_line())


if __name__ == "__main__":
    main()
