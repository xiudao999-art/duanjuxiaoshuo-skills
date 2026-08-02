# Caption style specification

## Ordinary caption rail

Use these defaults for a 720×1280 vertical master; scale proportionally for other canvases.

| Property | Default |
|---|---|
| Font | Noto Serif SC variable or another genuine heavy Chinese face |
| Normal size | 42 px |
| Accent size | 60 px |
| Weight | 850 |
| Normal fill | `#FFFFFF` |
| Accent fill | `#FFE440` |
| Edge | dark neutral, approximately 1.15 px before supersampling |
| Shadow | close, soft, low-opacity; never the source of apparent weight |
| Maximum width | 650 px |
| Lines | 1–2 |
| Line gap | 72 px |

Use a 2× or 4× supersampled canvas and downsample with Lanczos.

## `bogouwei_reference` measured profile

Use this profile when the user requests the subtitle language learned from `泊狗位.mp4`. These values were obtained from stable burned-caption frames, color sampling, and glyph-mask fitting on the 720×1280 master.

| Property | Measured / locked value |
|---|---|
| Typeface | `Noto Serif SC VF` (closest installed match) |
| Font size | 59 px |
| Weight | 825 |
| Stable glyph fill height | approximately 52–58 px |
| Baseline | render at y=1021 with Noto Serif SC so the visible fill settles around y=971–1026 |
| Normal fill | `#FFFFFF` |
| Emphasis fill | flat pale lemon `#FEFF9E`; do not use a visible gradient |
| Edge | dark neutral for white; muted brown-olive near `#5F5635` for yellow |
| Shadow | yellow template uses restrained neutral-gray drop near RGB `(34,33,30)`, mask opacity about 105/255, approximately +2 px x / +3 px y; ordinary white captions retain a stronger shadow |
| Horizontal glyph scale | 98.8% after rasterization |
| Optical center | approximately 5 px right of the geometric 360 px center |
| Safe line width | 540–560 px |
| Maximum line length | target 9 full-width Han characters; hard maximum 10 |
| Lines | one line only for this profile |

Do not substitute the legacy saturated yellow `#FFE440`; it is visibly different. Interior-pixel measurement on the stable `泊狗位` frame gives source median RGB `(254,255,158)`. The previous gradient implementation rendered around `(247,240,124)` and is rejected as too dark and too dimensional. Use flat `#FEFF9E` and the measured muted outline.

### Wrapping

- Measure glyph width using the actual font.
- Keep an accent phrase on one line when it fits.
- Avoid a one-character last line.
- Do not begin a line with closing punctuation.
- Prefer breaking at semantic phrase boundaries over equal character counts.

### Emphasis density

- Enlarge yellow text no more than once per 2–3 sentences.
- A normal 3-minute explainer usually needs 6–12 yellow phrases and 2–3 CK quotes.
- Repeated technical nouns are not automatically emphasis.
- If every sentence is yellow, hierarchy has failed.

## CK emotional quote hit

Use only for a strong emotional or viewpoint sentence. The quote may wrap to two lines.

### Main text animation

| Relative time | Scale |
|---:|---:|
| 0.00 s | 5% |
| 0.06 s | 18% |
| 0.12 s | 43% |
| 0.18 s | 76% |
| 0.23 s | 100% |
| 0.28 s | 105.5% |
| 0.36 s | 100% |

Fade readable opacity in over the first 0.10 seconds. Start nearly white, then resolve to gray-gold/yellow between 0.11 and 0.27 seconds. Hold at 100% until the complete spoken thought ends.

### Echo trails

Create four yellow-green copies behind the main text.

- Base opacities: `0.42`, `0.31`, `0.21`, `0.13`.
- Expand mostly horizontally; keep vertical growth close to the main glyph.
- Increase blur on outer copies.
- Use a single rise-and-fall envelope from 0.05 to 0.43 seconds.
- Remove all echoes after approximately 0.43 seconds.

The effect is an optical zoom streak, not a circular glow.

The section above defines the legacy `legacy_zoom_streak` template. For `bogouwei_reference`, use the named templates and timings in [template-catalog.md](template-catalog.md); do not force every phrase through the legacy zoom-streak motion.

## Layout presets

For a 720×1280 vertical video:

### Conventional lower rail

- Circular PIP: about `x=22, y=806, size=218`.
- Two-line caption baseline: choose a bottom baseline around 1110–1160 depending on platform safe area.

### Swapped rail and PIP

- Caption baselines: approximately `875, 950`.
- Circular PIP: about `x=22, y=1040, size=218`.
- Confirm the circle remains fully inside the canvas and preserves its border.

Treat these as starting points. Inspect actual faces, graphics, and logos before locking coordinates.
