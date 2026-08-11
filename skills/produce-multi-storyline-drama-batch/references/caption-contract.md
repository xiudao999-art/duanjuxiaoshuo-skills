# Final caption contract

1. Approved narration text is canonical; ASR supplies timing only.
2. Split first on punctuation and semantic pauses, then on word tokens.
3. Keep names, idioms, fixed phrases, and grammar-bound tokens intact.
4. Each cue is one physical rendered line, normally 4–9 visible Chinese characters. A protected term may exceed the limit only with an explicit layout exception and an encoded-frame proof that it remains one line.
5. Cue end must be no later than the next cue start; use zero overlap.
6. A sentence or audible pause starts a fresh cue and clears the prior cue.
7. Never append a new sentence below the previous sentence.
8. Burn narration captions without punctuation unless the user requests punctuation.
9. Preserve enough vertical separation from original hard subtitles.
10. After repair, regenerate all pop-up/highlight assets from the repaired cue IDs.
11. If a highlight phrase spans several cues, split it into one highlight event per cue. Never let a phrase persist as a second line beneath the next cue.
12. Do not move characters between cues without moving their word timing boundaries. Repair text and timing as one atomic change.
13. Invalidate cached caption layers when script text, word timings, protected terms, font, font size, tracking, maximum width, baseline, or cue IDs change.
14. Use `short-drama-vsr-tight-rail-1080x1920`: 64 px one-line captions,
    baseline 1385, on the 90 px blur-only rail at y=1318. Do not inherit the
    88 px talking-head style or rail geometry from a mask map.

Required metrics: `scriptRoundtrip=true`, `maximumCharacters<=9`, `wordSplitCount=0`, `protectedTermSplitCount=0`, `overlapCount=0`, `multilineCueCount=0`, `orphanCount=0`. Inspect encoded reset contact sheets across the start, middle, and end of every video. Include both real pauses and immediate cue replacements. At a real pause the middle frame must be blank; at a gapless replacement it may show the new cue but never the previous and new cues together.
