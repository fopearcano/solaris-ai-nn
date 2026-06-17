# External feeder templates (tester utilities — NOT Solaris runtime)

These scripts are **external tester utilities**. They are **not** part of the Solaris
runtime, and Solaris never starts, stops, schedules, controls, edits, or executes them.

> **Architectural rule:** Solaris does not run feeders. Feeders are dumb external
> scripts or manual files created by the tester/operator. They read simple
> local/public-safe signals and write JSONL events into the live inbox. Solaris only
> *validates* the JSONL events that appear in `.solaris_ai_nn_live/inbox/`.

## What they are

Small, boring Python scripts that write one or more read-only JSONL events to an
explicit `--out` path. Every script:

- is standalone (it does **not** import any Solaris runtime internals);
- must be **run manually** by the tester/operator (no daemon, no scheduling);
- writes JSONL events only, to an explicit `--out` path;
- supports `--dry-run` (print, do not write);
- marks every event `read_only=true`, `is_command=false`,
  `human_label_is_ground_truth=false`, `debug_gloss_is_ground_truth=false`.

## What they must never do

They must never read secrets, private messages, browser/email/contacts/calendar/
clipboard/screen-capture data, camera, microphone, GitHub, Git, shell command output,
or do filesystem-wide scans. They must never control hardware or schedule themselves.

## Scripts

| script | source | writes |
| --- | --- | --- |
| `chronos_absence_feeder.py` | `chronos_absence` | a chronos tick / absence marker |
| `machine_body_feeder.py` | `machine_body` | safe machine scalars (cpu/mem/disk %) |
| `manual_environment_writer.py` | `local_environment_manual` | manual env scalars |
| `project_artifact_feeder.py` | `project_artifact_field` | file count/mtime (no content) |
| `operator_pulse_writer.py` | `operator_pulse` | a short operator note (stimulus only) |
| `local_weather_manual_writer.py` | `local_weather_readonly_external` | manual weather |

## Example

```bash
# Manually append a chronos tick to the live inbox:
python tools/external_feeders/chronos_absence_feeder.py \
    --out .solaris_ai_nn_live/inbox/chronos_absence.jsonl

# Preview without writing:
python tools/external_feeders/machine_body_feeder.py --out /tmp/body.jsonl --dry-run
```

These are tester utilities. Review every script before running it, and never approve a
source you do not understand.
