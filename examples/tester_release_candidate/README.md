# Tester Release Candidate examples (Prompt 80)

This directory holds example assets for the **tester release candidate (RC) assembly** —
the local step that collects everything a trusted tester needs into one place, after the
tester packaging doctor and the tester safety freeze pass.

> **Architectural rule:** RC assembly is a local step only. It never publishes, uploads,
> tags, releases, or sends anything anywhere. It installs no packages, starts/controls no
> feeders, controls no hardware, and accesses no network/shell/Git/GitHub/browser/OS. The
> RC bundle is local and is shared manually only if a tester requests it.

## Contents

- `sample_ready_manifest.json` — an RC manifest for a state where packaging and the
  safety freeze are ready; readiness is `ready_with_warnings` with no missing required
  artifacts.
- `sample_blocked_manifest.json` — an RC manifest for a fresh, under-prepared state;
  readiness is `blocked` because required packaging/safety-freeze artifacts are missing.

## Demos

```bash
python examples/run_tester_rc_demo.py \
    --tester-state-dir .solaris_ai_nn_tester/test_rc_demo
python examples/run_tester_rc_manifest_demo.py \
    --tester-state-dir .solaris_ai_nn_tester/test_rc_manifest
python examples/run_tester_rc_readiness_demo.py \
    --tester-state-dir .solaris_ai_nn_tester/test_rc_readiness
python examples/run_tester_rc_docs_demo.py \
    --tester-state-dir .solaris_ai_nn_tester/test_rc_docs
python examples/run_tester_rc_bundle_demo.py \
    --tester-state-dir .solaris_ai_nn_tester/test_rc_bundle
```

The RC readiness gate blocks on packaging, safety-freeze, membrane, and fixture failures.
Open release blockers prevent the RC; critical safety blockers cannot be silently waived.

_These examples describe a local assembly step only. They make no claim of consciousness,
sentience, biological life, personhood, agency, free will, emotion, feeling,
understanding, self-awareness, autonomous self-improvement, or subjective experience._
