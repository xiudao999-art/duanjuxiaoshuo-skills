# CK animation and sound template catalog

## Selection rule

First classify the phrase with [selection-method.md](selection-method.md). This catalog only applies after a phrase has qualified as a full L2/L3 CK event. Choose the smallest motion that matches the sentence function. A template name is a semantic decision, not decoration. Hold the stable phrase until its complete spoken thought ends.

## Templates learned from `泊狗位.mp4`

All timings assume 30 fps. At other frame rates preserve seconds, not frame counts.

| Template | Reference beat | Visual contract | Best use | SFX contract |
|---|---|---|---|---|
| `rise_settle` | `基本0成本的设计` around 0.73 s | Whole phrase rises about 58 px from below, opacity 0→1, scale 0.92→1.04→1; readable by ~0.20 s | Opening thesis, a compact result, a number-led hook | Low-confidence source transient; default reference clip is ambience-heavy. Prefer no SFX or a restrained low whoosh in clean productions |
| `char_toss` | `泊狗位` around 6.93 s | Characters enter with 45 ms stagger, varied -28°…-2° rotation, small lateral offsets, scale 0.30→1.08→1; all settled by ~0.30 s | Funny coined term, reveal, punchline | Short tossed/impact accent; onset locked within one frame |
| `stretch_reveal` | `专门来打卡拍照` around 17.17 s | Whole phrase starts horizontally compressed and blurred, scale-x 0.24→1 in ~0.23 s, vertical scale nearly stable | Behavior/result phrase, destination or action | Soft expansion/air transient, onset locked |
| `fade_snap` | `分享发圈` around 18.40 s | Fast opacity and mild scale 0.86→1.035→1; no long trail | Secondary action, quick social behavior | Source has no clean onset-locked transient; sound is optional |
| `light_sweep` | `情感的共鸣` / `和社交的传播` around 38.37–39.47 s | Left-to-right reveal over ~0.36 s with a narrow pale light band at the advancing edge | Emotional insight, cause→effect pair, concluding value | Airy sweep synchronized to the moving light edge; paired lines may use `light_sweep_pair.wav` |
| `type_on` | `低成本的引流` around 46.80 s | Reveal one character every 45–85 ms; each glyph scales 0.72→1.06→1 and becomes stable before the next phrase completes | Final conclusion, accumulating keyword, list/count logic | Repeating light ticks or one compact rising build; first transient onset locked |
| `legacy_zoom_streak` | CK陈凯 V3 reference | 5%→100% in 0.23 s, 105.5% overshoot, four horizontal yellow-green echoes, settle by 0.36 s | Strong standalone quote, emotional judgment | One clean impact/whoosh; do not combine with the `泊狗位` pale sweep sounds by default |

## Density

- Use a full CK template about once per 2–3 sentences at most.
- `char_toss` and `legacy_zoom_streak` are strong punctuation; avoid placing them in consecutive cues.
- A paired `light_sweep` counts as one designed beat when the two phrases form one grammatical conclusion.
- `type_on` is most convincing when the spoken phrase itself accumulates word by word.

## Exact-reference sound assets

The local reference clips and provenance are recorded in `assets/sfx/bogouwei-reference/manifest.json`. `char_toss`, `light_sweep`, and `type_on` have high-confidence visual/onset alignment. `rise_settle` and `fade_snap` do not show a clean isolated transient and must not be described as exact isolated SFX.

## QC checkpoints

- `rise_settle`: 0.07 s, 0.14 s, 0.20 s, 0.30 s.
- `char_toss`: each 45 ms character onset, then 0.18 s and 0.30 s.
- `stretch_reveal`: 0.07 s, 0.15 s, 0.23 s, 0.32 s.
- `fade_snap`: 0.07 s, 0.15 s, 0.22 s.
- `light_sweep`: 25%, 50%, 75%, and 100% reveal.
- `type_on`: every character boundary and final settled frame.
