---
name: produce-multi-storyline-drama-batch
description: Transcribe an entire Chinese short-drama series, derive many distinct storylines through narrative templates, and produce a complete batch of roughly two-minute 9:16 narration-led recap videos with event-bound long shots, complete source dialogue, burned-source-subtitle removal, single-line word-safe script-aligned captions, deduplication, encoded-frame subtitle reset inspection, and hard-gated final delivery QC. Use when the user asks to make a whole drama into many story lines, multiple narrative categories, all qualified videos, subtitle-safe finished videos, or a final delivery-level batch rather than simple consecutive episode slices.
---

# Produce Multi-Storyline Drama Batch

## Purpose

Turn one complete drama into every qualified, meaningfully different recap window. Treat story selection, evidence binding, editing, subtitles, and QC as one pipeline; do not render speculative jobs and repair them casually afterward.

## Required companion skills

1. Read `hyperframes` first for every video task.
2. Read `produce-two-minute-drama-recap` and its routed references for narration, narrative lenses, and base rendering.
3. Read `script-aligned-subtitles` before generating captions.
4. Read `qc-repair-talking-head-video` before final delivery QC.
5. Use `video-use` or an equivalent word-timed ASR pipeline for source dialogue boundaries.
6. Read [hard-subtitle-treatment.md](references/hard-subtitle-treatment.md) whenever any source master contains burned subtitles.
7. Read [narrative-profiles.md](references/narrative-profiles.md) before selecting a story structure. Read [sample-style-story-editing.md](references/sample-style-story-editing.md) only when the selected profile is `P01_dual_time_conflict`.
8. Read [semantic-visual-alignment.md](references/semantic-visual-alignment.md) before binding narration footage or approving a preview.

## Operating modes

- `complete`: generate and deliver every candidate that passes differentiation and quality gates. This is the default for “做全”.
- `fixed-count`: create exactly the requested number, ranked by story quality.
- `preview-first`: render one sample only when the user explicitly requests confirmation.

Never pause between batches unless the user asks for a checkpoint.

## Workflow

### 1. Inventory and transcribe the whole series

- Accept only canonical numeric episode masters; ignore download duplicates and prior exports.
- Probe duration, dimensions, FPS, audio, and decode health.
- Produce a full-text transcript and a word-timed transcript for every episode.
- Preserve original dialogue text. ASR is evidence to locate dialogue, never permission to rewrite it.
- Build `episode-corpus.json` and record transcript confidence or uncertainty.

### 2. Build the event and scene ledger before writing scripts

Create stable records with:

`event_id`, `scene_id`, `episode`, `source_start`, `source_end`, `safe_in`, `safe_out`, `characters`, `location`, `action`, `conflict`, `reveal`, `relationship`, `emotion`, `dialogue`, `visual_tags`, `payoff`, `shot_boundary_confidence`.

The ledger is the only normal source for narration visuals. Never search footage at render time by matching narration words.

Before using the ledger, audit canonical character identities, aliases, age/time
states, actions, and episode/source ranges against representative frames and
the word-timed transcript. Correct a wrong ledger record before binding any
footage; a valid timecode attached to the wrong character is still invalid
evidence.

### 3. Generate multiple narrative families

Read [multi-storyline-templates.md](references/multi-storyline-templates.md). For a normal series, attempt 8–10 applicable families and multiple windows per family. A candidate must define:

- one central question;
- one explicit `narrative_profile` and profile version;
- a causal event path, not a chronological event list;
- a source hook whose type and duration satisfy the selected profile;
- an escalation and a real stage payoff or honest unresolved cliffhanger;
- 4–8 source episodes where the material supports it; non-contiguous episodes are allowed for thematic lines;
- explicit event IDs and source ranges for every narration block.

### 4. Score, differentiate, and select

Score each candidate for continuity, logic, attraction, payoff, evidence coverage, editability, and differentiation. Simulate three reviewers: story editor, ordinary viewer, and evidence editor.

