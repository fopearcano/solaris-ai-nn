"""Tests for the read-only localhost status server."""

from __future__ import annotations

import json
import urllib.request

from solaris_ai_nn.ops.local_status_server import LOCALHOST, LocalStatusServer


def _provider():
    return {"health": {"level": "ok"}, "status": {"steps": 5},
            "manifest": {"run_id": "r"}, "latest_report": "# report",
            "incidents": [{"type": "health_warning"}]}


def test_disabled_by_default():
    server = LocalStatusServer(provider=_provider)
    assert server.enabled is False
    assert server.url is None


def test_read_only_endpoints_return_json():
    server = LocalStatusServer(provider=_provider, port=8870)
    assert server.start() is True
    try:
        assert server.url.startswith(f"http://{LOCALHOST}:")
        for endpoint, key in (("/health", "health"), ("/status", "status"),
                              ("/manifest", "manifest"),
                              ("/incidents", "incidents")):
            with urllib.request.urlopen(server.url + endpoint, timeout=5) as r:
                payload = json.loads(r.read())
            assert key in payload
        with urllib.request.urlopen(server.url + "/nope", timeout=5) as r:
            pass
    except urllib.error.HTTPError as exc:
        assert exc.code == 404
    finally:
        server.stop()
    assert server.enabled is False


def test_binds_localhost_only():
    server = LocalStatusServer(provider=_provider, port=8880)
    server.start()
    try:
        assert server._server.server_address[0] == LOCALHOST
    finally:
        server.stop()


def test_port_busy_falls_back_gracefully():
    first = LocalStatusServer(provider=_provider, port=8890)
    assert first.start()
    second = LocalStatusServer(provider=_provider, port=8890, port_attempts=3)
    try:
        assert second.start() is True  # neighbour port
        assert second.actual_port != first.actual_port
    finally:
        first.stop()
        second.stop()
    # No ports at all -> disabled with warning, no exception.
    blocked = LocalStatusServer(provider=_provider, port=8890, port_attempts=0)
    assert blocked.start() is False
    assert blocked.warning
