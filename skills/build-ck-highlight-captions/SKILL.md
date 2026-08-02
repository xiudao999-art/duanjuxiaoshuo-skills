---
name: build-ck-highlight-captions
description: Build, burn, and quality-control designed Chinese caption layers for talking-head, tutorial, documentary, and evidence-led videos. Use when deciding where CK emphasis belongs, creating a reusable L0/L1/L2/L3 emphasis plan for a new video, adding flat heavy Song/Ming pure-white subtitles, pale-yellow emphasis phrases, selectable CK-style pop/reveal/type-on templates with synchronized SFX, speed-adjusted SRT timing, or captions that must avoid a presenter PIP. Produces compiled accent/highlight plans, transparent MOV layers, SFX bindings, and auditable timing decisions for FFmpeg or HyperFrames assembly.
---

# Build CK Highlight Captions

Create readable Chinese captions with three controlled emphasis levels: ordinary white text, stable inline yellow accents, and a small number of designed CK-style events. Preserve the approved words; use ASR only for timing.

## Required inputs

- Source video or final narration duration.
- Approved UTF-8 SRT.
- Delivery speed. Use `1.0` unless the edited narration was retimed; output time is `source_time / speed`.
- Optional yellow accent plan and CK highlight plan.
- Current PIP bounds and caption-safe area.

Read [references/reusable-emphasis-system.md](references/reusable-emphasis-system.md) first for the cross-video contract. Read [references/selection-method.md](references/selection-method.md) before deciding whether a phrase stays white, becomes inline yellow, or becomes a full CK event. Read [references/style-spec.md](references/style-spec.md) before changing typography. Read [references/template-catalog.md](references/template-catalog.md) before assigning an animation or sound. Read [references/integration.md](references/integration.md) before compositing, retiming, or moving captions around a PIP.

## Workflow

1. Confirm the narration text and timing source. Do not silently rewrite, merge, or omit approved wording.
2. Inspect the whole script before choosing emphasis. Apply the score, veto rules, and density controls in `references/selection-method.md`. Author one `emphasis-plan.json`; do not maintain accent and CK decisions independently. Select one yellow phrase per 2–3 sentences at most. Select no more than three CK events in a roughly three-minute video unless the format or user explicitly justifies a denser treatment.
3. Prefer phrases carrying contrast, risk, opportunity, judgment, numbers, or the conclusion. Do not highlight filler, chapter labels, or every occurrence of `AI`.
4. Verify emphasis against the speaker's delivery when audio is available. Semantic importance wins; acoustic stress is supporting evidence.
5. Define layout coordinates. Keep normal captions and CK quotes out of the PIP, faces, logos, and baked-in UI text. If the user swaps captions and PIP, move both as one coordinated layout change.
6. Record `level`, `score`, `semantic_role`, and `reason`, then assign each L2/L3 phrase one named template and its matching SFX. Choose from meaning, delivery, and scene; do not rotate templates merely for novelty.
7. Copy `assets/emphasis-plan-template.json`, record all L1/L2/L3 decisions, and run `scripts/compile_emphasis_plan.py`. Fix validation errors before running `scripts/build_caption_assets.py` with the compiled plans.
8. Composite B-roll and graphics first, normal captions next, and CK highlight clips last. Mix the bound SFX at the same resolved onset. Never allow a normal caption and its replacement CK quote to display simultaneously. When an independently validated ASS file owns the ordinary caption rail, pass `--skip-normal-layer`; this avoids a redundant long transparent MOV while still producing CK clips, timing/SFX bindings, and the overlay manifest.
9. Extract QC frames at template-specific checkpoints, representative PIP shots, and the last caption. Compare against the reference when exact matching is requested.

## Burn-in contract

For a 720-wide Chinese vertical video using the learned flat CK look, pass `--style-profile bogouwei_reference`. This locks the family, weight, horizontal glyph scale, optical center, flat colors, outline, and separate yellow-shadow treatment. Explicit `--normal-size`, `--accent-size`, `--highlight-size`, `--max-width`, and baseline arguments remain authoritative so the same typography can be scaled into a conference rail or another safe box.

For the illustrated-audiobook `深宅小福星` 1080×1920 contract, pass `--style-profile shenzhai_recap_1080`. This is a fixed profile: 25fps, weight 825, 88px normal/accent/highlight text, ScaleX 98.8%, optical center x=545, baseline y=1720, true two-line baselines 1566/1720, 154px gap, and 860px raster width budget. Do not use `bogouwei_reference`'s 720-wide defaults for this delivery.

