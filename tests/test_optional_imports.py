"""Tests for the safe optional-import layer (no Solaris_Ai required)."""

from __future__ import annotations

import sys
import types

from solaris_ai_nn.integration import optional_imports as oi


def test_unavailable_solaris_does_not_crash():
    # In this environment the real package is absent: everything degrades.
    assert oi.is_solaris_available() in (True, False)  # never raises
    if not oi.is_solaris_available():
        assert oi.import_solaris_signals() == {}
        assert oi.import_solaris_conscience() is None


def test_import_error_is_recorded():
    if not oi.is_solaris_available():
        err = oi.get_solaris_import_error()
        assert err is not None
        assert "solaris" in err


def test_mocked_availability(monkeypatch):
    fake_root = types.ModuleType("solaris")
    fake_runtime = types.ModuleType("solaris.runtime")
    fake_signals = types.ModuleType("solaris.runtime.signals")

    class Stimulus:  # minimal fake canonical classes
        pass

    class Reaction:
        pass

    fake_signals.Stimulus = Stimulus
    fake_signals.Reaction = Reaction
    monkeypatch.setitem(sys.modules, "solaris", fake_root)
    monkeypatch.setitem(sys.modules, "solaris.runtime", fake_runtime)
    monkeypatch.setitem(sys.modules, "solaris.runtime.signals", fake_signals)

    assert oi.is_solaris_available() is True
    classes = oi.import_solaris_signals()
    assert classes["Stimulus"] is Stimulus
    assert classes["Reaction"] is Reaction


def test_mocked_conscience_import(monkeypatch):
    fake_root = types.ModuleType("solaris")
    fake_conscience_mod = types.ModuleType("solaris.conscience")

    class Conscience:
        pass

    fake_conscience_mod.Conscience = Conscience
    monkeypatch.setitem(sys.modules, "solaris", fake_root)
    monkeypatch.setitem(sys.modules, "solaris.conscience", fake_conscience_mod)
    assert oi.import_solaris_conscience() is Conscience


def test_signals_module_without_classes_records_error(monkeypatch):
    fake_root = types.ModuleType("solaris")
    empty = types.ModuleType("solaris.runtime.signals")
    monkeypatch.setitem(sys.modules, "solaris", fake_root)
    monkeypatch.setitem(sys.modules, "solaris.runtime.signals", empty)
    assert oi.import_solaris_signals() == {}
    assert "no canonical signal classes" in oi.get_solaris_import_error()
