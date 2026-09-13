# Short-drama source index schema

The combined index uses `short-drama-source-index-v1` and contains seven
components: `episodes`, `utterances`, `characters`, `scenes`, `events`, `shots`,
and `story_graph`.

## Episode

Required: `episode_id`, `episode`, `source_path`, `duration`, `width`, `height`,
`fps`, `has_audio`, `source_fingerprint`.

## Utterance

Required: `utterance_id`, `episode_id`, `start`, `end`, `text`, `confidence`,
`word_timing_ref`. Recommended: `speaker_id`, `words`, `review_status`.

The text is verbatim evidence. Do not normalize it into narration prose.

## Character

Required: `character_id`, `canonical_name`, `aliases`. Recommended: `role`,
`relationships`, `goals`, `secrets`, `time_states`, `identity_changes`.

## Scene

Required: `scene_id`, `episode_id`, `start`, `end`, `characters`, `location`,
`time_state`, `summary`, `safe_in`, `safe_out`.

## Shot

Required: `shot_id`, `scene_id`, `episode_id`, `start`, `end`, `characters`,
`action`, `location`, `emotion`, `objects`, `motion`, `dialogue_state`,
`visual_quality`, `safe_in`, `safe_out`, `event_ids`.

`dialogue_state` is one of `silent`, `complete_turn`, `partial_turn`,
`overlap`, or `uncertain`. A `partial_turn` shot may be used under narration
only when its source audio is muted.

## Event

Required: `event_id`, `episodes`, `characters`, `goal`, `obstacle`, `action`,
`reaction`, `consequence`, `evidence`. Optional but important: `reveal`,
`emotion_before`, `emotion_after`, `dependencies`, `visual_strength`,
`dialogue_strength`, `hook_strength`.

Each evidence item contains `episode_id`, `start`, `end`, and at least one of
`scene_id`, `shot_id`, or `utterance_id`.

## Story graph

Use edges with `from`, `to`, and `type`. Supported types are `temporal`,
`causal`, `relationship`, `reveal`, `contrast`, and `motif`.

## Review and invalidation

Record `review_status`, `confidence`, and `notes` on uncertain records. Source
fingerprint, transcript, timing, identity, scene boundary, or event-evidence
changes require rebuilding the combined index and invalidate any downstream
binding whose recorded index hash no longer matches.
