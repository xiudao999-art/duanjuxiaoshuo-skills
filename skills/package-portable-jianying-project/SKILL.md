---
name: package-portable-jianying-project
description: Package, relocate, install, and verify Jianying Pro/CapCut China desktop draft projects with all referenced videos, audio, images, fonts, captions, effects, and editable timeline data. Use when exporting a 剪映工程包, moving a draft to another Windows machine or user account, fixing black/offline media after migration, collecting all project dependencies, or rewriting absolute draft paths.
---

# Package Portable Jianying Project

Create a self-contained Windows package; never treat copying `draft_content.json` alone as migration.

## Portability contract

Require all of the following before calling a package complete:

1. Preserve the whole draft directory and editable tracks.
2. Copy every user-owned media/font dependency into the draft's `Resources` tree.
3. Rewrite the packaged JSON to packaged paths, then rewrite again at install time to the destination user's absolute path.
   Rebind from each dependency's `Resources`-relative suffix; never assume the extraction path equals the build path.
4. Include a one-click installer and a SHA-256 manifest.
5. Validate that every video/audio/font reference exists and is inside the installed project.
6. Decode-check timeline video/audio with `ffprobe`; do not accept path existence alone as proof against black frames.
7. Include the final reference render when available, but do not replace editable tracks with only a flattened render.

Read [references/draft-portability.md](references/draft-portability.md) when diagnosing fonts, black frames, built-in effects, or duplicate filenames.

## Workflow

1. Close Jianying before packaging or installing.
2. Resolve the latest intended draft, not merely the newest folder. Inspect `draft_content.json`, track names, duration, and material counts.
3. Build missing editable timeline media in H.264/yuv420p and AAC when Jianying cannot decode alpha/legacy intermediates.
4. Run:

```powershell
python scripts/package_jianying_project.py --draft "<draft-folder>" --output "<bundle-folder>" --zip
```

5. Inspect `portable-manifest.json` and run the generated `安装到剪映.ps1` on the current machine with `PORTABLE_TEST_NO_PAUSE=1` for a real install test.
6. Open or structurally verify the installed copy. Confirm zero missing paths, zero external user-media paths, bundled fonts, nonempty media streams, and matching duration.
7. Deliver both the ZIP and unpacked bundle. State the tested Jianying version and any built-in cloud effects that may need re-download.

## Rules

- Never overwrite an existing destination draft. Append `_import_yyyyMMdd_HHmmss`.
- Never depend on the old drive letter, username, temp directory, download directory, or Jianying cache for user assets.
- Preserve built-in Jianying effect identifiers; do not copy proprietary application cache blindly.
- Package exact custom font files. Install them per-user during import when allowed, while retaining project-local font paths.
- Use collision-safe packaged names based on SHA-256, not basename alone.
- Keep original source clips as well as timeline-normalized clips when later replacement/retrimming is expected.
- Emit a machine-readable manifest and a human-readable import result.
