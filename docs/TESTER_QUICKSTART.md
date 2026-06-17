# Tester Quickstart

A five-minute local start for a trusted tester.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -e .
python -m solaris_ai_nn doctor
python -m solaris_ai_nn tester-demo --state-dir .solaris_ai_nn_tester --profile fixture_tester_v0
```

Then open `.solaris_ai_nn_tester/console/INDEX.md`. See `TESTER_RUNBOOK.md` for the full path and `TESTER_RELEASE_NOTES.md` for what this release is and is not.

_Local fixture-first quickstart. The runtime is local-only and non-actuating; it makes no claim of consciousness/life/agency._