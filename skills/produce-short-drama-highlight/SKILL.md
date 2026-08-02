---
name: produce-short-drama-highlight
description: Produce narration-led vertical short-drama highlight videos from an approved Markdown article and episode MP4s. Use when Codex must interleave MiniMax narration with complete original drama dialogue, align narration captions to the approved script, select semantically matching 2–4 second background shots, assemble with Remotion or HyperFrames, burn a persistent source notice, and QC every cut before delivering one MP4 at a time.
---

# Produce Short-Drama Highlight

Build one highlight at a time. Treat the approved article as editorial truth and the episode MP4s as evidence.

## Load the production stack

Read these installed skills before production:

1. `hyperframes` for video routing.
2. `video-use` for dialogue-safe cutting and waveform QC.
3. `remotion-best-practices` when using the reusable React composition.
4. `minimax-emotional-narration` for MiniMax chunking and voice continuity.
5. `script-aligned-subtitles` for narration captions.

Read [references/workflow-contract.md](references/workflow-contract.md) before creating or modifying a job. Read [references/qc-checklist.md](references/qc-checklist.md) before rendering the delivery master.

## Parse the approved article

Run:

```powershell
python scripts/parse_highlight_script.py --input <highlights.md> --output <batch.json>
```

Select exactly one `index` from the generated batch. Never rewrite a `★` narration beat or a `☆` dialogue beat unless the user changes the article.

## Produce one job

1. Create `<source-root>/edit/highlight_XX/`; keep source episodes untouched.
2. Bind only the episodes named by the selected article section.
3. Resolve every dialogue beat against the episode-specific timed transcript. Inspect the source waveform and frames before locking boundaries.
4. Cut dialogue from a complete sentence opening through a complete sentence ending. Add click-prevention fades of 30 ms and preserve 0.30–0.50 seconds after the final spoken word when the next line does not begin.
5. Generate narration from complete coherent `★` blocks with the runtime-provided MiniMax voice. Preserve raw TTS and a trimmed WAV. Do not persist credentials.
6. Rebuild word timing for the actual generated narration. Use ASR only as timing; use the approved `★` text as caption text.
7. Cover narration with 2–4 second semantic shots from the bound episodes. Match named people, action, location, and emotional state. Do not show a wrong character merely because the shot is visually convenient.
8. Assemble narration and original dialogue without overlap. Keep dialogue audio untouched except for boundary fades. Keep narration blocks at least one second longer than their audio when a visual tail helps the transition.
9. Burn captions last. Burn the source notice continuously in the upper-right safe area.
10. Render, inspect, repair, and deliver the MP4 before starting the next index.

## Required artifacts

Keep these in each job folder:

- `job.json`: approved beats, source bindings, locked dialogue ranges, montage ranges, and timeline.
- `narration/`: raw MiniMax responses, trimmed WAVs, and a manifest containing the voice ID but no key.
- `captions/*.segments.json`: script text plus ASR timing.
- `remotion/` or `hyperframes/`: renderable composition.
- `qc/`: cut-boundary timeline images, contact sheet, measurements, and report.
- `project.md`: decisions and any deviation from this contract.

Deliver as `片段XX_<标题>_新音色完整对白来源标识版.mp4` unless the user specifies another naming convention.

## Stop conditions

Do not deliver when any dialogue is cut mid-sentence, narration overlaps drama speech, captions differ from approved text, a named character is visually mismatched, the source notice disappears, the lower frame is obscured by an added mask, or final true peak exceeds -1 dBTP.

