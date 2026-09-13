---
name: bind-short-drama-script-to-source-clips
description: Bind an approved Chinese short-drama narration/dialogue script to exact event, scene, shot, utterance, episode, and source-time records in a validated source-content index, then emit a reviewable beat map and edit decision list. Use after story writing and before subtitle removal or rendering; do not use it to invent or rewrite the story.
---

# Bind Short Drama Script To Source Clips

Turn a locked storyline script into traceable source footage. This skill owns
retrieval, semantic matching, reviewed source ranges, continuity, and the final
script-to-index binding. It never changes the central question, causal spine,
event order, approved narration, verbatim dialogue, or payoff.

## Inputs

Require:

- a validated `short-drama-source-index-v1`;
- the approved story plan and its SHA-256;
- approved narration and verbatim dialogue beats;
- real mastered narration timings when available;
- the selected narrative Profile and its picture thresholds.

Read [references/binding-contract.md](references/binding-contract.md) before
locking any match. Start from [assets/script-beats-template.json](assets/script-beats-template.json).

## Retrieval order

1. Split narration into semantic beats of one to three adjacent sentences that
   describe the same event or continuous causal action.
2. Copy the story plan's `event_ids` into each factual beat. If a factual beat
   has no event ID, return it to story planning; do not search by narration
   keywords and pretend the result is evidence.
3. Retrieve shots bound to those events first. Then consider adjacent shots in
   the same scene for setup, gesture, reaction, or a safe cut boundary.
4. Filter by required character, action, location, time state, emotion,
   dialogue state, and chronology. A correct timecode with the wrong person is
   still invalid.
5. Rank structured candidates only as a review aid. The top result is not
   approved until start/middle/end frames and dialogue boundaries are checked.
6. Mark each selected range `exact`, `context`, `neutral`, or `contradiction`.
   Contradiction is never deliverable.

Run candidate retrieval with:

```powershell
python scripts/rank_index_candidates.py `
  --index planning/source-content-index.json `
  --beats planning/script-beats.json `
  --output planning/candidate-bindings.json
```

## Lock reviewed bindings

Create a reviewed selection file containing one row per beat with
`beat_id`, `shot_id`, `match_type`, `review_status`, and optional reviewed
source in/out overrides. Overrides must remain inside the indexed shot and use
reviewed safe boundaries.

```powershell
python scripts/build_clip_bindings.py `
  --index planning/source-content-index.json `
  --beats planning/script-beats.json `
  --reviewed planning/reviewed-bindings.json `
  --story-plan planning/selected/recap-01.json `
  --beat-map planning/narration-beat-maps/recap-01.json `
  --edl planning/edl/recap-01.json

python scripts/validate_script_clip_bindings.py `
  planning/narration-beat-maps/recap-01.json `
  --index planning/source-content-index.json `
  --story-plan planning/selected/recap-01.json `
  --output production/recap-01/qc/script-clip-binding-audit.json
```

## Editing rules

- Use one to three continuous ranges per narration block; normally prefer
  5-19 second scenes over many short shots.
- Let one verified scene cover adjacent beats in the same continuity group.
- Do not create a cut merely because a sentence begins.
- Source picture and dialogue remain at `1.0x`.
- Start dialogue before its first word, finish the complete turn, and keep
  0.3-0.5 seconds of reaction space when available.
- A partial-turn shot may be used only muted under narration.
- Do not reuse a shot/range inside one video unless an intentional callback is
  declared and audited.
- Never fall back to word similarity after the story is locked.

## Hard gates

- beat text round-trips exactly to the approved narration;
- the recorded source-index hash and story-plan hash match;
- all factual beats resolve to known events;
- all selected shots resolve and overlap the beat's events;
- source ranges stay inside indexed shots and have safe boundaries;
- exact-or-context duration is at least 90%;
- contradiction count and unbound factual beat count are zero;
- selected Profile thresholds for exact coverage, average shot length, and
  under-five-second clips pass;
- a low-resolution encoded preview is visually approved before VSR/STTN or
  final rendering.

## Outputs

Produce `candidate-bindings.json`, `reviewed-bindings.json`,
`narration-beat-map.json`, `edit-decision-list.json`, preview evidence frames,
and `script-clip-binding-audit.json`. Downstream subtitle removal and rendering
must consume the locked EDL rather than searching the source again.