Two candidates may share source material, but each must differ in central question, causal spine, payoff, narration wording, and principal footage. Reject a candidate when its core-event overlap with a stronger candidate reaches 70% or more, or when the difference is merely a title/ordering change.

In `complete` mode, keep every candidate that passes the quality floor. Do not invent a quota.

### 5. Write grounded mixed scripts

Read [narrative-profiles.md](references/narrative-profiles.md). Apply the global
grounding and delivery contract to every family, then apply only the selected
profile's chronology, hook, dialogue budget, picture thresholds, and payoff
test. For `P01_dual_time_conflict`, also read
[sample-style-story-editing.md](references/sample-style-story-editing.md).

- Target about 110–135 seconds after assembly.
- Calibrate against the locked TTS voice before rendering. A practical starting
  range is 450–630 Chinese characters at 1.25x narration speed, then measure the
  synthesized files instead of trusting character count.
- Use the selected profile's dialogue-turn and duration budget. Complete
  dialogue boundaries remain global even when a profile permits zero dialogue.
- Use the selected profile's native causal sequence; do not force reverse
  chronology, investigation, romance, or anthology logic onto another profile.
- Every factual clause must map to one or more `event_id` values.
- End on a complete sentence and retain at least 0.45 seconds of audible/visual breathing room.
- Remove any attractive but unsupported motive, document, prop, action, or
  consequence before TTS. Dramatic wording never overrides the full-series
  transcript and event ledger.

### 6. Bind long continuous visuals at planning time

Read [semantic-visual-alignment.md](references/semantic-visual-alignment.md) and
[event-bound-editing.md](references/event-bound-editing.md). Treat visual
alignment as a downstream evidence operation: do not change the selected
family, narrative profile, central question, causal spine, or payoff merely to
improve alignment metrics.

- Synthesize the locked narration and obtain real word timings before final
  footage placement. Split adjacent narration into semantic beats of one to
  three sentences that describe the same event; do not force one cut per
  sentence.
- Create `planning/narration-beat-maps/<job-id>.json`. Every beat must contain
  the approved narration text, real TTS start/end, event IDs, required
  characters/action/location/time state, and its reviewed clip bindings. Event
  titles or summaries are not substitutes for the spoken narration text.
- Lock the original story plan by SHA-256 in the beat map. From this point,
  visual repair must not change the family, profile, central question, causal
  spine, hook, narration/dialogue text, event IDs or order, or payoff. Repair
  only source in/out points inside already-bound events/scenes, safe cut
  boundaries, subtitle treatment, or affected renders. Unsupported wording is
  a story-stage failure to resolve before this lock, never a reason to rewrite
  a locked job during visual QC.
- Classify reviewed coverage as `exact`, `context`, `neutral`, or
  `contradiction`. Apply the selected Profile's exact-clip, exact-duration,
  average-shot, and under-five-second thresholds. Globally require
  exact-or-context duration at least 90% and zero contradiction or unbound
  factual beats.
- Use the selected Profile's picture-duration floor. Let one continuous clip
  serve adjacent beats in the same continuity group; do not cut merely because
  a new sentence begins. Keep no more than four narration-picture cuts in any
  rolling 30-second window unless the Profile explicitly overrides it.
- Before VSR/STTN, run the deterministic frame-budget preflight below against
  the final mastered narration timings and the materialized B-roll plan. This
  uses no model call and must finish before any expensive subtitle removal:

  `python scripts/validate_motion_coverage.py --job <production/job-id/job.json> --broll <production/job-id/broll-audit.json> --output <production/job-id/qc/motion-coverage-audit.json>`

  `hold_after` defaults to zero. At 25 fps, allow at most three total hold
  frames in one narration block only for rounding; never use cloned final
  frames or `tpad=stop_mode=clone` to compensate for missing drama footage.
  On failure, make one targeted repair by extending or selecting a natural
  range inside the same already-bound event/scene. Recheck once. If it still
  fails, mark that item `visual-coverage-pending` and continue the batch; do
  not rewrite the story, add events, or enter an open-ended render/QC loop.
