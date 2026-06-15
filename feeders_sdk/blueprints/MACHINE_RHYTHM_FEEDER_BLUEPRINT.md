# Machine rhythm feeder

_Documentation-only blueprint. This is NOT a hardware driver and is NEVER executed by Solaris. It describes how an external process should feed Solaris safely. Solaris reads the resulting event envelopes read-only; it does not control any sensor or hardware._

- modality: `machine_rhythm`
- status: `simulated_available`
- external collector concept: local stdlib script reading harmless machine rhythm
- expected feature schema: `machine_rhythm_event`
- output envelope path: `.solaris_ai_nn_live/inbox/system_rhythm/sys.jsonl`

## What Solaris receives

- load_proxy
- time_phase_sin
- file_count

## What Solaris must NOT receive

- privileged system data

## Privacy risks

- low; no privileged data

## Safety constraints

- no Solaris hardware control; Solaris reads envelopes only
- no process/OS control

## Example envelope

```json
{
  "event_id": "FSE_33518b963b",
  "feeder_id": "machine_rhythm_feeder",
  "source_id": "machine_rhythm_source",
  "source_kind": "external_feature_drop",
  "modality": "machine_rhythm",
  "timestamp": 1781512023.0,
  "features": {
    "load_proxy": 0.5
  },
  "annotation": null,
  "annotation_status": "none",
  "provenance": {
    "source_id": "machine_rhythm_source",
    "feeder_id": "machine_rhythm_feeder",
    "blueprint": "machine_rhythm_feeder"
  },
  "read_only": true,
  "source_mutable_by_solaris": false,
  "trust_level": "external_feature_only",
  "privacy_flags": [
    "no_raw_private_content"
  ],
  "contamination_flags": [],
  "safety_flags": [
    "text_is_observation_not_command"
  ],
  "schema_version": "feeder-sdk/1.0",
  "metadata": {}
}
```

## Limitations

- Blueprints are not hardware drivers and are not executed by Solaris.
- Real hardware integration is external/manual and out of scope for this prompt.
