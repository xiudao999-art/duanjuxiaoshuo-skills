---
name: produce-two-minute-drama-recap
description: Produce roughly two-minute vertical short-drama recap videos spanning one continuous 4–8 episode story arc. Use when Codex must write a high-retention Chinese narration script, mix it with complete original dialogue, select unique semantically aligned drama shots, generate MiniMax narration, build script-aligned punctuation-free captions with CK emphasis effects, keep drama footage and dialogue at original speed while retiming narration, match narration/dialogue loudness, burn a persistent source notice, and deliver a quality-controlled MP4.
---

# Produce Two-Minute Drama Recap

Build one complete 110–130 second recap from a continuous 4–8 episode arc. Treat episode footage and transcripts as evidence; never invent a plot fact to improve the hook.

## Load the production stack

Read these skills before production:

1. `hyperframes` for video routing.
2. `video-use` for word-safe cuts and dialogue boundaries.
3. `minimax-emotional-narration` for coherent TTS chunks.
4. `script-aligned-subtitles` for script-locked caption text.
5. `build-ck-highlight-captions` for semantic emphasis placement.
6. `remotion-best-practices` only when the project uses Remotion assembly.

Read [references/narration-method.md](references/narration-method.md) before writing. Read [references/workflow-contract.md](references/workflow-contract.md) before binding media. Read [references/qc-checklist.md](references/qc-checklist.md) before delivery.

## Lock the story arc

1. Inventory and transcribe the candidate episodes.
2. Select 4–8 consecutive episodes that contain one causal arc. Do not combine unrelated subplots to reach the episode count.
3. Write one central question and one visible payoff decision.
4. Create 6–8 escalating story units. Make at least three units change the audience's understanding of a relationship, goal, evidence, identity, or consequence.
5. End after the payoff decision and one new consequence question. Do not postpone the result promised by the hook.

Start from [assets/job-template.json](assets/job-template.json). Validate the plan before TTS or editing:

```powershell
python scripts/validate_recap_job.py job.json
```

Stop when validation reports an error. Treat warnings as editorial review items.

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

Write the script with locked beats:

```text
★ NARRATION N1
<approved narration paragraph>

☆ DIALOGUE D1 episode=05
<verbatim complete dialogue>
```

Do not rewrite a locked `★` or `☆` beat after approval unless the user changes it.

## Bind narration and evidence

1. Generate MiniMax narration in coherent paragraph chunks with one runtime voice ID. Never store credentials in the skill or job.
2. Preserve raw TTS responses, trimmed WAVs, and a voice manifest.
3. Obtain word timings from the actual generated audio. Use ASR only for timing; keep the approved script as caption text.
4. Cover narration with 2–4 second semantic shots. Allow 4–6 seconds for decisive reactions or visually complex evidence.
5. Match named people, action, location, and dramatic state. Reject a visually convenient but wrong character.
6. Treat a source range as used after it is selected. Do not reuse the same shot, overlapping range, or trivially shifted copy elsewhere in one recap unless an intentional callback is declared in `broll-audit.json`.
7. Use complete dialogue from the first spoken word through the last spoken word. Preserve 0.30–0.50 seconds after the final word when the next utterance does not begin.
8. Add 30 ms audio fades at every edit boundary. Never overlap narration with original dialogue.
9. Loudness-match every narration and original-dialogue block to the same speech target before concatenation. Measure the two block classes separately; a final whole-program normalization alone is insufficient.

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
