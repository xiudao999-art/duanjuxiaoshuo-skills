# Integration and quality control

## Timing contract

If narration is delivered at speed `s`, transform every approved SRT boundary as:

```text
output_start = source_start / s
output_end   = source_end / s
```

Do not change B-roll playback speed merely because narration was accelerated. Trim excess B-roll or choose a different source range.

## Layer order

Use this visual order:

1. Talking-head or edited base.
2. B-roll, chapter cards, dashboards, and PIP framing.
3. Ordinary transparent caption layer.
4. CK highlight replacement clips.

Suppress ordinary subtitle cues covered by a CK quote. Otherwise duplicate wording appears on screen.

## FFmpeg assembly pattern

For each short CK clip, offset its timestamps before overlaying:

```text
[highlight:v]setpts=PTS-STARTPTS+START/TB[h];
[captioned][h]overlay=enable='between(t,START,END)':eof_action=pass[outv]
```

Use QuickTime Animation (`qtrle`, `argb`) for deterministic transparent MOV layers. Use ProRes 4444 only when the downstream editor requires it.

### SFX binding

Every resolved highlight may include `sfx_file`, `sfx_offset`, and `sfx_gain_db`. Delay the SFX to `highlight.start + sfx_offset`, apply gain, and mix it with the program track. Keep the transient within one 30 fps frame (33.3 ms) of the first meaningful visual movement unless the template catalog specifies a deliberate lead.

Reference-derived sounds live under `assets/sfx/bogouwei-reference/`. They were separated from a user-supplied mono mix and can contain faint music or speech leakage. Use them for exact local reconstruction and A/B validation; use clean licensed equivalents for distributable template packs.

## Coordinate checks

- Measure PIP bounds, including border and shadow.
- Keep caption glyph bounds outside the PIP, not just the text baseline.
- On graphic frames, check collisions with baked-in labels and charts.
- Reserve approximately 72–110 px of bottom safety on a 1080-high master and scale proportionally.
- A coordinate change to captions may require moving the PIP or changing line breaks.

## Required QC frames

For every CK quote, inspect:

- `start + 0.10s`: first readable frame.
- `start + 0.23s`: normal scale reached.
- `start + 0.28s`: 105.5% overshoot.
- `start + 0.36s`: settled frame.
- `start + 0.60s`: clean steady hold.

Also inspect:

- One ordinary one-line caption.
- One ordinary two-line caption.
- Every distinct PIP/layout mode.
- A dense graphic or dashboard frame.
- The final caption and final video frame.

Reject the render if text is clipped, covered, duplicated, stale after the spoken sentence, too close to the edge, or visually heavier than the speaker.

For exact-reference requests, render a two-up test video: original event on the left, PNG-generated reconstruction on the right. Use a still sampled immediately before the original caption event as the rebuilt background so subtitle motion can be judged without unrelated camera motion. Report typography/motion/SFX deviations separately; bit-identical video pixels are not a meaningful requirement after source HEVC compression.
