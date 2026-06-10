#!/usr/bin/env python3
"""Generate the staged soak plan (documentation only; launches nothing).

    python examples/run_soak_plan.py
    python examples/run_soak_plan.py --include-24h --include-30d
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.ops import SoakPlanBuilder


def main() -> None:
    parser = argparse.ArgumentParser(description="Staged soak plan generator")
    parser.add_argument("--output-dir", type=str,
                        default=".solaris_ai_nn_ops/soak_plan")
    parser.add_argument("--include-24h", action="store_true")
    parser.add_argument("--include-30d", action="store_true")
    args = parser.parse_args()

    plan = SoakPlanBuilder(include_24h=args.include_24h,
                           include_30d=args.include_30d).build()
    paths = plan.write(args.output_dir)
    print("Staged soak plan generated (nothing was launched):")
    print(f"  JSON:     {paths['json']}")
    print(f"  Markdown: {paths['markdown']}")
    print("-" * 60)
    for i, stage in enumerate(plan.stages, 1):
        marker = "INCLUDED" if stage.included else (
            "requires flag" if stage.requires_flag else "planned")
        print(f"  stage {i}: {stage.name:28s} [{marker}]")
    print("-" * 60)
    print("Long stages require explicit flags AND an operator decision after")
    print("reviewing the previous stage. No stage auto-launches.")


if __name__ == "__main__":
    main()
