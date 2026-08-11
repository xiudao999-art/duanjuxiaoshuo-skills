# VSR/STTN narration subtitle removal

Use this reference whenever narration footage contains burned source subtitles.

## Locked toolchain

- Tool: `D:/codex/短剧剪辑/tools/video-subtitle-remover`
- Runtime: `.venv-gpu/Scripts/python.exe`
- Entry point: `backend/main.py`
- Model/mode: `--inpaint-mode sttn-auto`
- Reusable preprocessor: `../scripts/prepare_vsr_narration_clips.py`

The core invocation is:

```powershell
python backend/main.py -i INPUT -o OUTPUT -c YMIN YMAX XMIN XMAX --inpaint-mode sttn-auto
```

## Contract

1. Lock story evidence and shot boundaries before subtitle processing.
2. Never choose a weaker visual because it has fewer subtitles.
3. Never crop/zoom the narration frame to remove subtitles.
4. Define masks in the normalized full-frame coordinate system.
5. Split different subtitle geometries into separate STTN batches.
6. Preserve hook/dialogue video, audio, and original subtitles unchanged.
7. Apply the residual rail only to narration shots.

## Mask map

Create one JSON file per source series:

```json
{
  "defaultMasks": [[1275, 1415, 0, 1079]],
  "episodes": {
    "3": [[1260, 1425, 0, 1079]]
  },
  "rail": {
    "enabled": true,
    "x": 0,
    "y": 1285,
    "width": 1080,
    "height": 120,
    "blurSigma": 28,
    "darkOpacity": 0.0,
    "captionBaseline": 1385
  }
}
```

Derive coordinates from full-resolution representative frames. Use the minimum
single-line vertical bounding box that includes every glyph edge plus only
about 6–12 pixels of visible rail padding. Horizontal coverage may run edge-to-edge across
the screen; do not leave card-like side margins. Do not default to a
two-line-height mask when the source is one line. Keep the residual rail no
taller than the reviewed one-line safe area. If one series changes subtitle
placement or truly uses two lines, create additional episode/layout groups
instead of widening the vertical mask.

## Run

Run after final event-bound B-roll calibration and before rendering:

```powershell
python .codex/skills/produce-multi-storyline-drama-batch/scripts/prepare_vsr_narration_clips.py `
  configs/job.json --mask-map configs/source-subtitle-masks.json `
  --output-config configs/job-vsr.json `
  --work-root D:/video-work/job-vsr-sttn
```

The script deduplicates final narration ranges, batches identical masks, calls
STTN, splits exact frame ranges, adds the residual rail, and writes
`precleaned_path` into every manual narration visual. Render only the generated
VSR-bound config.

Use `--work-root` on a scratch volume with enough space for raw clips, the
concatenated STTN batch, the repaired batch, and split cleaned clips. Do not
change the owning production root merely to relocate these reproducible files.

## Residual rail design

- Use a clearly visible smooth Gaussian/frosted blur of the same band by
  default (`blurSigma` about 24–32 at 1080×1920). Do not simulate the effect
  with darkness or a coarse pixel mosaic. Do not add a dark, gray, or colored
  tint. A non-zero tint requires explicit user approval.
- Keep the rail inside the subtitle-removal band.
- Put the approved narration caption on the rail with a high-contrast white
  fill and black outline.
- The rail may persist through a narration block. It must never appear on hook
  or real-dialogue blocks.

## Hard gate

Do not infer success from configuration. Inspect encoded first/middle/last
frames for every narration shot at usable resolution. A program may record
`passed` only after reviewed evidence exists. Hard-code neither `status=passed`
nor zero residual counters. Any readable source glyph, temporal smear, or rail
misplacement fails the shot and requires a mask rerun.
