# Tester console examples (Prompt 76)

The **Minimal Local Operator Console** turns the many JSON/Markdown artifacts produced
by the alpha/live/tester runs into a single static, local, **read-only** dashboard --
static Markdown (`INDEX.md`, the primary output) plus an optional static offline HTML
page (`INDEX.html`).

> It is a **read-only console, not a control panel.** It runs no server by default,
> opens no browser, controls no feeders/hardware, accesses no network/shell/Git/GitHub,
> publishes/uploads nothing, executes no artifact contents, shows no raw private
> payloads by default, and makes no consciousness/life/agency claim.

## Try it

```bash
# Build a fixture run first so the console has something to summarize:
python -m solaris_ai_nn tester-demo --state-dir .solaris_ai_nn_tester --profile fixture_tester_v0
# Then build the console:
python -m solaris_ai_nn tester-console --state-dir .solaris_ai_nn_live --tester-state-dir .solaris_ai_nn_tester --console-dir .solaris_ai_nn_tester/console
# Open the generated INDEX.md (or INDEX.html) in your editor/browser MANUALLY.
```

## Demo scripts

- `run_tester_console_demo.py` — builds the console from synthetic fixture/live
  artifacts and generates `INDEX.md` + `INDEX.html`.
- `run_tester_console_status_demo.py` — pass, warnings, blockers, missing optional.
- `run_tester_console_safety_demo.py` — quarantine, membrane-bypass, unsupported-claim
  blockers.
- `run_tester_console_runs_demo.py` — a run index with fixture/live/membrane runs and a
  latest-run marker.
- `run_tester_console_next_actions_demo.py` — next action with no fixture, after a
  fixture pass, and after a safety blocker.

The console does not open the generated files for you — open them yourself. A green
dashboard is operational status, not evidence of inner life.
