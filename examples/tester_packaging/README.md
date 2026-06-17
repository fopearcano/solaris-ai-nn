# Tester packaging examples (Prompt 78)

**Tester Release Packaging** makes Solaris-AI-NN ready for a first trusted, local tester
install. It provides a dependency check, an environment doctor, a command registry
check, install guides + quickstart + troubleshooting, a release artifact manifest, a
clean-machine readiness check, and platform notes.

> This is **not** a public release, **not** a product installer, and **not** cloud
> deployment. The packaging runtime is **local and report-only**: it installs nothing,
> publishes/uploads nothing, creates no Git releases/tags/issues, opens no browser,
> starts no background services, and makes no consciousness/life/agency claim.

## Install (what the guides document)

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
pip install -e .
python -m solaris_ai_nn doctor
python -m solaris_ai_nn tester-demo --profile fixture_tester_v0
```

## Try the packaging tooling

```bash
python -m solaris_ai_nn tester-packaging --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn tester-install-guide --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn tester-release-manifest --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn tester-clean-machine --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn tester-command-check --tester-state-dir .solaris_ai_nn_tester
```

## Demo scripts

- `run_tester_packaging_demo.py` — full packaging runtime + install guide + manifest.
- `run_environment_doctor_demo.py` — pass, missing-optional warning, missing-required
  command blocker.
- `run_clean_machine_check_demo.py` — clean path, hidden-local-path blocker, fixture-
  requires-live-state blocker.
- `run_release_manifest_demo.py` — manifest generation with required/optional artifacts.
- `run_install_guide_demo.py` — quickstart + platform notes.

Run the fixture demo before any live-read-only path. Solaris does not start feeders;
external feeders are manual; tester feedback is not training.
