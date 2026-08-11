# Event-bound long-scene editing

## Binding contract

Every narration clause carries `event_ids`. Every visual range carries one primary event and optional supporting events. Validate that the visible character, action, location, emotional state, and chronology do not contradict the narration.

Do not bind a 20–30 second narration block directly to a few generic events.
After TTS timing is available, group one to three adjacent same-event sentences
into semantic beats and record the real spoken text and time span in
`narration-beat-map.json`. A ledger title is never the narration sentence.

Lock and verify canonical identities in the event ledger first. Reject a range
when its timecode is valid but the visible character, life stage, action, or
chronology is wrong.

## Long-scene rule

- Use 1–3 continuous ranges per narration block, normally 5–19 seconds and preferably 7–14 seconds. A single correct long range is preferable to extra mismatched cuts.
- Keep establishing action, meaningful gesture, and reaction together when possible.
- Prefer continuity over excessive literalism: a preceding verified scene may continue under a related clause.
- Never retrieve footage by word similarity after script lock.
- Let one reviewed clip span several adjacent beats in the same continuity
  group. Do not create a cut at every sentence boundary. Require every
  narration clip to be at least five seconds, average at least seven seconds,
  and no more than four narration-picture cuts in a rolling 30-second window.
- Compare the sum of reviewed clip durations with the measured synthesized
  narration block before rendering. If picture is longer, select a naturally
  shorter safe range inside the same locked event; never rewrite locked
  narration, accelerate, truncate through an action, or silently substitute
  another event.
- Require selected picture duration to fit within one encoded frame of the
  assembled narration picture track. Individual clips may cross semantic-beat
  boundaries when continuity and meaning remain valid. `hold_after` defaults
  to zero. Permit at most three total hold frames per narration block, only for
  frame-rounding compensation; never clone a final frame to fill missing
  moving footage.

## Lightweight motion-coverage preflight

After final narration mastering and before VSR/STTN, convert each narration
block and every selected source range to the delivery frame rate. Require:

- moving source frames cover the block within three frames;
- moving plus declared hold frames match the block within one frame;
- no clip or whole block contains more than three hold frames;
- the picture cursor uses `clip_duration + hold_after`, exactly as the renderer
  and encoded cut audit do.

This preflight is deterministic frame arithmetic and uses no model call. On a
failure, make at most one targeted repair using a longer safe span of the same
event/scene or its already-bound reaction/context. Do not add an event, change
event order, or rewrite narration. If the second check still fails, mark the
item `visual-coverage-pending` and continue the batch instead of repeatedly
rendering or running VSR.

## Alignment grades

- `exact`: the visible character, action, place, time state, and event directly
  support the beat;
- `context`: the same character/scene or an adjacent causal reaction continues
  without contradiction;
- `neutral`: a non-contradictory establishing, object, walking, or silent
  reaction shot;
- `contradiction`: wrong identity, action, location, chronology, or emotional
  state. Never deliver it.

Require exact-match clips at least 50%, exact-match duration at least 55%,
exact-or-context duration at least 90%, neutral duration at most 10%, and zero
contradiction or unbound factual beats. Render a 540×960 preview and inspect the
start, middle, and end of every beat before subtitle removal and final encode.

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
