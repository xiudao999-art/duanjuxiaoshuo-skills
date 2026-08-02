---
name: script-aligned-subtitles
description: Burn or rebuild video subtitles from an approved script while using ASR/Whisper word timings only for alignment. Use when Chinese or mixed Chinese/English captions must avoid ASR homophone mistakes, preserve exact original copy, keep proper nouns/brand names/song names/BGM terms intact, prevent words from being split across subtitle cues, or re-burn ASS/SRT captions onto Remotion/HyperFrames/ffmpeg videos from a clean base.
---

# Script-Aligned Subtitles

## Core Rule

Treat the approved script as the only source of subtitle text. Use ASR only for timing.

Never trust ASR text for final captions when the user has provided or approved copy. ASR may produce homophones, simplified/traditional drift, wrong product names, or normalized numbers. The caption text must round-trip exactly to the script after whitespace normalization.

## Workflow

1. Start from a clean base video without old burned subtitles. If the latest output already has captions, locate or render a no-caption base first.
2. Extract or locate the exact voiceover audio used in the video.
3. Generate word-level ASR timings from the voiceover. Keep raw words and timestamps, but do not use their text as final caption text.
4. Store the approved script beside the job configuration as `scriptText`.
5. Tokenize `scriptText` with this priority:
   - Longest-match protected terms first.
   - ASCII words such as `BGM`, ids, and app names as one token.
   - Chinese words via `Intl.Segmenter("zh-Hans", { granularity: "word" })` when Node supports it.
   - Punctuation and whitespace as zero-duration text attached to the neighboring token.
6. Expand ASR words into a timing timeline at spoken-character granularity.
7. Map script tokens onto the ASR timeline. The final joined subtitle text must equal `scriptText` after removing whitespace; stop on mismatch.
8. Split timed script tokens into readable cues. Flush near `maxChars`, but never split a token/protected term.
9. Keep left-bound Chinese suffixes with the previous cue even if the cue becomes slightly longer: `的 地 得 了 着 过 里 中 内 外 吗 呢 吧 啊 呀 啦 嘛 么`. Do not treat normal word starters such as `去`, `下次`, `上头`, or `后来` as invalid cue starts.
10. Burn captions last in the ffmpeg filter chain, after all video overlays and motion graphics.
11. Generate QC frames or a contact sheet and inspect readability, old subtitle overlap, and placement.

## Required Invariants

Each generated segment manifest should include:

```json
{
  "source": "script-text+asr-timing",
  "scriptText": "approved original copy",
  "protectedTerms": ["汽水音乐", "BGM"],
  "segments": [
    { "text": "caption text", "audioStart": 0.12, "audioEnd": 1.8 }
  ]
}
```

Validate these conditions before presenting output:

- `source` is `script-text+asr-timing`.
- `segments.map(text).join("")` equals `scriptText` after whitespace normalization.
- Every protected term present in the script appears wholly inside at least one segment.
- No segment starts with a left-bound suffix such as `的`, `了`, or `里`.
- Known bad ASR homophones are absent from segment JSON.
- Final video is still the requested resolution/fps and has an audio stream.

## Protected Terms

Always include project-level protected terms for brands, product names, feature names, song names, app names, and fixed CTA phrases.

For Qishui Music style videos, start with:

```js
[
  "汽水音乐",
  "短视频",
  "BGM",
  "热门 BGM",
  "完整版本",
  "完整听",
  "接着听",
  "左下角下载",
  "收藏夹",
  "抖音音乐收藏",
  "场景歌单",
  "一整首",
  "十五秒"
]
```

Add per-video terms such as song titles, artist names, campaign wording, and phrases that must remain together.

## Validation Script

Use the bundled validator on generated `*.segments.json` files:

```bash
node .codex/skills/script-aligned-subtitles/scripts/validate_segments.mjs outputs/asr-subtitles
```

The script accepts files or directories. A directory is searched recursively for `.segments.json` files.

For final MP4 checks, also run `ffprobe`:

```bash
ffprobe -v error -show_entries format=duration -show_entries stream=codec_type,width,height,r_frame_rate -of json final.mp4
```

## Implementation Notes

When updating an existing project script, preserve its local ASR, ASS styling, and render commands. Patch only the text source, tokenization, splitting, and validation flow unless the user asks for a visual style change.

If a project already has a proven subtitle burner, adapt it to this contract instead of replacing the whole pipeline. In the Qishui project, this pattern lives in `scripts/burn-asr-aligned-openflick-subtitles.mjs`.
