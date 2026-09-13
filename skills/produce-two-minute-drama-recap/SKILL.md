---
name: produce-two-minute-drama-recap
description: Plan and produce batches of roughly two-minute vertical short-drama recap videos from a complete series or one 4–8 episode arc. Use when Codex must transcribe a whole drama, derive 10–16 overlapping episode windows with different central story questions, write high-retention Chinese narration, mix complete original dialogue, select globally non-repetitive evidence shots, generate MiniMax narration, build script-aligned punctuation-free captions with CK emphasis effects, preserve source footage and dialogue speed, and deliver quality-controlled MP4 files.
---

# Produce Two-Minute Drama Recap

Build one complete 110–130 second recap or plan a differentiated batch from the full series. Treat episode footage and transcripts as evidence; never invent a plot fact to improve the hook.

## Load the production stack

Read these skills before production:

1. `hyperframes` for video routing.
2. `video-use` for word-safe cuts and dialogue boundaries.
3. `minimax-emotional-narration` for coherent TTS chunks.
4. `script-aligned-subtitles` for script-locked caption text.
5. `build-ck-highlight-captions` for semantic emphasis placement.
6. `remotion-best-practices` only when the project uses Remotion assembly.
7. `index-short-drama-source-content` for the reusable full-series source index.
8. `bind-short-drama-script-to-source-clips` for post-script event/scene/shot retrieval and the locked EDL.

Read [references/narration-method.md](references/narration-method.md) before writing. For a whole-series batch, read [references/whole-series-planning.md](references/whole-series-planning.md) and [references/narrative-lenses.md](references/narrative-lenses.md) before selecting episodes. Read [references/workflow-contract.md](references/workflow-contract.md) before binding media. Read [references/qc-checklist.md](references/qc-checklist.md) before delivery.

Read [references/category-editing-playbook.md](references/category-editing-playbook.md)
after binding a window to `F01`–`F10` and before writing or selecting footage.
Apply only the rules recorded under that family; do not turn a sample-derived
category rule into a global default.

Read [references/category-story-selection.md](references/category-story-selection.md)
before locking the event path. Grade proposed events as causal spine, motive
evidence, category evidence, or decoration/repetition, and apply the required
event slots for the assigned family. Category determines which events belong;
it must not leak taxonomy jargon into spoken narration.

When the user requests 8–10 reusable templates, 50–70 candidate narratives,
taxonomy validation against real episodes, or a capacity estimate, also read
[references/template-validation.md](references/template-validation.md). Keep
candidate hypotheses separate from production-eligible windows.

## Choose the planning mode

- Use `continuous_arc` for one recap drawn from one continuous 4–8 episode arc.
- Use `overlapping_question` for a whole-series batch. Transcribe the full series first, then plan 10–16 windows for a normal 40-episode drama. Permit episode overlap across windows only when the central question, core event path, payoff, narration, and principal footage are materially different.

For `overlapping_question`, start from [assets/series-plan-template.json](assets/series-plan-template.json) and validate the batch before writing individual scripts:

```powershell
python scripts/validate_series_plan.py series-plan.json
```

Do not treat a shifted episode range as a new story. Reject two windows when their core-event overlap exceeds the declared threshold or when one can be summarized with the other window's central question.

## Build the whole-series corpus

Use `index-short-drama-source-content` for this stage. Its validated combined
index replaces ad-hoc per-job transcript searches and remains reusable across
all story windows.

Complete these steps before selecting windows in `overlapping_question` mode:

1. Inventory every episode and extract all spoken dialogue and narration with episode-local timestamps. Preserve verbatim source text and mark uncertain recognition instead of silently rewriting it.
2. Obtain word timings for safe dialogue cuts. Add speaker labels, character aliases, on-screen text, locations, visible actions, important objects, and shot-quality tags.
3. Build an event ledger. Give every event a stable ID, participants, goal, obstacle, action, reaction, consequence, reveal, emotional change, evidence ranges, and dependencies.
4. Build temporal, causal, relationship, reveal, contrast, and motif links between events.
5. Record transcript coverage and unresolved low-confidence regions. Do not declare the corpus complete while an episode is missing.

The full transcript is the factual source; summaries and generated narration are derived views.

## Plan overlapping story windows

For taxonomy expansion, first extract 4–8 story atoms per normal episode and
generate short validation drafts. Apply deterministic factual and duplication
gates before simulated scoring, then expand only shortlisted candidates into
production narration. Never treat the 50–70 hypothesis pool as a guaranteed
delivery count; report the surviving production-eligible count separately.

For a normal 40-episode drama, generate more candidates than needed, score them, then retain 10–16 final windows. Each window must:

