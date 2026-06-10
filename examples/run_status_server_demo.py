#!/usr/bin/env python3
"""Status server demo: read-only, localhost-only, opt-in.

    python examples/run_status_server_demo.py                 # server stays OFF
    python examples/run_status_server_demo.py --status-server # serves briefly
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.ops import OperationalRunManifest, OperationalSupervisor


def main() -> None:
    parser = argparse.ArgumentParser(description="Local status server demo")
    parser.add_argument("--status-server", action="store_true",
                        help="actually start the read-only localhost server")
    parser.add_argument("--steps", type=int, default=80)
    args = parser.parse_args()

    manifest = OperationalRunManifest(
        mode="bounded", max_steps=args.steps,
        state_dir=".solaris_ai_nn_state/status_server_demo",
        artifact_dir=".solaris_ai_nn_ops",
        healthcheck_interval_steps=40,
        enabled_features={"plasticity": False, "embodiment": False,
                          "language": False, "sidecar": False,
                          "evaluation": False,
                          "local_status_server": args.status_server})
    supervisor = OperationalSupervisor(manifest=manifest)

    print("=" * 70)
    print("Solaris-AI-NN -- status server demo "
          f"(server {'ENABLED' if args.status_server else 'disabled'})")
    print("=" * 70)
    if not args.status_server:
        print("Server is disabled by default. Pass --status-server to enable")
        print("the read-only endpoint on 127.0.0.1.")
        supervisor.run()
        print(supervisor._build_status().compact_line())
        return

    status = supervisor.run()  # server runs during the session
    # The supervisor stopped the server in finalize(); restart briefly to show
    # the endpoints, then shut down cleanly.
    supervisor.status_server.start()
    url = supervisor.status_server.url
    print(f"serving (read-only, localhost only): {url}")
    for endpoint in ("/health", "/status", "/incidents"):
        with urllib.request.urlopen(url + endpoint, timeout=5) as response:
            payload = json.loads(response.read())
        preview = json.dumps(payload, default=str)[:90]
        print(f"  GET {endpoint}: {preview}...")
    supervisor.status_server.stop()
    print("server shut down cleanly.")


if __name__ == "__main__":
    main()
