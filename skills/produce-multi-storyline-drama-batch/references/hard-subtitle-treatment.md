# Burned source subtitle treatment

## Contract

Burned subtitles are video pixels. Removing a subtitle stream does not remove them. Treat source-subtitle removal, new-caption generation, and encoded-frame verification as three separate stages.

Use this policy by track:

- Narration B-roll: keep the event-matched shot and original composition, remove active source hard subtitles with VSR/STTN, mute source audio, add the residual caption rail, then show approved-script narration captions.
- Real dialogue and source hooks: preserve the original frame, source audio, and source hard subtitles; do not add narration captions.
- No encoded frame may contain two readable subtitle layers.

## Required shot evidence

Record for every narration shot:

`sourceHasHardSubtitles`, `sourceSubtitleActive`, `sourceSubtitleText`, `subtitleEvidenceFrames`, `captionConflictChecked`, `hardSubtitlePolicy`, `crop/reframe geometry`, and `framingPlanSha256`.

Classify masters as `clean`, `burned`, or `unknown`. Do not render `unknown` masters. When subtitles are active, allow only:

- `reframed-outside-frame`: crop or reframe moves the complete subtitle band outside the output;
- `inpainted`: a reviewed pixel repair removes the complete text without visible artifacts;
- `explicit-waiver`: the user explicitly accepts a known visible remnant.

`no-conflict` by itself is not a removal policy.

## Locked strategy order

1. Lock the most semantically accurate event-bound shot. Do not replace it merely because subtitles are active.
2. Determine the minimum subtitle rectangle from representative full-resolution
   frames. For a one-line source subtitle, use a one-line-height bounding box
   with only modest repair padding; never reserve a generic lower third.
3. Process the locked narration shot with YaoFANGUK Video Subtitle Remover in `sttn-auto` mode.
4. Group clips that share subtitle geometry and run STTN in batches; never inpaint the whole frame blindly.
5. Inspect STTN output for readable remnants, smears, duplicated strokes, face/hand damage, and temporal flicker.
6. Add a single-line local strong Gaussian/frosted blur rail over the minimum
   repaired subtitle band and render the new narration caption on top. The
   blur must remain obvious after encoding; do not darken or pixelate it.
7. If STTN damages a critical subject, tighten or split the mask and rerun it. Do not crop the shot or switch to a less accurate visual as the normal fix.

The approved implementation is documented in [vsr-sttn-hard-subtitle.md](vsr-sttn-hard-subtitle.md). Output remains 1080×1920 with SAR 1:1 and the original composition intact.

## Rendering order

1. Apply VSR/STTN with the locked per-material mask to narration shots only.
2. Split the cleaned batches back to exact shot frame ranges.
3. Add the residual mosaic/blur caption rail to narration shots only.
4. Encode normalized shot blocks.
5. Concatenate a clean master with no generated captions.
6. Verify source-subtitle removal and rail geometry on the clean master.
7. Burn the persistent source notice.
8. Burn approved-script captions aligned by provider/ASR word timings on the rail.
9. Overlay one-cue-at-a-time emphasis assets.
10. Encode the final delivery and audit that encoded file.

Do not cover an already burned generated caption with a second caption. Rebuild from the clean master whenever caption text, timing, layout, or styling changes.

## Pilot hard gate

Before full delivery, sample the first, middle, and last encoded frame of every narration shot. Check:

- readable source subtitle count is zero;
- source/generated double-subtitle frame count is zero;
- no subtitle flashes at shot or dialogue boundaries;
- no blur strip, delogo smear, mask damage, vertical stretch, or aspect-ratio error;
- faces, hands, actions, and key props remain in frame;
- dialogue shots retain their intended original subtitles and receive no narration captions;
- the original composition is unchanged; no crop/zoom was used to solve subtitle contamination;
- every narration shot resolves to a real VSR-cleaned file whose source range matches the EDL;
- the residual rail covers the complete repaired subtitle band and the new caption is fully inside its safe text area.

Persist `pilotFramingAudit` with `status`, `checkedNarrationShots`, `checkedEncodedFrames`, `sourceGeneratedOverlapFrames`, `verticalStretchFrames`, `seekMismatchFrames`, evidence paths, Pilot hash, and framing-plan hash. Require at least three checked frames per narration shot. Any geometry or source-range change invalidates the audit.