- After the motion preflight passes, render exactly one 540×960 alignment
  preview before VSR/STTN or final rendering. Inspect the start, middle, and
  end of every beat and store the evidence frames. Route only uncertain
  identity/action matches to additional visual review.
- For jobs produced by the bundled two-minute recap pipeline, run
  `scripts/build_semantic_alignment_map.py` after the preview review to create
  the locked per-job story snapshot and beat map from `job.json`,
  `broll-audit.json`, and the reviewed beat evidence. Do not hand-copy event
  titles into narration fields.
- Run `scripts/validate_semantic_alignment.py <beat-map> --event-ledger
  <event-ledger> --story-plan <locked-story-plan> --output
  <production/job-id/qc/semantic-alignment-audit.json>`. Do not proceed to VSR
  unless it exits successfully.

- Bind each narration block to 1–3 reviewed continuous source clips, normally 5–19 seconds each. A block longer than 27 seconds may use four long clips when the average shot still exceeds roughly seven seconds. Prefer one correct long scene when additional cuts would force mismatched footage.
- Prefer one slightly imperfect but continuous scene over several short, semantically wrong shots.
- Do not cut half a shot, cross a camera motion discontinuity, or create one-frame flashes.
- Source drama shots and dialogue remain 1.0x. Only synthesized narration may use the configured speech speed.
- Within one video, do not reuse the same shot/range or repeat narration.
- Measure synthesized narration before rendering. Select a naturally shorter
  safe range inside the same reviewed event when picture exceeds the block;
  never change locked narration, accelerate source footage, trim through an
  action, or fall back to a word-similarity replacement. Moving-picture
  duration must cover the narration block within three frames, assembled
  picture may differ by at most one frame, and total rounding hold per block
  must remain at or below three frames.
- Merge adjacent ranges that are truly one scene. When separately cleaned ranges
  merely touch, avoid duplicating the shared encoded frame by leaving a one-frame
  boundary or by rebuilding them as one cleaned range.

### 7. Preserve complete source dialogue

- Start at a complete sentence or conversational turn; include reaction context when it changes meaning.
- End after the full sentence and add 0.3–0.5 seconds post-roll when available.
- Never let narration enter over an unfinished source sentence.
- If a fragment is visually valuable but its speech is incomplete, mute that fragment and use it only as narration B-roll.

### 8. Generate final captions

Read [caption-contract.md](references/caption-contract.md).

- Generate captions from the approved narration script and provider/ASR word timings.
- Punctuation and semantic pauses start a new cue; a pause must clear the previous cue.
- Keep protected names and phrases intact; never split a word across cues.
- One line only, normally at most 9 visible characters, zero cue overlap, no inherited previous sentence, no punctuation in the burned narration caption unless explicitly requested.
- Select the global `short-drama-vsr-tight-rail-1080x1920` subtitle profile for
  narration captions. Do not change the selected shot or raise/lower the
  caption merely to dodge source subtitles. The STTN mask map describes only
  source pixels to repair and must never override caption size, baseline, or
  visible-rail geometry.
- Rebuild designed pop-up captions from the new cue IDs after any timing repair.
- If one emphasis phrase spans multiple cues, render one one-line emphasis event per cue. The preceding event must disappear before the next cue appears; never keep the whole phrase as a sticky second line.
- Select each designed emphasis phrase from a different final caption cue.
  Reject nested or duplicate phrases that would schedule two replacement
  animations on one cue.

### 9. Remove source hard subtitles before burning new captions

Read [hard-subtitle-treatment.md](references/hard-subtitle-treatment.md). Treat removal as a shot-planning and encoded-frame QC task, not as deleting a subtitle stream.

- Classify every source as `clean`, `burned`, or `unknown`; `unknown` cannot enter final production.
- Do not weaken narration-to-picture alignment to avoid subtitles. Select the
  best event-bound visual first; subtitle treatment happens after the visual is
  locked.
- Preserve the original composition. For burned-subtitle narration shots, use
  Video Subtitle Remover (YaoFANGUK) with STTN `--inpaint-mode sttn-auto` and a
  reviewed, material-specific subtitle mask. Read
  [vsr-sttn-hard-subtitle.md](references/vsr-sttn-hard-subtitle.md).