1. Cover a coherent 4–8 episode span. It may share episodes with another window.
2. State one unique central question and one visible payoff.
3. Use 6–8 causal units with at least 3 core events that define this window's identity.
4. Apply one primary narrative lens from [references/narrative-lenses.md](references/narrative-lenses.md).
5. Assign one required `storyType` from the six-category production taxonomy and one more specific `narrativeLens`.
6. Explain its novelty relative to the most similar accepted window.
7. Keep core-event overlap with every accepted window at or below `0.40` by default.
8. Reserve ordinary source ranges globally after selection. Permit an iconic callback at most twice and document why its function differs.
9. Map every required category-specific story slot in
   [references/category-story-selection.md](references/category-story-selection.md)
   to a supported event ID before narration expansion.

Rank candidates by hook strength, causal coherence, escalation, visual evidence, payoff, and batch novelty. Quality controls the final count: do not pad a thin drama to 16 windows.

## Lock the story arc

1. Load the approved series window or inventory and transcribe the candidate episodes.
2. Select 4–8 episodes that contain one causal arc. Keep them consecutive unless the approved window documents a necessary causal bridge. Do not combine unrelated subplots to reach the episode count.
3. Write one central question and one visible payoff decision.
4. Create 6–8 escalating story units. Make at least three units change the audience's understanding of a relationship, goal, evidence, identity, or consequence.
5. End after the payoff decision and one new consequence question. Do not postpone the result promised by the hook.
6. Grade every proposed event as `A causal spine`, `B motive evidence`,
   `C category evidence`, or `D decoration_or_repeat`. Keep all required A
   events, enough B events to make choices credible, only relevant C evidence,
   and reject D by default.

Start from [assets/job-template.json](assets/job-template.json). Validate the plan before TTS or editing:

```powershell
python scripts/validate_recap_job.py job.json
```

Stop when validation reports an error. Treat warnings as editorial review items.

When the job belongs to a whole-series plan, set `planningMode=overlapping_question`, bind `seriesPlanWindowId`, `storyType`, `storyTypeLabel`, `narrativeLens`, `narrativeLensLabel`, `eventIds`, `coreEventIds`, and `noveltyRationale`, and copy only facts and evidence approved in that series window.

Make the narrative identity visible in production records and delivery naming. Use this filename form unless the user specifies another convention:

```text
NN《剧名》第X集至第Y集【一级类型·具体镜头】标题.mp4
```

Also copy both type fields into `qc-report.json`. Do not burn a large type label into the picture unless requested; the filename and manifest are the default identification surfaces.

## Write the approved mixed script

Target 500–650 Chinese narration characters, then use actual TTS duration as the final authority. Reserve 18–35 seconds for 2–4 complete original-dialogue clips.

Use this time architecture:

- `00:00–00:07`: visible abnormality or future climax.
- `00:07–00:20`: minimum relationship model.
- `00:20–00:43`: first boundary break and temporary response.
- `00:43–01:05`: escalation into public, family, identity, safety, or livelihood stakes.
- `01:05–01:27`: evidence, identity, or allegiance reversal.
- `01:27–01:45`: visible irreversible choice or counterattack.
- `01:45–02:00`: payoff plus a consequence-based cliffhanger.

Write narration as action → reaction → consequence. Use stable relationship labels until names become necessary. Use a turn word only when new information invalidates an expectation. Preserve dialogue only when it is irreplaceable evidence: a promise, denial, public allegiance, or irreversible decision.

Do not repair a missing event slot with interpretation. If a relationship
change, resource transfer, identity proof, or rescue signal has no supported
source event, reject or relabel the candidate before writing.

Choose one primary category pattern from
[references/category-editing-playbook.md](references/category-editing-playbook.md).
Let that pattern control what may be expanded, where original dialogue may
replace narration, and what visual bridge is required. In F03 and F07, a
complete 5–12 second dialogue island may carry a relationship change or
distress signal. In F01 and F08, prefer concise causal narration and visible
evidence over long conversational texture.

Write the script with locked beats:

```text
★ NARRATION N1
<approved narration paragraph>

☆ DIALOGUE D1 episode=05
<verbatim complete dialogue>
```

Do not rewrite a locked `★` or `☆` beat after approval unless the user changes it.

## Bind narration and evidence

After the script is locked, use `bind-short-drama-script-to-source-clips` to
create reviewed candidates, the narration beat map, and the final EDL. Do not
search the source again inside the renderer.

