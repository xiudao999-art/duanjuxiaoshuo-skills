---
name: build-eye-catching-video-cover
description: Select and build high-click video cover images from local MP4/MOV footage. Use when Codex needs to propose several thumbnail frames, map a selected frame back from a sped-up or edited output to a clean source, remove burned captions by re-extracting the original frame, add an exact main title plus a transcript-supported subtitle, preserve faces/hands/logos, and deliver a polished 9:16 cover or social-video thumbnail with visual QC.
---

# Build an eye-catching video cover

Create a separate cover image from a real video frame. Preserve the story and identity of the source while improving thumbnail readability and click appeal.

## Non-negotiable rules

- Prefer a clean original video over a subtitle-burned final. Never inpaint old captions when the clean source exists.
- Treat the selected video frame as the identity source. Preserve faces, hands, body proportions, logos, products, and meaningful screen content.
- Use only claims supported by the transcript or visible video content. Do not invent stakes, results, affiliations, or quotes.
- Keep every user-supplied title string verbatim.
- Deliver the cover as a separate PNG/JPG. Do not alter the MP4, insert a first frame, or attach platform artwork unless the user explicitly asks.
- Show candidate frames and wait for the user's choice when the user asks to choose first. Do not silently apply one.

## Workflow

### 1. Establish the clean-source timeline

Locate:

1. clean original footage;
2. current captioned/final video;
3. transcript or approved script;
4. speed factor and EDL, if the output was retimed or recut.

For a uniformly sped-up video:

```text
source_time = output_time × speed_factor
```

For a recut video, map through the EDL instead of multiplying globally.

### 2. Propose candidates

Extract 5–8 representative frames from semantic and visual peaks. Include different cover angles when available:

- recognizable person plus brand;
- confrontation or comparison;
- iconic topic visual;
- strong number or result;
- clean portrait with negative space.

Score candidates with [references/cover-design-rubric.md](references/cover-design-rubric.md). Reject blink frames, transition frames, motion blur, obstructed faces, weak lighting, and cluttered text.

Save explicit filenames, render the candidates inline, recommend an order, and wait for selection when required.

### 3. Extract the selected clean frame

Use `scripts/cover_frame.py` so output-time mapping stays reproducible:

```bash
python scripts/cover_frame.py extract \
  --input clean-source.mp4 \
  --output-time 7.0 \
  --speed 1.1 \
  --out cover/selected-clean-frame.png
```

Use `--source-time` instead of `--output-time` when the exact source time is already known.

Inspect the extracted frame before editing.

### 4. Write the cover copy

Use two text levels unless the user asks otherwise:

- main title: recurring column, theme, or strongest short hook;
- subtitle: one content-specific claim that explains why this episode matters.

Derive the subtitle from the approved transcript. Prefer `named subject + action + technology/result`. Keep it concise enough for one line when possible. See the subtitle rules and examples in the rubric.

### 5. Build the cover

Read and apply the installed `/imagegen` skill. Load the clean local frame with `view_image`, then use built-in image editing.

In the edit prompt:

- label the frame as the edit target;
- list identity and layout invariants explicitly;
- quote the main title and subtitle verbatim;
- reserve text for real negative space;
- require exactly the requested text blocks;
- forbid old subtitles, translations, extra labels, extra logos, and watermarks;
- match the source palette rather than imposing an unrelated look.

Use the production prompt template in [references/cover-design-rubric.md](references/cover-design-rubric.md).

If generated Chinese text is wrong, retry once with only that correction. If it remains wrong, keep the approved visual treatment and typeset the exact copy with a deterministic compositor; do not deliver misspelled copy.

### 6. Standardize the delivery image

For a vertical social cover, default to `1440×2560` unless the user requests another size:

```bash
python scripts/cover_frame.py finalize \
  --input generated-cover.png \
  --out final-cover.png \
  --width 1440 \
  --height 2560
```

The script uses a cover-scale plus centered crop and validates final dimensions.

### 7. Run visual QC

Inspect the final image at full size and as a small thumbnail. Require:

- exact main title and subtitle;
- no old caption, unwanted translation, extra label, watermark, or fake logo;
- faces, hands, body proportions, product geometry, and existing logos remain plausible;
- title does not cover a face, key gesture, or logo;
- sufficient contrast and mobile-thumbnail readability;
- correct aspect ratio and requested pixel size;
- final file saved inside the user's project.

Do not deliver a cover that fails any of these checks.

## Handoff

Report:

- final cover link and dimensions;
- exact main title and subtitle;
- whether built-in image editing or deterministic fallback was used;
- that the video itself was not changed, unless it actually was.
