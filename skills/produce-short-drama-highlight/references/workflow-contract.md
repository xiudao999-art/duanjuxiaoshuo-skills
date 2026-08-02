# Workflow contract

## Source hierarchy

1. Approved Markdown `★` text controls narration and narration captions.
2. Approved Markdown `☆` text controls which original dialogue must be preserved.
3. Episode-specific word/phrase timing locates dialogue but never replaces approved wording.
4. Source frames decide whether a cut is visually and emotionally usable.

## Beat model

Represent each article section as an ordered list:

```json
{
  "index": 2,
  "title": "一巴掌打出的缘分",
  "episodes": [2],
  "beats": [
    {"type": "narration", "text": "批准的旁白原文"},
    {"type": "dialogue", "speaker": "安然", "stage": null, "text": "批准的对白"}
  ]
}
```

The final timeline must retain this order. A long narration beat may use several visual clips but remains one coherent TTS request unless the API limit or a real semantic turn requires splitting.

## Dialogue locking

- Search only transcripts belonging to the named episodes.
- Use fuzzy text matching to propose candidates; manually inspect every chosen candidate.
- Start on the first word of the approved sentence, normally with 0.10–0.30 seconds of pre-roll.
- End after the last word and preserve 0.30–0.50 seconds of room before the next unrelated sentence. Extend farther only for a meaningful reaction.
- If one Markdown beat compresses several non-contiguous source sentences, either keep the full continuous exchange or document a sentence-safe internal cut.
- Apply exactly one 30 ms fade-in and fade-out at the extracted clip boundary. Do not add another long Remotion fade.

## Narration

- Use the selected voice consistently for all highlights in a batch.
- Submit complete paragraphs or semantic blocks; avoid sentence-by-sentence voice drift.
- Trim generated edge silence, preserve the raw response, and do not change speed, pitch, or volume to repair a poor voice.
- Master after assembly rather than modifying the TTS request volume.
- Keep credentials in environment variables for the command only. Never write them to scripts, manifests, logs, or reports.

## Visual evidence for narration

- Default shot length: 2–4 seconds.
- Prefer the article's `画面引用` order.
- Bind every narration clause to a visible subject, action, location, consequence, or reaction.
- Use a reaction tail after a narration sentence when it creates breathing room.
- Preserve the named character's identity. Audit face/gender/costume/location mismatches.
- Avoid repeating the same source range within one highlight unless it functions as an intentional callback.

## Composition

- Target 1080×1920 at 25 fps unless the source or user requires another format.
- Use a short opening title overlay, then let drama imagery occupy the full frame.
- Do not add a lower-half gradient or mask.
- Use narration captions as a large two-line rail near the lower safe area. Existing source dialogue subtitles may remain when readable.
- Place the persistent source notice at the upper-right: `视频来自短剧《在你心上迫降》`, approximately 27 px at 1080×1920, white at about 82% opacity with a dark shadow.
- Layer order: base video, designed overlays/title, source notice, narration captions last.
- Narration and dialogue audio must never overlap.

## Subtitle contract

- Generate fresh word timings for every newly synthesized narration file.
- Store `source: script-text+asr-timing` and the exact `scriptText`.
- Preserve proper names and fixed terms as protected tokens.
- Ensure joined cue text equals approved narration after whitespace normalization.
- Validate all segment manifests with the `script-aligned-subtitles` validator.

## Delivery cadence

- Produce indices in ascending order unless the user selects another order.
- Finish full QC and copy the delivery MP4 before starting the next index.
- Report the completed output path as soon as each index passes.

