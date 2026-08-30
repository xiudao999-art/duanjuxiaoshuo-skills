# Encoded-frame QC contract

## Mask review

1. Extract representative full-resolution frames for every source layout.
2. Locate the actual glyph top and bottom; do not estimate from a scaled UI
   preview.
3. Add only enough STTN padding to include outlines and shadows.
4. Keep horizontal coverage full width when subtitle length varies.
5. Create another mask group when vertical placement changes.

## Visual rail contract

- Locked normalized 1080×1920 short-drama rail: `x=0`, `y=1318`,
  `width=1080`, `height=90`, caption baseline `1385`.
- Default blur: FFmpeg `gblur=sigma=28:steps=3`.
- Use smooth blur only. Do not use a dark overlay, gray tint, gradient shadow,
  opaque rectangle, or coarse pixel blocks.
- Keep a single-line rail tightly fitted to the caption glyphs and outline.
- Reject legacy 120 px/180 px rails. Do not inherit visible-rail geometry from
  the STTN mask map.
- Preserve the source frame dimensions, pixel aspect ratio, and composition.

Scale coordinates proportionally only when the source is the same 9:16
composition at another resolution. Re-review the encoded result after scaling.

## Track contract

| Track | VSR/STTN | Blur rail | New narration caption | Source subtitle |
|---|---:|---:|---:|---:|
| Narration B-roll | Yes | Yes | Yes | Removed |
| Source hook | No | No | No | Preserved |
| Real dialogue | No | No | No | Preserved |

## Delivery checks

Require all of the following on the encoded MP4:

- zero readable source subtitle glyphs on narration shots;
- zero frames containing source and generated subtitles together;
- strong, smooth blur that remains visible after encoding;
- zero artificial darkening or colored tint in the rail;
- one physical caption line with no clipped outline;
- 6–12 px approximate vertical safety space, not a generic lower third;
- no STTN damage to faces, hands, actions, or important props;
- no crop, zoom, stretch, flash frame, or range mismatch;
- hooks and dialogue retain their intended original subtitles.

If STTN leaves text or damages content, tighten or split the repair mask and
rerun. Do not solve the failure by changing to a weaker story shot.