Before burning:

- Rechunk approved text to one line, preferably 9 and never more than 10 full-width Han characters per cue for the reference-size treatment.
- Use flat `#FEFF9E` for yellow. Do not add a visible gradient, gold shading, extrusion, glow, or a heavy shared subtitle shadow.
- Keep stable yellow text the same size as normal text unless the user explicitly requests another hierarchy; motion supplies the emphasis.
- Build the caption layer from the approved script, composite it after the final picture master, and encode only once after overlay.
- Suppress ordinary cues replaced by CK events and mix each selected SFX on the same resolved clock.

After burning, inspect a stable yellow frame and record its fill bounding box and eroded interior median color. For the 720×1280 reference, the target is `#FEFF9E`, 59 px, weight 825, horizontal scale 98.8%, optical center +5 px, and baseline y=1021. Reject visible gradient, brown/yellow drift, an embossed bottom bar, clipping, duplicate text, or a line longer than the locked cue policy. Read [references/style-spec.md](references/style-spec.md) for exact tokens and [references/template-catalog.md](references/template-catalog.md) for motion/SFX selection.

## Plan formats

Use `emphasis-plan.json` as the maintained source. The following accent and highlight structures are compiler outputs retained here for renderer compatibility.

Accent plan:

```json
{
  "accents": {
    "5": ["AI 替代"],
    "22": ["普通人的机会"]
  }
}
```

CK highlight plan:

```json
{
  "highlights": [
    {
      "id": "ordinary-person-opportunity",
      "cue_ids": [21, 22],
      "lines": ["这些大厂懒得碰的领域", "恰恰是普通人的机会"],
      "emotion": "反转 / 希望",
      "template": "light_sweep",
      "sfx": "auto",
      "sfx_offset": 0.0,
      "sfx_gain_db": -2.0
    }
  ]
}
```

Run:

```powershell
python scripts/compile_emphasis_plan.py `
  --plan D:\path\emphasis-plan.json `
  --out-dir D:\path\captions\plans

python scripts/build_caption_assets.py `
  --srt D:\path\master.srt `
  --out-dir D:\path\captions `
  --speed 1.1 `
  --skip-normal-layer `
  --duration 189.8 `
  --accent-plan D:\path\captions\plans\accent-plan.json `
  --highlight-plan D:\path\captions\plans\highlight-plan.json `
  --font C:\Windows\Fonts\NotoSerifSC-VF.ttf `
  --style-profile bogouwei_reference `
  --normal-size 48 `
  --accent-size 48 `
  --highlight-size 48 `
  --normal-baseline 950 `
  --highlight-baselines 875,950
```

The script writes:

- `plans/accent-plan.json`: compiled L1 cue/phrase map.
- `plans/highlight-plan.json`: compiled L2/L3 motion and SFX decisions.
- `plans/emphasis-audit.json`: retained scoring, semantic roles, reasons, and policy.
- `caption-layer.mov`: transparent ordinary subtitle rail, omitted when `--skip-normal-layer` declares that a locked ASS file owns normal captions.
- `highlights/*.mov`: one transparent CK animation per quote.
- `caption-plan.json`: transformed cue timings and accent decisions.
- `highlight-plan-resolved.json`: transformed quote timings and layer paths.
- `overlay-inputs.json`: assembly manifest, including resolved SFX paths and offsets.

## Non-negotiable checks

- Maintain one `emphasis-plan.json` as the decision source; compiled plans are render inputs, not independent editorial truth.
- Record `level`, `score`, `semantic_role`, `reason`, `onset_anchor`, `hold_until`, baseline policy, template, and SFX decision for every emphasized phrase.
- Use actual heavy glyph weight; do not fake bold text with oversized shadows.
- Keep ordinary text pure white and accents bright yellow.
- Use at most two lines and apply pixel-width, phrase-safe, orphan-safe wrapping.
- Hold each caption or quote until the spoken thought finishes.
- Treat a CK quote as a replacement for its underlying subtitle cues.
- Render captions after all normal visuals so footage cannot cover them.
- Preserve deterministic timing; do not use random motion or wall-clock animation.
- Align the first meaningful motion and effective SFX onset to the selected word/stress anchor within one frame unless a documented sweep/payoff offset is intentional.
- Do not use a visual CK hit without either its selected SFX or an explicit `"sfx": "none"` decision.
- Reference-derived SFX are local-use evidence assets. Do not redistribute them.
- Keep a final audit manifest with speed, font, coordinates, selected accents, and highlight timings.