1. Generate MiniMax narration in coherent paragraph chunks with one runtime voice ID. Never store credentials in the skill or job.
2. Preserve raw TTS responses, trimmed WAVs, and a voice manifest.
3. Obtain word timings from the actual generated audio. Use ASR only for timing; keep the approved script as caption text.
4. Cover narration with 2–4 second semantic shots. Allow 4–6 seconds for decisive reactions or visually complex evidence.
5. Match named people, action, location, and dramatic state. Reject a visually convenient but wrong character.
6. Treat a source range as used after it is selected. Do not reuse the same shot, overlapping range, or trivially shifted copy elsewhere in one recap unless an intentional callback is declared in `broll-audit.json`.
7. Use complete dialogue from the first spoken word through the last spoken word. Preserve 0.30–0.50 seconds after the final word when the next utterance does not begin.
8. Add 30 ms audio fades at every edit boundary. Never overlap narration with original dialogue.
9. Loudness-match every narration and original-dialogue block to the same speech target before concatenation. Measure the two block classes separately; a final whole-program normalization alone is insufficient.
10. Update the batch reuse ledger as soon as a source range or narration claim is locked. Check both exact range overlap and semantic repetition across completed videos.
11. For F03 and F07, do not trust ASR silence when burned-in source subtitles,
    continuing mouth movement, crying, or overlapping music indicate dialogue.
    Review the image, waveform, subtitle text, and question-answer closure
    before deleting the range.

## Assemble and caption

Use vertical `1080×1920` at `25 fps` unless the user specifies another delivery format. For the established mixed-speed style, set narration delivery to `1.25×` while keeping all source drama video, hook audio, and original dialogue at `1.0×`. Do not globally accelerate the master. Retime only narration captions and CK events onto the resulting mixed output timeline.

Burn captions last. Display narration captions without punctuation while preserving the approved punctuation internally. Give ordinary cues a subtle entry pop. Replace, rather than duplicate, ordinary cues at CK events.

Segment Chinese captions by words, not raw character counts. Protect names, titles, relationship labels, and story-specific compounds before generic segmentation. Reconstruct every caption block and require exact round-trip equality with the approved script. Reject any cue boundary that lands inside a protected or segmented word.

Treat two-line layout as a baseline-spacing contract. Set the baseline gap to at least `1.65 × font size`; start around `1.75–1.85 ×` for heavy Chinese fonts with outlines and shadows. For the established `88 px` style, use about `150–160 px`, not `72–118 px`. Apply the same rule to ordinary captions and CK replacements. Extract actual encoded frames containing both ordinary and CK two-line captions; do not approve spacing from configuration values alone.

Place CK emphasis only on exact or high-confidence script phrases. Prefer 4–7 events across two minutes, separated by at least one plain sentence. Select templates by meaning: conflict, evidence, reversal, emotional contrast, decision, or cliffhanger. Skip a low-confidence candidate instead of forcing it onto another cue.

Burn `视频来自《<剧名>》` continuously in the upper-right safe area. Do not add a lower-frame shadow mask.

Make the final block narration and append at least `0.45 s` after its source audio duration at the declared narration speed. After rendering, measure at least `0.35 s` of trailing silence in the final narration block. Rebuild the final block, concatenated master, caption package, and final audio whenever this tail changes. Never infer sentence completeness only from the planned timeline.

## Required artifacts

Keep these in every job:

- `job.json`: episode range, question, payoff, units, dialogue bindings, time budgets, and output policy.
- `approved-script.md`: locked narration and verbatim dialogue beats.
- `narration/`: raw TTS, trimmed WAVs, and a manifest without credentials.
- `captions/`: script-aligned word timing and punctuation-free display SRT.
- `emphasis-plan.json` and `emphasis-audit.json`.
- `broll-audit.json`: each narration beat mapped to source episode ranges.
- `render/`: reusable blocks, clean master, packaged master, and delivery master.
- `qc-report.json`: technical and editorial checks.
- `series-plan.json` and `used-segments-ledger.json` for a whole-series batch.

## Stop conditions

Do not deliver when any condition is true:

- The story spans fewer than 4 or more than 8 episodes, or skips an episode without an explicit causal reason.
- The hook promises a payoff the video does not deliver.
- Twenty continuous seconds pass without a new goal, evidence, relationship change, or consequence.
- A dialogue clip begins or ends mid-sentence.
- Narration overlaps drama dialogue.
- Captions differ from the approved script or display punctuation against the requested style.
- A caption boundary splits a word, protected name, title, relationship label, or story-specific compound.
- A two-line caption uses a baseline gap below `1.65 × font size`, or encoded contact frames show touching outlines, shadows, or glyphs.
- A CK phrase is mapped to unrelated words.
- A named character is visually mismatched.
- The same source shot appears more than once without an audited intentional callback.
- Drama footage or original dialogue is accelerated when the output policy says source playback is `1.0×`.
- Narration and original dialogue differ materially in speech loudness after block mastering.
- The source notice disappears or a lower-frame mask obscures footage.
- The final narration sentence has less than `0.45 s` planned tail or less than `0.35 s` measured trailing silence after rendering.
- Final integrated loudness falls outside approximately `-15.0` to `-13.0 LUFS`, or true peak exceeds `-1 dBTP`.
- A whole-series window duplicates another window's central question, exceeds the approved core-event overlap threshold, or reuses principal footage without an audited exception.
- A candidate-pool count is reported as a production count before the hard
  gates and global difference test in `references/template-validation.md`.
