# Ultrasound echo feature feeder

_Documentation-only blueprint. This is NOT a hardware driver and is NEVER executed by Solaris. It describes how an external process should feed Solaris safely. Solaris reads the resulting event envelopes read-only; it does not control any sensor or hardware._

- modality: `ultrasound_echo`
- status: `external_hardware_required`
- external collector concept: external ultrasound logger produces echo features
- expected feature schema: `echo_reflection_event`
- output envelope path: `.solaris_ai_nn_live/inbox/echo/ultrasound.jsonl`

## What Solaris receives

- boundary
- reflectivity
- distance_estimate

## What Solaris must NOT receive

- identity inferences as truth

## Privacy risks

- proximity sensing

## Safety constraints

- no Solaris hardware control; Solaris reads envelopes only

## Example envelope

```json
{
  "event_id": "FSE_dc390ac123",
  "feeder_id": "ultrasound_feeder",
  "source_id": "ultrasound_echo_source",
  "source_kind": "external_feature_drop",
  "modality": "ultrasound_echo",
  "timestamp": 1781512023.0,
  "features": {
    "boundary": 0.5
  },
  "annotation": null,
  "annotation_status": "none",
  "provenance": {
    "source_id": "ultrasound_echo_source",
    "feeder_id": "ultrasound_feeder",
    "blueprint": "ultrasound_feeder"
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