- Batch clips by identical subtitle geometry, run STTN once per batch, split
  them back on exact frame boundaries, and bind every cleaned clip path into
  the final EDL. Never silently fall back to crop/zoom or a different shot.
- Add a clearly visible one-line smooth Gaussian/frosted blur rail over the minimum
  vertical repaired subtitle band, then place the new approved-script caption
  on that rail. Let the rail run edge-to-edge horizontally so it does not look
  like a floating card with empty side margins. The blur must be visually
  obvious at delivery resolution; do not substitute a weak blur, coarse pixel
  mosaic, or darkened strip. Do not add a dark or colored tint unless
  explicitly requested. The rail is a residual-remnant
  safeguard, not a substitute for STTN. Do not use a two-line-height or
  lower-third-size rail for one-line text. Fit the visible rail tightly around
  the encoded glyphs and outline; retain only 6–12 px top/bottom safety padding.
- At 1080x1920, lock the short-drama rail to `y=1318`, `height=90`, caption
  baseline `1385`, caption size `64`, and `darkOpacity=0`. Reject legacy 120 px
  or 180 px rails. Do not derive these visual parameters from a mask map.
- Apply removal only to narration B-roll by default. Preserve the original full frame and original hard subtitles for real dialogue, and do not overlay narration captions there.
- Build a clean master first. Burn source notice, approved-script captions, and per-cue emphasis only after source-subtitle treatment is locked.
- Generate an encoded Pilot and inspect the first, middle, and last frame of every narration shot. Require zero readable source subtitles, zero source/generated double-subtitle frames, zero vertical stretch, and no cropped face, action, or key prop.
- Hash the framing plan and Pilot. Any source range, crop, reframe, or geometry change invalidates the Pilot and requires a new audit.

### 10. Render and run hard-gate QC

Read [final-delivery-gates.md](references/final-delivery-gates.md). Run checks on encoded deliverables, not only timelines:

- full decode, format, duration, loudness, peak, tail, black/frozen/flash frames;
- narration-to-event alignment and scene continuity;
- complete dialogue boundaries and narration handoffs;
- no repeated shot/range and no repeated narration inside a video;
- exact caption script round-trip, word-split zero, overlap zero, multiline zero, orphan zero, timing drift within tolerance;
- verify every caption cue is one physical rendered line and no wider than the locked limit; do not infer this only from SRT newlines;
- create encoded contact-sheet triplets immediately before, at, and after representative caption resets across the start, middle, and end of every video; include both audible pauses and immediate replacements;
- require a visible blank frame at real pauses where the word timings contain a gap; for gapless speech, require a clean one-cue replacement with no stale prior text;
- verify narration caption text against word timings and confirm the final spoken sentence and last subtitle complete before the tail;
- inspect the encoded first, middle, and last frame of every narration shot for source hard-subtitle leakage and framing damage;
- batch-level story and footage overlap report.
- run encoded cut-boundary inspection on every block and picture transition;
  calculate cuts from `clip_duration + hold_after`, and require
  `flashCandidates=[]`, `pictureHoldCandidates=[]`, and
  `freezeThenCutCandidates=[]` rather than relying on nominal timeline math;
- require `production/<job-id>/qc/motion-coverage-audit.json` with
  `status=passed`, zero motion-shortfall/timeline-mismatch/hold-budget blocks,
  and `maximumClipHoldFrames<=3` before final delivery validation;
- rerun `scripts/validate_semantic_alignment.py` against the final locked EDL
  and require `status=passed`, `scriptRoundtrip=true`,
  `storyPlanHashMatches=true`, `eventLedgerResolved=true`, the selected
  Profile's picture thresholds, `exactOrContextDurationRatio>=0.90`,
  `contradictionCount=0`, and `unboundBeatCount=0`;
- run `scripts/qc_long_scene_cut_boundaries.py --output-root <batch-root>
  [--production-root <isolated-cache>]` for the encoded cut audit;
