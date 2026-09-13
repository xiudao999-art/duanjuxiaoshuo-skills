---
name: index-short-drama-source-content
description: Build or refresh a reusable, timecoded content index for a complete Chinese short-drama series from canonical episode masters, verbatim transcripts, word timings, and reviewed visual annotations. Use before storyline planning or script-to-footage matching; do not use it to write narration or select a story.
---

# Index Short Drama Source Content

Create the factual retrieval layer for a whole drama. The result must let a later
editor resolve a person, event, scene, utterance, object, action, or emotional
state back to an exact source episode and safe video range.

## Boundaries

- This skill owns source inventory, transcription references, identity
  normalization, scene/event/shot marking, stable IDs, source ranges, and index
  validation.
- It does not choose a storyline, write narration, rank story candidates, or
  render video.
- Use `video-use` or an equivalent ASR workflow for verbatim text and word
  timings. ASR uncertainty must remain visible until reviewed.
- Never replace the full transcript with an episode summary.

## Workflow

1. Inventory only canonical numeric episode masters. Record the source path,
   duration, dimensions, FPS, audio presence, and a source-version fingerprint.
2. Produce one verbatim utterance stream and one word-timed stream per episode.
   Preserve original wording; mark low-confidence text instead of rewriting it.
3. Normalize characters before event annotation. Give each person one canonical
   ID and record aliases, roles, relationships, age/time states, and identity
   reveals.
4. Segment scenes and shots from actual camera/action boundaries. For each range,
   mark visible characters, location, action, emotion, objects, motion,
   dialogue state, visual quality, and `safe_in`/`safe_out`.
5. Build event nodes from goal -> obstacle -> action -> reaction -> consequence.
   Bind every event to reviewed scene/shot/utterance evidence and add temporal,
   causal, relationship, reveal, contrast, and motif edges.
6. Assemble the immutable index and validate it before storyline planning.

Read [references/index-schema.md](references/index-schema.md) when creating or
migrating index files. Start manual annotation from
[assets/source-index-template.json](assets/source-index-template.json).

## Stable IDs

Use stable IDs that do not change when titles or summaries are edited:

- episode: `EP001`
- character: `C0001`
- utterance: `EP001-U0001`
- scene: `EP001-SC0001`
- shot: `EP001-SH0001`
- event: `EV000001`

Never recycle an ID. If a record is superseded, retain its ID and mark its
status rather than silently pointing it at another range.

## Build and validate

```powershell
python scripts/build_source_index.py `
  --episodes planning/episodes.json `
  --utterances planning/utterances.jsonl `
  --characters planning/characters.json `
  --scenes planning/scenes.jsonl `
  --events planning/events.jsonl `
  --shots planning/shots.jsonl `
  --story-graph planning/story-graph.json `
  --output planning/source-content-index.json

python scripts/validate_source_index.py `
  planning/source-content-index.json `
  --output planning/source-content-index-audit.json
```

The validator must pass before another skill treats the index as authoritative.

## Required quality gates

- all canonical episodes are present and independently decodable;
- IDs are unique and references resolve;
- every time range is positive and lies inside its episode;
- every selected event has source evidence;
- every indexed shot has reviewed cut safety and dialogue state;
- character aliases and time states are canonicalized;
- uncertain transcript or identity records are explicitly flagged;
- the manifest hashes every component, so changed source/transcript/annotation
  invalidates downstream bindings.

## Outputs

Keep the component files plus `source-content-index.json` and its audit. The
combined index is the only normal input to storyline-to-footage retrieval.
