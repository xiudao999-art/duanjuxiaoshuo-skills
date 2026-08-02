# QC checklist

## Editorial

- Every approved beat appears in order.
- Narration wording and narration captions exactly match the approved article.
- Every original-dialogue insert begins and ends on a complete sentence.
- The exit after a dialogue has 0.30–0.50 seconds of room or a documented reaction tail.
- Narration never interrupts or overlaps original dialogue.
- Named characters and stated events match the visible shot.

## Visual

- Inspect first 2 seconds, last 2 seconds, and a contact sheet at 8-second intervals.
- Inspect every narration/dialogue boundary with a filmstrip plus waveform covering at least ±1.5 seconds.
- Confirm 1080×1920, expected fps, no black flash, no frozen tail, no lower-half mask, and no hidden caption.
- Confirm the upper-right source notice persists on title, narration, and dialogue frames.

## Captions

- Run `validate_segments.mjs` on the job caption directory.
- Confirm all manifests report `script-text+asr-timing`.
- Inspect protected names, line starts, two-line fit, and bottom safe area.

## Audio

- Measure integrated loudness and true peak after final AAC encoding.
- Aim near -14 LUFS integrated and require true peak no higher than -1 dBTP.
- Check for clicks at every cut and suspicious silence of at least 0.8 seconds.

## Safety and handoff

- Run a credential-pattern scan over the job directory.
- Verify H.264 video plus AAC 48 kHz audio with `ffprobe`.
- Hash the mastered file and copied delivery; hashes must match.
- Write `qc/qc-report.md` with dialogue ranges, voice ID, caption validation, media specs, loudness, and unresolved limitations.

