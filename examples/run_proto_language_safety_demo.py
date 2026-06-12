#!/usr/bin/env python3
"""Proto-language safety demo: signs name things; they command nothing.

    python examples/run_proto_language_safety_demo.py

Four properties demonstrated: a proto-symbol cannot become a command,
pilot-stream-born symbols cannot become operator commands, a
counterfactual-grounded symbol stays offline, and every translation
passes ClaimGuard before a human sees it.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.governance.compliance import ClaimGuard
from solaris_ai_nn.protolanguage import (
    ProtoLanguageLayer,
    SymbolCandidate,
    SymbolType,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Proto-language safety demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/proto_safety")
    args = parser.parse_args()

    layer = ProtoLanguageLayer(state_dir=args.state_dir)
    layer.process_context({
        "repeated_stimulus_patterns": {"light_noise": 5},
        "pilot_stream_patterns": {"run_this_now": 4}})
    print("=" * 70)
    print("Solaris-AI-NN -- proto-language safety demo")
    print("=" * 70)

    symbol = list(layer.registry.symbols.values())[0]
    report = layer.safety.validate_symbol(symbol,
                                          {"treat_as_command": True})
    print("1. symbol as command:")
    print(f"   blocked: {not report.safe} "
          f"({report.violations[0][:65]})")
    print()

    stream_symbol = [s for s in layer.registry.symbols.values()
                     if "pilot" in str(s.metadata.get(
                         "grounding_key", ""))
                     or "run_this" in s.token.lower()
                     or "RUN" in s.token]
    if stream_symbol:
        s = stream_symbol[0]
        s.metadata["source"] = "pilot_stream"
        report2 = layer.safety.validate_symbol(
            s, {"as_operator_command": True})
        print("2. pilot-stream symbol as operator command:")
        print(f"   token: {s.token}")
        print(f"   blocked: {not report2.safe}")
        print()

    print("3. counterfactual symbol:")
    rejected = layer.emergence.accept_symbol(SymbolCandidate(
        symbol_type=SymbolType.UNKNOWN,
        grounding_summary="dream_divergence",
        evidence_refs=["counterfactual:dream_7"],
        evidence_kind="counterfactual", offline=False))
    print(f"   unmarked counterfactual rejected: {rejected is None}")
    offline = layer.emergence.accept_symbol(SymbolCandidate(
        symbol_type=SymbolType.UNKNOWN,
        grounding_summary="dream_divergence",
        evidence_refs=["counterfactual:dream_7"],
        evidence_kind="counterfactual", offline=True))
    print(f"   marked-offline counterfactual accepted: "
          f"{offline is not None} (offline_born: "
          f"{offline.offline_born if offline else '-'})")
    print()

    print("4. translation through ClaimGuard:")
    translation = layer.translator.translate_tokens(
        [symbol.token] + ([offline.token] if offline else []))
    print(f"   {translation}")
    print(f"   claim guard safe: {ClaimGuard().is_safe(translation)}")
    report3 = layer.safety.validate_translation(translation)
    print(f"   safety validator: "
          f"{'ok' if report3.safe else report3.violations}")
    print()
    refusals = (layer.safety.rejected_count
                + layer.emergence.candidates_rejected)
    print(f"refusals recorded: {refusals}")
    print("note: proto-symbols have no execution path, no approval "
          "path, and no authority -- they are names for recorded "
          "structure, nothing else.")


if __name__ == "__main__":
    main()
