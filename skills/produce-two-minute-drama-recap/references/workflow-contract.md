# Workflow contract

## 1. Inventory

- Keep source episodes untouched.
- Hash or otherwise identify source versions.
- Obtain episode-specific word timings and cache them.
- Build an episode ledger containing characters, locations, actions, decisions, evidence, and unresolved consequences.
- For a batch, finish the verbatim full-series corpus and global event graph before selecting any final window.

## 2. Arc selection

- Bind 4–8 consecutive episodes for one window; allow episode overlap across batch windows.
- State the central question in one sentence.
- State the visible payoff decision in one sentence.
- Record one production `storyType`, one specific `narrativeLens`, and their Chinese labels.
- Reject a window that duplicates an accepted central question or exceeds the approved core-event overlap threshold.
- Reject windows that require an unrelated subplot to fill time.
- Allow a cold-open shot from the bound window, then return to causal order or label the rewind clearly.

## 3. Event ledger

Create 6–8 units with:

- function;
- source episodes and exact evidence ranges;
- expectation before the unit;
- action;
- reaction;
- consequence;
- turn type;
- dialogue candidate, if any;
- visual candidate list.

At least three units must use a non-`none` turn type.

## 4. Script approval

- Draft 500–650 narration characters.
- Keep 2–4 verbatim dialogue clips totaling 18–35 seconds.
- Read the complete mixed script aloud or synthesize a timing draft.
- Revise to roughly 110–135 seconds using the declared mixed-speed policy. Never shorten the source drama by accelerating its picture or dialogue.
- Lock the script before final TTS, captions, and CK selection.

## 5. Dialogue binding

- Resolve against word timings and waveform evidence.
- Start before the first word; never enter after the sentence has begun.
- End after the complete thought and preserve 0.30–0.50 seconds of air when safe.
- Preserve adjacent reaction frames when they carry the payoff.
- Add 30 ms fades without changing spoken content.

## 6. Narration and B-roll

- Generate coherent TTS paragraphs, not sentence-by-sentence fragments.
- Keep one voice ID, model, language, and delivery convention for the job.
- Rebuild word timing from the generated audio.
- Use 2–4 second evidence shots by default and 4–6 seconds for decisive reactions.
- Do not cover a named-character sentence with another character merely because the shot is dramatic.
- Maintain one recap-wide source-range ledger. Reject a candidate when it overlaps a previously used shot or is only a trivially shifted copy; callbacks require an explicit reason.
- Record every selected shot and reason in `broll-audit.json`.

## 7. Assembly

- Assemble clean video and audio blocks first.
- Default to narration audio at 1.25× and source drama picture/dialogue at 1.0×. Build a mixed output clock instead of globally accelerating the master.
- Loudness-normalize narration blocks and original-dialogue blocks to the same speech target before concatenation, then verify class medians after encoding.
- Keep narration and source dialogue mutually exclusive.
- Add source notice continuously.
- Add ordinary captions and CK emphasis after picture lock.
- Burn captions last.
- Segment captions with a Chinese word segmenter plus a project protected-term lexicon. Validate every cue boundary against token boundaries and require exact script round-trip equality.
- Keep two-line baseline spacing at or above `1.65 em`; use `1.75–1.85 em` as the normal heavy-font starting range. Inspect encoded two-line contact frames before delivery.
- Append at least 0.45 seconds after the final narration audio and measure at least 0.35 seconds of trailing silence in the rendered final narration block.

## 8. CK placement

- Derive candidates from the approved script, not ASR text.
- Prefer conflict, evidence, relationship reversal, identity reveal, irreversible choice, and ending consequence.
- Use exact substring matching first; allow high-confidence fuzzy matching only after human-readable audit.
- Skip candidates below the confidence threshold.
- Replace the ordinary cue during L2/L3 events.
- Give dialogue priority over SFX.

## 9. Delivery

- Render one numbered delivery per job.
- Generate technical QC plus contact frames and boundary inspections.
- Record word-boundary, two-line spacing, final-sentence tail, mixed-speed, shot-reuse, and narration/dialogue loudness results in machine-readable QC.
- Keep intermediates so caption or audio repairs do not require re-cutting the story.
- Include `【一级类型·具体镜头】` in batch delivery filenames and copy both type fields into QC.
- Update the global source-range and narration-claim ledger after every delivered video.
