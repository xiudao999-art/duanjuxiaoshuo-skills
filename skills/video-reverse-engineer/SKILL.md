---
name: video-reverse-engineer
description: Reverse-engineer an existing video into a reconstruction-ready narrative, word-timed audio plan, shot/beat graph, observable expression and camera-motion evidence, normalized composition data, review flags, and a runnable HyperFrames HTML/GSAP skeleton. Use when Codex must deconstruct MP4/MOV/WebM footage, explain how an edit works, create structured data for recreating a reference video, or translate an existing video's timing and visual grammar into code-first reconstruction instructions.
---

# Video Reverse Engineer

Turn a finished video into an evidence-backed reconstruction package. Prefer executable geometry, timing, tracks, and motion over prose or image prompts. Treat inferred emotion as direction, never as a claim about a person's internal state.

## Installation gate

Do not vendor companion skills into this skill folder. Before enabling this
skill, install every required sibling skill listed in
`references/dependencies.json`, provision the Python and Node runtimes, then
run:

```powershell
python .\.codex\skills\video-reverse-engineer\scripts\check_dependencies.py
```

Stop and report the missing items when the preflight exits non-zero. Install
conditional skills only when the requested workflow activates their condition.

## Required companion skills

Read and apply these skills when available, in this order:

1. `video-use` for word-level transcript acquisition and audio-first timing.
2. `continuous-story-video` for boundary type, action causality, and continuity.
3. `minimax-emotional-narration` for event-based narration emotion.
4. `script-aligned-subtitles` only when an approved script exists.
5. `hyperframes`, `hyperframes-core`, `hyperframes-creative`, `hyperframes-animation`, and `hyperframes-cli` before changing or validating generated HyperFrames code.
6. Qishui-specific skills only for Qishui ads. Use `seedance-video-director` only when generated photoreal media is requested.

Do not replace frame-level boundary detection with a VLM summary. Use a VLM to interpret and reconcile evidence, not to establish exact fast-cut timestamps.

## Workflow

### 1. Acquire deterministic evidence

Run `ffprobe` and obtain a word-level transcript. Prefer the cached `video-use` transcript; pass it with `--transcript-json`. When no transcript is available, still produce the package and add a blocking review flag rather than inventing words.

```powershell
& .\.codex\skills\video-reverse-engineer\scripts\run-analysis.ps1 input.mp4 --mode deep --target hyperframes `
  --language zh --transcript-json transcript.json `
  --approved-script script.txt --out analysis/video-name
```

The project-local wrapper uses the `video-use` Python 3.11 environment, resolves
FFmpeg/FFprobe from a compatible project harness or `PATH`, and automatically caches TransNetV2 JSON
for `--mode deep` when `--transnet-json` is not supplied.

The script fuses PySceneDetect, FFmpeg scene/fade detection, and optional TransNetV2 JSON. It automatically prefers the project's full `ffmpeg-static`/`ffprobe-static` binaries over reduced Remotion builds. It uses OpenCV optical flow when installed and emits a review flag when camera motion cannot be measured. Omit `--approved-script` when no canonical copy exists. Add `--export-audio` when the reconstruction package should retain a mono 16 kHz WAV. Temporary frames are not part of the deliverable.

For long or 4K sources, pass an equal-duration low-resolution cache with
`--visual-proxy`. Frame-level boundary, fade, and camera-motion analysis use the
proxy while source metadata, audio, hashing, preview playback, and the manifest
source path remain bound to the original video. Reject proxies whose duration
differs from the source by more than 0.25 seconds.

When `--approved-script` is present, place one approved sentence per non-empty line in the same order as ASR segments. The analyzer replaces ASR text with approved tokens while retaining segment timing; a line-count mismatch becomes `approved_script_alignment_failed`.

### 2. Add semantic observations

Read `references/semantic-observation-contract.md`. Inspect the complete video first, then each detected shot and ambiguous boundary. Keep `spokenDelivery`, `visibleExpression`, and `inferredNarrativeEmotion` separate. Write `semantic-observations.json`, then rerun with `--semantic-json`. Record disagreements under `reviewFlags`; never silently overwrite deterministic evidence.

### 3. Review and refine

Read `report.md`, `review-flags.json`, and low-confidence shots. Inspect dense frames around ambiguous boundaries and the previous tail/next head for continuity. Update semantic observations, not the derived manifest by hand, then rerun.

### 4. Compile and validate

```powershell
& .\.codex\skills\video-use\.venv\Scripts\python.exe `
  .\.codex\skills\video-reverse-engineer\scripts\validate_manifest.py `
  analysis/video-name/reconstruction-manifest.json
npx --no-install hyperframes lint analysis/video-name/hyperframes
npx --no-install hyperframes validate analysis/video-name/hyperframes
npx --no-install hyperframes inspect analysis/video-name/hyperframes
```

Generated shot compositions express layout and motion. Keep photoreal humans or complex locations as explicit `media-slot` elements with minimal generation constraints.

## Output contract

Always deliver `report.md`, `reconstruction-manifest.json`, `narrative-arc.json`, `transcript.words.json`, `audio-plan.json`, `shot-graph.json`, `review-flags.json`, and `materials-index.json`. The `hyperframes/` directory contains `README-请先看.md`, `preview.html`, `STORYBOARD.md`, the formal `index.html`, and one sub-composition per shot.

The formal `index.html` is a HyperFrames runtime entry, not a normal standalone webpage. Generated projects copy the local GSAP browser runtime into `hyperframes/vendor/`, and must detect direct `file://` opening and redirect to the dependency-free `preview.html` human viewer. The viewer must use the source video directly, provide shot navigation and readable Chinese fields, and must not require extracted still images. Keep the HyperFrames runtime structure unchanged for CLI usage.

Read `references/reconstruction-manifest-v1.md` for field semantics and confidence rules. Validate normalized geometry, complete time coverage, ordered word times, legal transitions, and unique HyperFrames IDs.

Read `references/dependency-map.md` when installing, publishing, debugging a
missing dependency, or deciding whether a companion skill is mandatory,
conditional, or merely transitive.

## Hard rules

- Keep source media untouched and cache immutable analysis.
- Do not include extracted frames, face crops, or contact sheets in the final package.
- Do not cut or align speech inside a word.
- Do not infer private mental state from facial landmarks.
- Preserve algorithm, audio, and model evidence separately with confidence and provenance.
- Use code-first reconstruction. Add prompts only for media slots that cannot be represented structurally.
- Keep the manifest engine-neutral; HyperFrames is a compiler target, not the source of truth.
- Do not claim full reconstruction while unresolved `error` review flags remain.

## Resources

- `scripts/analyze_video.py`: end-to-end analyzer and HyperFrames compiler.
- `scripts/check_dependencies.py`: dependency preflight; never installs or vendors companion skills.
- `scripts/validate_manifest.py`: dependency-free manifest validator.
- `scripts/test_smoke.py`: synthetic-video integration test.
- `scripts/run-analysis.ps1`: project-local runtime and automatic TransNetV2 wrapper.
- `references/reconstruction-manifest-v1.md`: data model and invariants.
- `references/reconstruction-manifest-v1.schema.json`: machine-readable JSON Schema.
- `references/semantic-observation-contract.md`: model interchange format.
- `references/dependency-map.md`: skill/runtime dependency boundaries, install order, and failure ownership.
- `references/dependencies.json`: machine-readable required, conditional, and on-demand dependency declaration.
