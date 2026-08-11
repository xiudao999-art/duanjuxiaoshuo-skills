# Event-bound long-scene editing

## Binding contract

Every narration clause carries `event_ids`. Every visual range carries one primary event and optional supporting events. Validate that the visible character, action, location, emotional state, and chronology do not contradict the narration.

## Long-scene rule

- Use 1–3 continuous ranges per narration block, normally 5–19 seconds. A single correct long range is preferable to extra mismatched cuts.
- Keep establishing action, meaningful gesture, and reaction together when possible.
- Prefer continuity over excessive literalism: a preceding verified scene may continue under a related clause.
- Never retrieve footage by word similarity after script lock.
- Compare the sum of reviewed clip durations with the measured synthesized
  narration block before rendering. If picture is longer, add only a useful
  causal beat or select a naturally shorter reviewed range; never accelerate,
  truncate, or silently substitute the locked source scene.
- Require selected picture duration to fit within one encoded frame of the
  narration block. Permit at most six seconds of deliberate final-frame hold.

## Boundary rule

- Inspect ±1.5 seconds around every proposed cut.
- Cut at a stable camera boundary, action rest, or verified shot change.
- Avoid a range shorter than 1.2 seconds unless it is an intentional accent and passes flash-frame inspection.
- After encoding, sample the frame before the cut, the cut frame, the next frame, and +0.2/+0.5 seconds.
- For separately cleaned ranges with identical source endpoints, merge a truly
  continuous scene or leave one encoded frame between them. Do not encode the
  shared boundary frame twice.

## Dialogue handoff

- Preserve the complete turn and 0.3–0.5 seconds post-roll.
- Narration may start only after the source sentence and reaction breath finish.
- Mute partial dialogue used as B-roll.
