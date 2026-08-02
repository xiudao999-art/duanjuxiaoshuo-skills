# Jianying draft portability reference

## Path-bearing locations

- `draft_content.json > materials.videos[].path`
- `draft_content.json > materials.audios[].path`
- JSON-encoded `materials.texts[].content > styles[].font.path`
- `draft_meta_info.json` and backups may contain the original draft folder path.

Jianying desktop drafts normally store absolute Windows paths. A portable ZIP therefore needs an installer that copies the project into the destination draft root and rewrites paths after extraction.

Do not implement installation as only `old package root -> current package root`. The JSON still contains the build machine's absolute package root after ZIP extraction. Resolve each reference by the suffix beginning with `Resources\`; use a collision-checked basename fallback only when the suffix is unavailable.

Keep PowerShell 5 compatible installers ASCII-only, or save them as UTF-8 with BOM. Windows PowerShell may parse UTF-8 without BOM using a legacy code page and corrupt Chinese string delimiters.

## Black-frame prevention

Path existence is insufficient. A file can still decode black because of unsupported alpha, masks, pixel formats, or stale cache. For timeline exchange media prefer H.264 High/Main, `yuv420p`, constant 30 fps, AAC 48 kHz, and `+faststart`. Keep alpha overlays as editable text/graphics when possible; otherwise pre-compose them into an H.264 visual segment.

Check every packaged video with `ffprobe`; require a video stream, positive duration, and nonzero dimensions. Check audio dependencies for an audio stream and positive duration.

## Fonts

Bundle the exact `.otf`/`.ttf` used in the approved render. Point text style font paths to the project-local copy. The installer may also copy fonts to `%LOCALAPPDATA%\Microsoft\Windows\Fonts` and register them under HKCU, avoiding administrator access.

## Built-in effects

Transitions, animations, stickers, and effects represented by Jianying IDs are application dependencies, not user files. Preserve their IDs. On another machine Jianying may download the built-in resource once; this is not an offline-media error.

## Acceptance checks

- `draft_content.json` parses.
- All video/audio/font paths exist.
- All user paths start with the installed project directory.
- No old username, drive root, temp folder, or downloads folder remains in media/font paths.
- Every video/audio file passes `ffprobe` stream checks.
- Timeline duration and material counts match the source draft.
- The exact custom font is present and hashed.
