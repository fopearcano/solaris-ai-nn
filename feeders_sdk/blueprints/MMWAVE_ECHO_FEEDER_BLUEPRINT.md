# mmWave/radar reflection metadata feeder

_Documentation-only blueprint. This is NOT a hardware driver and is NEVER executed by Solaris. It describes how an external process should feed Solaris safely. Solaris reads the resulting event envelopes read-only; it does not control any sensor or hardware._

- modality: `microwave_mmwave`
- status: `external_hardware_required`
- external collector concept: external radar/echo tool produces reflection metadata
- expected feature schema: `echo_reflection_event`
- output envelope path: `.solaris_ai_nn_live/inbox/echo/echo.jsonl`

## What Solaris receives

- distance_estimate
- reflectivity
- doppler_shift
- cluster_count
- boundary

## What Solaris must NOT receive

- person identity
- object labels as ground truth

## Privacy risks

- could track people if misused

## Safety constraints

- no Solaris hardware control; Solaris reads envelopes only
- do not label person/object as ground truth

## Example envelope

```json
{
  "event_id": "FSE_5dffcf3a96",
  "feeder_id": "mmwave_echo_feeder",
  "source_id": "microwave_mmwave_source",
  "source_kind": "external_feature_drop",
  "modality": "microwave_mmwave",
  "timestamp": 1781512023.0,
  "features": {
    "value": 0.5
  },
  "annotation": null,
  "annotation_status": "none",
  "provenance": {
    "source_id": "microwave_mmwave_source",
    "feeder_id": "mmwave_echo_feeder",
    "blueprint": "mmwave_echo_feeder"
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
