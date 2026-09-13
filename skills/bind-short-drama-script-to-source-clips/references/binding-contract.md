# Script-to-source binding contract

## Beat schema

Each narration beat contains `beat_id`, `text`, `tts_start`, `tts_end`,
`factual`, `event_ids`, `continuity_group`, and `requirements`. Requirements
may include `characters`, `action`, `location`, `time_state`, `emotion`,
`objects`, and `dialogue_state`.

Dialogue beats additionally contain `utterance_ids`, `verbatim_text`, and the
required pre/post-roll policy. Dialogue text must match the indexed utterance;
ASR may locate it but may not rewrite it.

## Candidate retrieval

The event path is authoritative. Candidate ranking may use structured tags to
order shots already attached to the required event, but it may not introduce a
new event because words look similar. Beats without event IDs remain
`unresolved-story-binding`.

Rank positive evidence in this order:

1. required event;
2. correct canonical character and time state;
3. required action and location;
4. same continuity group or adjacent causal reaction;
5. safe cut boundaries, suitable dialogue state, motion, and visual quality.

## Review file

```json
{
  "schema": "reviewed-short-drama-bindings-v1",
  "selections": [
    {
      "beat_id": "N1-B01",
      "shot_id": "EP004-SH0012",
      "match_type": "exact",
      "review_status": "passed",
      "source_start": 41.2,
      "source_end": 50.4,
      "evidence_frames": ["start.jpg", "middle.jpg", "end.jpg"],
      "notes": "Correct character, action, location and chronology"
    }
  ]
}
```

## Invalidation

A changed source-index hash, story-plan hash, narration text, event order,
mastered timing, selected shot, source range, or dialogue boundary invalidates
the affected binding audit. Picture repairs may adjust only reviewed safe
in/out points inside the same indexed shot/event.
