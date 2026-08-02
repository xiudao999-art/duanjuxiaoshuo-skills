# Semantic content QC

## Decision order

1. Determine whether a repeated passage is an edit accident or original speech.
2. Determine whether the later passage adds evidence, mechanism, example, contrast, or conclusion.
3. Remove only the minimum range that eliminates redundancy while leaving complete speech on both sides.
4. Prefer clarity over an arbitrary target duration.

## Finding classes

### Duplicate edit

The same source interval, sentence, or phoneme appears twice because EDL ranges overlap or a clip was inserted twice. Remove the duplicated interval and inspect both joins.

### Exact verbal repetition

The speaker immediately repeats the same word or phrase while searching for wording. Examples include repeated names, “数据工具……数据工具”, and restarted clause openings. Remove the false start when a clean restart follows.

### Same-meaning repetition

Two complete statements assert the same idea without adding information. Keep the clearer, more specific, or better-delivered statement. Preserve a later concise conclusion when it supplies a strong ending; otherwise prefer the first definition.

### Necessary progression

Keep these even when keywords recur:

- definition → mechanism;
- claim → evidence or example;
- problem → consequence → solution;
- general category → numbered list;
- thesis → concise final takeaway;
- contrast between two time periods or methods.

### Filler and false starts

Suppress “呃、嗯、啊、那个、就是说” in captions. Cut from audio only when a clean word boundary and natural cadence remain. Do not create many micro-cuts merely to remove every filler.

### Incomplete or orphaned speech

Remove stage directions, “待会再解释”, abandoned comparisons, and clauses whose referent exists only in deleted material. After a cut, remove subtitle residue from the discarded clause even when an old cue overlaps the kept range.

### Off-topic and private material

Remove irrelevant greetings, scheduling details, private references, named-person asides, or venue logistics when they do not support the short video's thesis. Preserve names and context required for attribution or evidence.

### Wrong words

Use context, the speaker's domain, slides, glossary, and parallel occurrences. Separate:

- audio is correct, ASR is wrong: correct subtitle;
- speaker self-corrects: keep the final intended wording and optionally cut the false start;
- speaker appears to misspeak: do not rewrite meaning silently; flag or preserve unless the approved script resolves it;
- proper noun or technical term: require evidence and protect it from cue splitting.

## Severity

- **Blocker:** duplicate clip, wrong meaning, clipped word, corrupted media, missing audio, empty tail.
- **Major:** repeated definition, incomplete sentence, severe pause, protected term split, off-topic aside that disrupts the thesis.
- **Minor:** harmless filler in audio, spoken grammar, natural repetition for emphasis, short breath pause.

