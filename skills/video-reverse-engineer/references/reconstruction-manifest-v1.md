# Reconstruction Manifest v1

`reconstruction-manifest.json` is the canonical, engine-neutral description of timing, narrative, audio, composition, camera, performance, and continuity.

## Conventions

- Use finite seconds from source start.
- Use normalized top-left geometry: `x`, `y`, `width`, `height` in `[0,1]`.
- Cover `[0, source.duration]` with ordered, non-overlapping shots; keep beats inside the parent shot.
- Represent unknowns with `null`, empty arrays, or `status: "unknown"`; never invent values.

## Evidence and confidence

Use `{"source":"ffmpeg|scenedetect|opencv|asr|audio-analysis|vlm|human","method":"...","range":{"start":0,"end":1},"confidence":0.8}`. Confidence is epistemic: `0.9+` directly measured; `0.7-0.89` corroborated; `0.5-0.69` plausible; below `0.5` requires review.

Keep `spokenDelivery`, `visibleExpression`, and `inferredNarrativeEmotion` separate. The last is performance direction, not a claim about internal emotion.

Review flags use `{id,severity,scope,code,message,evidence}` with `info`, `warning`, or `error`. Errors prevent a full-reconstruction claim.

## HyperFrames mapping

- Shot range becomes a top-level timed clip hosting a sub-composition.
- Normalized geometry becomes percentage CSS.
- Camera translation, scale, and rotation become GSAP transforms on one camera wrapper.
- Transitions use deterministic finite tweens.
- Photoreal content becomes a labeled media slot; its prompt is secondary metadata.
