"""Optional read-only localhost status server. Stdlib http.server only.

Disabled by default; binds exclusively to 127.0.0.1; serves JSON snapshots of
/health /status /manifest /latest-report /incidents from a provider callable.
No command execution, no writes, no remote access, no web framework. If the
requested port is busy it tries a few neighbours, then degrades to disabled
with a warning instead of failing the run.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, Optional

LOCALHOST = "127.0.0.1"
ENDPOINTS = ("/health", "/status", "/manifest", "/latest-report", "/incidents")


def _make_handler(provider: Callable[[], Dict[str, Any]]):
    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
            data = provider() or {}
            key = {
                "/health": "health",
                "/status": "status",
                "/manifest": "manifest",
                "/latest-report": "latest_report",
                "/incidents": "incidents",
            }.get(self.path)
            if key is None:
                self._send(404, {"error": "unknown endpoint",
                                 "endpoints": list(ENDPOINTS)})
                return
            self._send(200, {key: data.get(key)})

        def _send(self, code: int, payload: Dict[str, Any]) -> None:
            body = json.dumps(payload, default=str).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args: Any) -> None:  # silence stdlib logging
            return

    return _Handler


@dataclass
class LocalStatusServer:
    """Read-only, localhost-only, opt-in status endpoint."""

    provider: Callable[[], Dict[str, Any]]
    port: int = 8765
    port_attempts: int = 5

    enabled: bool = field(default=False, init=False)
    actual_port: Optional[int] = field(default=None, init=False)
    warning: Optional[str] = field(default=None, init=False)
    _server: Optional[ThreadingHTTPServer] = field(default=None, init=False,
                                                   repr=False)
    _thread: Optional[threading.Thread] = field(default=None, init=False,
                                                repr=False)

    def start(self) -> bool:
        """Bind 127.0.0.1 on the first free port in range; False if none."""
        handler = _make_handler(self.provider)
        for offset in range(self.port_attempts):
            candidate = self.port + offset
            try:
                self._server = ThreadingHTTPServer((LOCALHOST, candidate),
                                                   handler)
                break
            except OSError:
                continue
        if self._server is None:
            self.warning = (f"no free port in {self.port}.."
                            f"{self.port + self.port_attempts - 1}; status "
                            "server disabled")
            return False
        self.actual_port = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever,
                                        name="solaris-status-server",
                                        daemon=True)
        self._thread.start()
        self.enabled = True
        return True

    @property
    def url(self) -> Optional[str]:
        if not self.enabled:
            return None
        return f"http://{LOCALHOST}:{self.actual_port}"

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None
        self.enabled = False

    def snapshot(self) -> Dict[str, Any]:
        return {"enabled": self.enabled, "url": self.url,
                "bind_host": LOCALHOST, "warning": self.warning,
                "endpoints": list(ENDPOINTS)}
