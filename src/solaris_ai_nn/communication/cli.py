"""Stdlib-only CLI helpers for the operator dialogue.

``run_scripted_dialogue`` feeds a fixed list of inputs through a gateway
(the deterministic demo path); ``run_interactive`` reads stdin until
``quit``. No external services, no unbounded loops without an exit, and
every exchange lands in the transcript.
"""

from __future__ import annotations

from typing import Any, Iterable, List, Tuple

SUPPORTED_HELP = (
    "Supported inputs: status | health | show boundaries | show inner "
    "map | show world model | why no action? | generate report | "
    "generate self-report | add operator note: <text> | approve "
    "request <id> | reject request <id> | what can I ask? | emergency "
    "stop | quit"
)


def run_scripted_dialogue(gateway: Any, inputs: Iterable[str],
                          echo: bool = True,
                          ) -> List[Tuple[str, Any]]:
    """Run a fixed input list; returns (input, response) pairs."""
    exchanges = []
    for text in inputs:
        response = gateway.handle_input(text)
        exchanges.append((text, response))
        if echo:
            print(f"> {text}")
            print(f"  [{response.kind}] {response.text[:160]}")
            if response.evidence_refs:
                print(f"  evidence: "
                      f"{', '.join(response.evidence_refs[:4])}")
            print()
    return exchanges


def run_interactive(gateway: Any, max_turns: int = 200) -> int:
    """Bounded interactive loop; 'quit' (or EOF) exits."""
    print(SUPPORTED_HELP)
    turns = 0
    while turns < max_turns:
        try:
            text = input("operator> ").strip()
        except EOFError:
            break
        if not text:
            continue
        if text.lower() in ("quit", "exit", "q"):
            break
        response = gateway.handle_input(text)
        print(f"[{response.kind}] {response.text}")
        turns += 1
    print(f"session ended after {turns} turn(s); transcript: "
          f"{gateway.session.state.transcript_path or 'in memory'}")
    return turns
