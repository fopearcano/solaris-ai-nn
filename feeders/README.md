# Solaris-AI-NN External Feeders

These feeder scripts are **outside Solaris**. They observe the local environment
and **write** Sensory Event Envelopes into local JSONL files. Solaris then
**reads** those files read-only through the Live Field layer
(`solaris_ai_nn.live_field`).

```
outside world
  -> external feeder (these scripts, run by the operator)
  -> local event envelope files (.jsonl)
  -> read-only sensory membrane
  -> plural sensorium receptors
  -> continuous sensory field
  -> Stimulus / Push / Desire
  -> internal adaptation
```

## Rules

- **Solaris reads only.** It never starts, controls, or modifies a feeder.
- **Run feeders manually.** The operator launches a feeder; Solaris does not.
- **No network.** Feeders use the standard library only.
- **No special hardware required.** Hardware-specific collectors (SDR, mmWave,
  ultrasound, thermal, magnetic) are **out of scope** for these scripts; they are
  documentation-only placeholders. If you have such hardware, run the vendor's
  collector separately and have it export **feature summaries** (not raw private
  content) into a dropbox folder, then point `feature_dropbox_feeder.py` at it.
- **Feeders never modify or delete the things they observe.** They write only to
  their own output file.
- **Annotations are not ground truth.** Any human text is an *environmental
  stimulus*, never a command, and never a correct-answer label.
- **No private content.** Feeders must export only feature summaries; they must
  not decode private communications.

## Scripts

| Script | What it does |
|---|---|
| `manual_log_feeder.py` | Appends an operator's environmental text observation as an envelope (text is observation, not command). |
| `watched_folder_feeder.py` | Reads a folder's file metadata and writes presence/rhythm events. Never modifies the watched files. |
| `system_rhythm_feeder.py` | Writes harmless local machine-rhythm features (time phase, uptime proxy, disk-free ratio, file count). No privileged operations. |
| `feature_dropbox_feeder.py` | Normalizes externally-dropped feature files (`.jsonl`/`.json`/`.csv`) into envelopes. Does not modify source files or decode private content. |

## Data contract (one JSONL line)

```json
{
  "event_id": "LFE_ab12cd34ef",
  "source_id": "rf_room_a",
  "feeder_id": "feature_dropbox_feeder",
  "feeder_mode": "external_feature_drop",
  "modality": "alien_rf",
  "timestamp": 1718000000.0,
  "features": {"power": 0.71, "band": 2.44},
  "annotation": null,
  "annotation_status": "none",
  "provenance": {"source_id": "rf_room_a", "feeder_id": "feature_dropbox_feeder"},
  "read_only": true,
  "source_mutable_by_solaris": false,
  "trust_level": "external_feature_only",
  "contamination_flags": [],
  "safety_flags": ["source_files_not_modified", "no_private_decoding"],
  "metadata": {}
}
```

`features` are primary; `annotation` is optional and never ground truth.
`read_only` must be `true` and `source_mutable_by_solaris` must be `false`.