- run global hard gates, then only the selected profile's regression checks from
  [narrative-profiles.md](references/narrative-profiles.md);
- allow legacy compatibility only when the complete approved artifact set
  matches [compatibility-baselines.json](references/compatibility-baselines.json)
  by SHA-256; never apply that path to a new or changed render;
- for `P01_dual_time_conflict`, additionally run the validated sample checks in
  [sample-style-story-editing.md](references/sample-style-story-editing.md).

Repair locally and rerun all affected gates. Copy a video into `deliveries` only after every hard gate passes.

Required per-video caption metrics are `scriptRoundtrip=true`, `maximumCharacters<=9`, `wordSplitCount=0`, `protectedTermSplitCount=0`, `overlapCount=0`, `multilineCueCount=0`, and `orphanCount=0`. Required hard-subtitle Pilot metrics are `status=passed`, at least three checked encoded frames per narration shot, `sourceGeneratedOverlapFrames=0`, `verticalStretchFrames=0`, and unchanged plan/Pilot hashes.

### Production-safe implementation details

- Cache TTS by exact narration text, voice, provider, and model. Any script
  change invalidates audio and word-timing artifacts together.
- For source files with burned subtitles, keep narration framing unchanged and
  bind VSR/STTN-cleaned clips plus the residual caption rail. Preserve the
  original full frame and original hard subtitles during real dialogue and
  hooks; never add narration captions to those tracks.
- Shot-graph endpoints may differ from ffprobe by a few hundredths of a second.
  Permit only a terminal clamp of at most 0.12 seconds to the actual decodable
  limit; never relocate the reviewed event range.
- Add duration through narration or complete dialogue, not long silent padding.
  Normal final tail is 0.85–6 seconds and must retain a complete last sentence.
- Derive each job's bound episode list from the hook, every dialogue turn, and
  every manual visual range. A job must be independently resumable; do not rely
  on another batch item incidentally loading a required episode.
- Put bulky render caches on a scratch volume when the delivery volume is
  constrained. Keep final deliveries and indices at the requested destination,
  then remove only reproducible blocks, temp clips, normalized masters, and CK
  intermediates after QC passes.
- Overlay short CK emphasis clips directly at their event timestamps. Do not
  concatenate them into a full-duration lossless transparent track.
- Never reuse cached caption or emphasis assets after cue text, cue timing,
  protected terms, font metrics, maximum width, or hard-subtitle framing changes.
- Leave AAC true-peak headroom: target about -4 dBTP during the final audio-only
  pass so the encoded delivery remains safely below the -1 dBTP hard gate.

## Outputs

Place all work under `<source>/edit/多故事线全量剪辑版/`:

- `corpus/`: transcripts and episode corpus;
- `planning/`: event ledger, candidates, scores, selection rationale, event-bound EDLs;
- `planning/narration-beat-maps/`: approved narration-to-event-to-clip maps with locked story-plan hashes;
- `production/`: narration, captions, intermediate assets, and per-video manifests;
- `qc/`: machine reports, motion-coverage and semantic-alignment audits, the single low-resolution preview evidence set, contact sheets, and repair ledger;
- `deliveries/`: final MP4, SRT, and per-video QC JSON;
- `delivery-index.md` and `delivery-index.json`.
- `qc/narrative-profile-regression-summary.json` and encoded cut/caption-reset contact
  sheets for every delivered item.

File names must state narrative family and source episode range, for example:

`03_亲情关系线_第04集至第11集_母亲为何替女儿隐瞒真相.mp4`

## Non-negotiable failure policy

Do not describe a batch as complete when any planned item is unrendered or any hard gate fails. Report exact passed/failed counts and paths. Never hide a failed candidate by silently deleting it; record rejection or repair status in the index.

Keep the previous delivery until its replacement passes every gate. A successful encode is not a successful delivery. If subtitle removal, caption reset, script timing, dialogue completion, or final-sentence completion cannot be proven from the encoded MP4, mark the item failed and do not publish it.
