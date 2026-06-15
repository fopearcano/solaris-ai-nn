# Thermal gradient feeder

_Documentation-only blueprint. This is NOT a hardware driver and is NEVER executed by Solaris. It describes how an external process should feed Solaris safely. Solaris reads the resulting event envelopes read-only; it does not control any sensor or hardware._

- modality: `thermal_gradient`
- status: `external_hardware_required`
- external collector concept: external thermal sensor logger produces gradient summaries
- expected feature schema: `thermal_gradient_event`
- output envelope path: `.solaris_ai_nn_live/inbox/thermal/thermal.jsonl`

## What Solaris receives

- gradient
- drift
- hotspot_count

## What Solaris must NOT receive

- thermal images of people

## Privacy risks

- thermal imagery of people is forbidden

## Safety constraints

- no Solaris hardware control; Solaris reads envelopes only
- summaries only; no thermal imagery of people

## Example envelope

```json
{
  "event_id": "FSE_d483188870",
  "feeder_id": "thermal_feeder",
  "source_id": "thermal_gradient_source",
  "source_kind": "external_feature_drop",
  "modality": "thermal_gradient",
  "timestamp": 1781512023.0,
  "features": {
    "gradient": 0.5
  },
  "annotation": null,
  "annotation_status": "none",
  "provenance": {
    "source_id": "thermal_gradient_source",
    "feeder_id": "thermal_feeder",
    "blueprint": "thermal_feeder"
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
