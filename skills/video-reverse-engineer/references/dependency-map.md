# Dependency Map

## Contents

1. [Layer model](#layer-model)
2. [Skill contracts](#skill-contracts)
3. [Runtime contracts](#runtime-contracts)
4. [Execution flow](#execution-flow)
5. [Install and verification](#install-and-verification)
6. [Failure ownership](#failure-ownership)

## Layer model

`video-reverse-engineer` coordinates evidence collection and compilation. It
does not replace the skills that own transcription, continuity reasoning,
emotional interpretation, approved-copy captions, or HyperFrames correctness.
Companion skills must be installed independently as siblings under
`.codex/skills/`; never copy their folders into `video-reverse-engineer`.

```text
hyperframes (project-level video router; read first)
└─ video-reverse-engineer (analysis coordinator and manifest owner)
   ├─ video-use (word timestamps and audio-first evidence)
   ├─ continuous-story-video (boundary semantics and continuity)
   ├─ minimax-emotional-narration (spoken-delivery interpretation)
   ├─ script-aligned-subtitles (conditional: approved script exists)
   └─ HyperFrames compiler stack
      ├─ hyperframes-core (composition contract)
      ├─ hyperframes-creative (visual and narrative direction)
      ├─ hyperframes-animation (seek-safe motion)
      └─ hyperframes-cli (lint, validate, inspect, preview, render)
```

The reconstruction manifest is the source of truth. HyperFrames is one compiler
target. A VLM may add semantic observations, but it must not replace exact
frame-level boundary detection.

## Skill contracts

| Skill | Status | What this workflow consumes | What it does not imply |
| --- | --- | --- | --- |
| `hyperframes` | Required by project routing | Selects the video workflow and routes domain skills | It does not perform source analysis |
| `video-reverse-engineer` | Required | Owns evidence fusion, manifest, reports, review flags, and the HyperFrames skeleton | It does not invent missing transcript or semantic evidence |
| `video-use` | Required | Cached word-level Scribe JSON and audio-first timing rules | Its editing confirmation gate applies only when editing, not read-only analysis |
| `continuous-story-video` | Required | Boundary classification, causality, continuity anchors, and hidden-cut diagnosis | It does not establish exact fast-cut timestamps |
| `minimax-emotional-narration` | Required for delivery analysis | Keeps spoken delivery, visible expression, and inferred narrative emotion separate | MiniMax synthesis credentials are not required for analysis |
| `script-aligned-subtitles` | Conditional | Approved text remains canonical while ASR supplies timing | Do not invoke when no approved script exists |
| `hyperframes-core` | Required for compiler work | DOM timing, tracks, sub-compositions, determinism, media ownership | It does not choose style or narrative purpose |
| `hyperframes-creative` | Required for compiler work | Composition, typography, palette, beat, and reconstruction-slot direction | It does not override core invariants |
| `hyperframes-animation` | Required for compiler work | One paused, seek-safe GSAP timeline and deterministic motion | It does not own composition structure |
| `hyperframes-cli` | Required for validation | `lint`, `validate`, `inspect`, `preview`, and `render` | A passing lint alone is not visual approval |
| `seedance-video-director` | Conditional | Photoreal media-slot generation when explicitly requested | It is not required for analysis or code-first geometry |
| Qishui skills | Conditional | Qishui-specific routing, gates, assets, captions, packaging, and QC | Generic reverse engineering must not depend on Qishui media or credentials |

The following HyperFrames skills are transitive/on-demand rather than baseline
requirements: `hyperframes-keyframes`, `hyperframes-media`,
`hyperframes-registry`, and `media-use`. Load them only when the generated
reconstruction actually needs advanced keyframes, new audio/media, registry
blocks, or asset resolution.

`remotion` and `manim-video` are available alternative assembly/animation
engines through the wider project, but they are not dependencies of the
default reverse-engineering compiler.

## Runtime contracts

| Runtime | Location or resolution order | Purpose |
| --- | --- | --- |
| Python 3.11 | `.codex/skills/video-use/.venv/` | Analyzer and helper execution |
| `numpy` | `video-use/pyproject.toml` | Numeric evidence processing |
| OpenCV headless | Pulled by the Python environment | Sparse optical flow and affine camera-motion estimates |
| PySceneDetect headless | `scenedetect-headless>=0.7,<0.8` | Adaptive cuts and threshold/fade candidates |
| Torch + TransNetV2 | `transnetv2-pytorch>=1.0.5,<2` | Neural boundary candidates in deep mode |
| FFmpeg / FFprobe | Explicit environment → target project Node runtime → compatible harness → `PATH` | Metadata, scene evidence, fades, and optional audio export |
| Node.js 22+ | System runtime | HyperFrames CLI and Node harness |
| GSAP | `GSAP_RUNTIME` → target project `node_modules` → compatible harness | Vendored seek-safe browser timeline in generated packages |
| HyperFrames CLI | Target project `node_modules/.bin/` or a compatible harness | Static and browser validation, inspection, preview, and rendering |
| ElevenLabs Scribe | `ELEVENLABS_API_KEY` at runtime | Word-level transcript acquisition through `video-use`; optional when transcript JSON is supplied |

Do not commit `.venv`, `node_modules`, `.env`, source media, extracted frames,
transcripts, generated analysis, or model caches.

## Execution flow

1. Probe and hash the immutable source with FFprobe.
2. Load a cached word-level transcript, or record `transcript_missing`.
3. In deep mode, fuse PySceneDetect, FFmpeg, and TransNetV2 boundary evidence.
4. Estimate camera motion with OpenCV optical flow.
5. Merge optional semantic observations without overwriting deterministic data.
6. Build the reconstruction manifest, narrative arc, shot graph, audio plan,
   report, materials index, and review flags.
7. Compile normalized geometry and motion into a HyperFrames project. Copy a
   local GSAP runtime into `hyperframes/vendor/`.
8. Validate the manifest, then run HyperFrames lint, browser validation, and
   layout inspection.

Use `--visual-proxy` only for frame-level visual analysis of long or 4K media.
The source remains authoritative for metadata, hashing, audio, preview playback,
and the manifest path. Reject a proxy with a duration delta greater than 0.25s.

## Install and verification

From the project root:

```powershell
Push-Location .\.codex\skills\video-use
uv sync --python 3.11
Pop-Location

npm install --save-dev gsap hyperframes

& .\tools\verify-video-reverse-engineer.ps1
```

Run an analysis:

```powershell
& .\.codex\skills\video-reverse-engineer\scripts\run-analysis.ps1 `
  input.mp4 --mode deep --target hyperframes `
  --transcript-json transcript.json --out analysis/example
```

## Failure ownership

| Symptom | Owner / next check |
| --- | --- |
| No word timestamps | `video-use`; configure Scribe or pass cached transcript JSON |
| Missing or unstable cuts | VRE detector fusion; inspect PySceneDetect, FFmpeg, and TransNetV2 evidence separately |
| Correct timestamps but wrong boundary meaning | `continuous-story-video` plus semantic observations |
| Approved copy differs from captions | `script-aligned-subtitles`; approved script must remain canonical |
| Camera motion is unknown | OpenCV runtime or low-texture footage; inspect the emitted review flag |
| HyperFrames IDs/timing invalid | `hyperframes-core` and manifest validator |
| Motion is non-seekable or nondeterministic | `hyperframes-animation` |
| Browser console or layout failure | `hyperframes-cli` validation/inspection |
| Missing generated human/location media | Conditional media-slot generation; do not fake it with HTML |
