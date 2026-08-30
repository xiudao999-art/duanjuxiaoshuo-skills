---
name: remove-hard-subtitles-vsr-blur
description: Remove burned Chinese source subtitles from narration B-roll with YaoFANGUK Video Subtitle Remover using STTN auto inpainting, then add a full-width, tightly fitted, blur-only single-line caption rail for new script-aligned subtitles. Use when short-drama footage has hard subtitles that must be removed without changing the semantically matched shot, cropping, zooming, darkening the image, or covering real-dialogue subtitles.
---

# Remove Hard Subtitles With VSR Blur

Preserve the selected story evidence and original composition. Repair subtitle
pixels only after the narration shot and exact source range are locked.

## Route tracks

- Process narration B-roll only. Mute its source audio during final assembly.
- Preserve hook and real-dialogue video, source audio, and original hard
  subtitles. Add no narration caption to those tracks.
- Never replace a semantically correct shot merely because it contains text.
- Never crop, zoom, stretch, or move the frame to hide subtitles.

## Build a reviewed mask

Copy [mask-map-template.json](assets/mask-map-template.json) into the job. Sample
full-resolution frames from the start, middle, and end of each subtitle layout.

- Fit the STTN rectangle around the complete one-line source glyph band with
  modest repair padding. Keep the vertical range minimal.
- Let the mask and visible rail span the full frame horizontally.
- Split genuinely different vertical layouts into separate groups instead of
  widening one global vertical mask.
- Set `reviewStatus` only after inspection and save `reviewEvidence`.

Read [qc-contract.md](references/qc-contract.md) before approving a mask or
delivery.

## Process a locked clip

Use the bundled script after final shot selection:

```powershell
python scripts/process_vsr_blur_clip.py INPUT.mp4 OUTPUT.mp4 `
  --mask 1275 1415 0 1079 `
  --rail-y 1318 --rail-height 90 --blur-sigma 28
```

The script preserves source dimensions and SAR, calls the project VSR GPU
runtime in `sttn-auto` mode, then overlays a strong smooth Gaussian blur on the
minimum one-line band. It adds no dark, gray, or colored tint.

Use `--already-inpainted` only when the input is a reviewed STTN output. This
mode tests or rebuilds the blur rail without rerunning STTN.

Treat the mask map as an inpainting-geometry file only. Never read visible
caption-rail geometry, caption size, or baseline from a series mask map. Select
the global `short-drama-vsr-tight-rail-1080x1920` subtitle profile instead.
At 1080x1920 its locked visible rail is `y=1318`, `height=90`, with the caption
baseline at `1385`. Reject obsolete `y=1285/height=120` or expanded lower-third
rails instead of silently rendering them.

## GPU scheduling and recovery

- Use one GPU VSR owner at a time. Poll both utilization and memory, and record
  `waiting-for-gpu` in the job heartbeat while another healthy VSR process is
  active. Never launch two STTN models into a 4 GB device.
- For 1080x1920 footage on a 4 GB GPU, use merged batches of at most 700 frames.
  On `CUBLAS_STATUS_ALLOC_FAILED`, zero-frame output, or a frame-count mismatch,
  keep all validated cache hits and retry only the misses at 450 frames, then
  300 frames. Do not rerun completed clips.
- Do not treat a quiet progress bar as a stall. STTN can be silent during a
  50-frame inference block. Require no log growth, negligible CPU delta, and
  GPU utilization below 5% for eight minutes across at least three samples
  before killing only the affected process tree.
- Write a UTF-8 live status file throughout extraction, GPU wait, STTN,
  splitting, rail rebuild, config binding, and render handoff. Validate all
  Chinese paths before launch; continuation logic must receive paths as
  arguments rather than embedding them in a generated PowerShell source file.
- A failed attempt must never delete the persistent content-addressed cache.
  The next attempt starts with a dry-run/cache audit and reports target-key
  hits and misses, not the raw number of files in the cache directory.

## Burn replacement captions

- Burn captions only after VSR and the blur rail are complete.
- Use the approved narration script as text and ASR/provider timings only for
  alignment.
- Render one physical line per cue. Protect names and compounds from splitting.
- Center white heavy text with a black outline on the rail.
- Fit the rail tightly around the encoded glyphs and outline. Retain only
  6–12 px top/bottom safety padding; do not leave empty lower-third space.
- Keep the rail full width and visually obvious at delivery resolution.

## Hard gates

Inspect encoded first, middle, and last frames of every narration shot. Fail
the shot for readable source glyphs, flicker, STTN smears, weak blur, a darkened
band, cropped composition, multiline captions, or captions outside the rail.

Keep the previous delivery until the replacement passes. Record the source
range, mask, rail geometry, VSR mode, output path, and review evidence in the
job manifest.
