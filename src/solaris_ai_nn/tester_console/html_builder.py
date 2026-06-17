"""Console HTML builder -- a static, offline, control-free dashboard.

:class:`TesterConsoleHtmlBuilder` writes a single static ``INDEX.html`` that works fully
offline: no external CDN/fonts/images, no required JavaScript, no network requests, no
auto-refresh, no forms, and no active controls (no buttons that do anything). It mirrors
the Markdown dashboard and never exposes raw private payloads. It is a static report,
not an app.
"""

from __future__ import annotations

import html
import os
from dataclasses import dataclass
from typing import Any, Dict, List

_STYLE = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
max-width:960px;margin:1.5rem auto;padding:0 1rem;color:#1a1a1a;
background:#fafafa;line-height:1.5}
h1,h2{border-bottom:1px solid #ddd;padding-bottom:.2rem}
table{border-collapse:collapse;width:100%;margin:.5rem 0}
th,td{border:1px solid #ccc;padding:.3rem .5rem;text-align:left;font-size:.9rem}
.banner{background:#eef;border:1px solid #ccd;padding:.6rem;border-radius:6px}
.blocker{color:#a00;font-weight:bold}
.warning{color:#a60}
.ok{color:#070}
.muted{color:#666;font-size:.85rem}
""".strip()


@dataclass
class TesterConsoleHtmlBuilder:
    """Builds the static, offline INDEX.html (no controls, no network)."""

    dashboard: Any
    safety_panel: Any

    def write(self, console_dir: str) -> str:
        os.makedirs(console_dir, exist_ok=True)
        path = os.path.join(console_dir, "INDEX.html")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self._render())
        return path

    def _render(self) -> str:
        s = self.dashboard.sections
        rs = s["release_status"]
        sp = self.safety_panel.to_dict()
        parts: List[str] = [
            "<!DOCTYPE html>", "<html lang='en'><head>",
            "<meta charset='utf-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1'>",
            "<title>Solaris-AI-NN Tester Console</title>",
            f"<style>{_STYLE}</style></head><body>",
            "<h1>Solaris-AI-NN Tester Console</h1>",
            "<p class='banner'>This console is <b>read-only</b>. It does not "
            "start feeders, control hardware, access network/Git/GitHub/shell/"
            "browser/OS, run a server, open a browser, publish/upload, execute "
            "artifact contents, train on tester feedback, or make any claim of "
            "consciousness, sentience, biological life, personhood, agency, free "
            "will, emotion, feeling, understanding, self-awareness, or subjective "
            "experience.</p>",
            "<h2>Release Status</h2>",
            f"<p>overall health: <b>{_e(rs['overall_health'])}</b> &middot; "
            f"release ready: {_e(rs['release_ready'])} &middot; blockers: "
            f"{_e(rs['blocker_count'])} &middot; warnings: "
            f"{_e(rs['warning_count'])}</p>",
            "<h2>Quick Safety Status</h2>",
            f"<p>safety: <b class='{_sev(sp['safety_status'])}'>"
            f"{_e(sp['safety_status'])}</b> &middot; blockers: "
            f"{_e(sp['blocker_count'])}</p>",
            self._table(["check", "severity", "detail"],
                        [[f["check"], f["severity"], f["detail"]]
                         for f in sp["findings"]]),
            "<h2>Summary cards</h2>",
            self._table(["area", "status", "report"],
                        [[c["title"], c["status"], c["report_path"] or "-"]
                         for c in s["cards"]]),
            "<h2>Missing required artifacts</h2>",
            self._ul(s["missing_artifacts"] or ["none"]),
            "<h2>Skipped optional stages</h2>",
            self._ul(s["skipped_optional_stages"] or ["none"]),
            "<h2>Next recommended action</h2>",
            self._next_action(s.get("next_recommended_action", {})),
            "<h2>Run index</h2>",
            self._table(["run id", "type", "status", "latest"],
                        [[r["run_id"], r["run_type"], r["status"],
                          "yes" if r["latest"] else ""]
                         for r in s["run_index"]["runs"]]),
            "<h2>What this console cannot do</h2>",
            self._ul(self.dashboard.to_dict()["what_this_console_cannot_do"]),
            "<p class='muted'>Static offline report. No JavaScript is required; "
            "no network requests are made.</p>",
            "</body></html>",
        ]
        return "\n".join(parts)

    @staticmethod
    def _table(headers: List[str], rows: List[List[Any]]) -> str:
        out = ["<table><thead><tr>"]
        out += [f"<th>{_e(h)}</th>" for h in headers]
        out.append("</tr></thead><tbody>")
        for row in rows:
            out.append("<tr>" + "".join(f"<td>{_e(c)}</td>" for c in row)
                       + "</tr>")
        out.append("</tbody></table>")
        return "".join(out)

    @staticmethod
    def _ul(items: List[Any]) -> str:
        return "<ul>" + "".join(f"<li>{_e(i)}</li>" for i in items) + "</ul>"

    @staticmethod
    def _next_action(na: Dict[str, Any]) -> str:
        if not na:
            return "<p>none</p>"
        manual = " (requires manual approval)" \
            if na.get("requires_manual_approval") else ""
        return (f"<p><b>{_e(na.get('action'))}</b> "
                f"({_e(na.get('priority'))}){_e(manual)} &mdash; "
                f"{_e(na.get('detail'))}</p>")


def _e(value: Any) -> str:
    return html.escape(str(value))


def _sev(status: str) -> str:
    return {"blocked": "blocker", "warnings": "warning", "ok": "ok"}.get(
        status, "muted")
