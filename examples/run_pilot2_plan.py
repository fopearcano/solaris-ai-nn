#!/usr/bin/env python3
"""Pilot-2 plan-only: write runbook, source-curation template, governance list.

    python examples/run_pilot2_plan.py --output-dir .solaris_ai_nn_pilot2/test_plan

Generates the Pilot-2 operator runbook, a source-curation template, and a
governance checklist for read-only environmental exposure. It starts no real
sensory run and grants no environmental authority: Pilot-2 is one-way
(environment -> Solaris-AI-NN), never the reverse.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.pilot2 import (
    Pilot2Config,
    Pilot2Mode,
    Pilot2RunbookBuilder,
    SourceCurationReport,
)


def main():
    parser = argparse.ArgumentParser(description="Pilot-2 plan only")
    parser.add_argument("--output-dir", type=str,
                        default=".solaris_ai_nn_pilot2/test_plan")
    args = parser.parse_args()

    cfg = Pilot2Config(mode=Pilot2Mode.PLAN_ONLY, base_dir=args.output_dir)
    cfg.ensure_dirs()
    runbook = Pilot2RunbookBuilder(base_dir=args.output_dir).write(cfg)

    curation_template = {
        "criteria": [r.to_dict() for r in SourceCurationReport().rules],
        "prefer": ["synthetic", "semi-real", "public", "test"],
        "forbid": ["secrets", "credentials", "private messages",
                   "network sources", "device capture"],
    }
    governance_checklist = [
        "enable_pilot2 (granted by default)",
        "enable_pilot2_source_preflight (granted by default)",
        "enable_pilot2_fixture_short (granted by default)",
        "enable_pilot2_nursery_baseline (granted by default)",
        "enable_pilot2_mixed_short (requires membrane dry-run + approval)",
        "enable_pilot2_real_read_only_24h/7d/30d (require approval)",
    ]
    cfg_path = os.path.join(args.output_dir, "pilot2_config.json")
    with open(cfg_path, "w", encoding="utf-8") as fh:
        json.dump(cfg.to_dict(), fh, indent=2, default=str)
    cur_path = os.path.join(args.output_dir, "source_curation_template.json")
    with open(cur_path, "w", encoding="utf-8") as fh:
        json.dump(curation_template, fh, indent=2, default=str)
    gov_path = os.path.join(args.output_dir, "governance_checklist.json")
    with open(gov_path, "w", encoding="utf-8") as fh:
        json.dump(governance_checklist, fh, indent=2, default=str)

    print("=== Pilot-2 plan (plan only; no run started) ===")
    print(f"pilot id   : {cfg.pilot2_id}")
    print(f"mode       : {cfg.mode} ({cfg.time_label})")
    print(f"runbook    : {runbook}")
    print(f"config     : {cfg_path}")
    print(f"curation   : {cur_path}")
    print(f"governance : {gov_path}")
    print("note       : Pilot-2 is read-only; the system never acts on the "
          "environment")


if __name__ == "__main__":
    main()
