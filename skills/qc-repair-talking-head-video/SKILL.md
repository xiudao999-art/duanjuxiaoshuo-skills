---
name: qc-repair-talking-head-video
description: Audit and repair interview, speech, lecture, podcast, and talking-head videos before delivery. Use for semantic transcript QC, wrong-word correction, filler suppression, repeated or off-topic speech removal, severe-pause repair, coherent recutting, subtitle rechunking and timing, Chinese word-boundary protection, cut-residue cleanup, audio loudness, decode, black-frame, and empty-tail checks. Supports audit-only reports and authorized repaired-video output for horizontal or vertical videos.
---

# Talking-head semantic QC and repair

Treat speech meaning as the primary signal, audio boundaries as the editing authority, and the final rendered file as the object that must pass QC.

## Route the request

- For **audit, review, or diagnosis**, inspect and report exact time ranges. Do not alter media.
- For **repair, revise, fix, shorten, or deliver**, create a reversible EDL, rebuild subtitles, render, and verify.
- For caption-only work, leave picture and audio unchanged unless the user explicitly asks for speech edits.
- For an existing production pipeline, run this skill after content selection and again after final render. Do not replace the owning design or assembly skill.

## Required inputs

Locate, in priority order:

1. Original source video or lossless edit master.
2. Word-level ASR with source timestamps. Reuse cached ASR; do not retranscribe unchanged media.
3. Approved/corrected script, subtitle file, glossary, and current EDL when available.
4. Existing final render for comparison and delivery QC.

Never use a subtitle-burned delivery file as the source of a new repair when an original or clean master exists.

## Workflow

### 1. Establish the timeline

- Probe duration, resolution, frame rate, codecs, and audio streams.
- Bind every candidate sentence to source time and output time.
- Preserve an immutable source-time EDL and derive output times from it.
- Keep all video times frame-aligned; keep audio cuts on word boundaries with 30–200 ms edge padding.

### 2. Audit meaning before mechanics

Read the entire selected transcript. Classify findings using `references/semantic-content-qc.md`.

Separate these cases:

- accidental duplicate clip or overlapping EDL;
- exact verbal repetition;
- same-meaning repetition;
- necessary thesis-to-evidence progression;
- filler, false start, or unfinished comparison;
- irrelevant aside, private reference, or long-form stage direction;
- semantic ASR error, proper-noun error, or harmless spoken grammar.

Do not delete repetition merely because words recur. Preserve definitions followed by mechanisms, claims followed by evidence, enumerations, contrasts, and deliberate rhetorical callbacks.

### 3. Build the repair plan

For every proposed removal, record:

- source start/end;
- output start/end in the current cut;
- exact spoken text;
- classification and reason;
- retained sentence before and after;
- expected new transition;
- confidence and whether listening is required.

Prefer removing whole clauses or sentences. Use an internal micro-cut only when the remaining audio forms a natural complete sentence. Keep sections coherent; do not turn a lecture into a rapid quote montage.

If the user requested only an audit, stop after the report. If the user authorized repair, continue.

### 4. Recut from clean source

Follow `references/edit-and-caption-repair.md`.

- Extract each kept range separately.
- Add 30 ms audio fades at every segment edge.
- Concatenate normalized segments.
- Recompute title, Frame, graphic, CK, and subtitle times from the new output timeline.
- Never reuse old absolute overlay times after content removal.

### 5. Rebuild and semantically correct subtitles

- Use approved wording plus word-level ASR timing.
- Remove filler from subtitles even when a harmless filler remains audible.
- Correct words only when context, terminology, slides, or the approved script supports the correction.
- Do not silently rewrite the speaker's position.
- Remove cut-away residue inherited from a discarded clause.
- Keep one semantic phrase together; never split a word, number, abbreviation, name, or protected term across cues.
- Use no punctuation when the project style requires punctuation-free captions.

Run `scripts/audit_subtitle_boundaries.py` after every subtitle change. Treat zero reported issues as necessary, not sufficient; manually inspect compound nouns and role names the rule set may not know.

### 6. Inspect every cut

At each edit boundary, inspect ±1.5 seconds of the rendered or clean master:

- listen for clipped syllables, repeated phonemes, pops, and unnatural silence;
- verify the preceding and following text forms a complete thought;
- check visual discontinuity, flash frames, and overlay state;
- distinguish a natural pause from a severe interruption.

Repair only severe pauses or clearly broken cadence. Do not over-tighten normal breath, emphasis, or speaker rhythm.

### 7. Render through the owning production workflow

Preserve the established aspect ratio, brand background, title cards, Frames, caption identity, highlight effects, and target loudness unless the user asks for a design change. Composite subtitles after other overlays so graphics cannot cover them.

### 8. Run final delivery QC

Run `scripts/probe_delivery.py` and apply `references/delivery-qc.md`.

Require:

- full decode without errors;
- expected resolution, frame rate, duration, and frame count;
- audio stream present and near the project loudness target;
- true peak within limit;
- no unintended black sequence;
- no empty video after speech ends;
- no unintended tail silence;
- subtitle boundary audit passed;
- first frame, every cut, key overlay, last caption, and last frame visually sampled.

If a render fails QC, do not deliver it. Identify whether the failure comes from source/master corruption, caption/overlay inputs, edit timing, or final encoding. Validate the repaired intermediate before rerendering.

## Output contract

For an audit, produce a time-coded report with `keep`, `trim`, `remove`, and `listen` decisions.

For a repair, preserve the previous version and deliver:

- repaired video with a distinct filename;
- source-time EDL;
- final SRT and subtitle-boundary audit JSON;
- final technical QC JSON;
- concise summary of removed content, actual duration, loudness, and any unresolved judgment calls.

