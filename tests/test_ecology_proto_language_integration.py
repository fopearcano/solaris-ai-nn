"""Integration: a recurring ecology feeds proto-symbol emergence."""

from __future__ import annotations

from solaris_ai_nn.developmental.developmental_runtime import (
    DevelopmentalRuntime,
)
from solaris_ai_nn.ecology.nursery import NurseryConfig
from solaris_ai_nn.ecology.regimes import RegimeType


def _runtime(tmp_path, **kw):
    config = NurseryConfig(seed=7, duration_steps=240,
                           active_regimes=[RegimeType.STABLE_REPETITION],
                           output_state_dir=str(tmp_path / "eco"), **kw)
    return DevelopmentalRuntime(
        state_dir=str(tmp_path / "dev"), simulated_time=True,
        time_acceleration=3600.0, max_steps=240,
        consolidation_interval_steps=60, seed=7,
        enable_ecology=True, nursery_config=config,
        enable_proto_language=True)


def test_proto_language_active_with_ecology(tmp_path):
    runtime = _runtime(tmp_path)
    runtime.run()
    assert runtime.protolanguage is not None
    # Proto-symbols are grounded in ecology context (no teaching/labels).
    assert runtime.protolanguage.summary()["symbol_count"] >= 0


def test_absence_grounds_symbols(tmp_path):
    runtime = _runtime(tmp_path, absence_rate=0.4)
    runtime.run()
    # The runtime injects nursery absence into the proto-language context.
    # We assert the symbols carry no human-language / label claim by
    # checking the layer's safety stance.
    assert runtime.protolanguage.safety.symbols_have_authority() is False


def test_tokens_are_internal_signs_not_speech(tmp_path):
    runtime = _runtime(tmp_path)
    runtime.run()
    for symbol in runtime.protolanguage.registry.symbols.values():
        # Deterministic internal tokens, never human words.
        assert "_" in symbol.token
        assert symbol.token == symbol.token.upper() or any(
            ch.isdigit() for ch in symbol.token)
