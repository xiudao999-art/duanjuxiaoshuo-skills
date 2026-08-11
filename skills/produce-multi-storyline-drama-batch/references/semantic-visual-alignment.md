# Semantic narration-to-picture alignment

Use this protocol after story selection and narration writing. It improves
picture evidence without changing the selected narrative family, profile,
central question, causal spine, or payoff.

## Inputs and locks

Require:

- the approved story plan and its SHA-256;
- the full transcript and word timings;
- an audited event/scene ledger with canonical identities and source ranges;
- the approved narration text;
- synthesized narration with real word timings;
- a shot graph or reviewed safe cut boundaries.

Audit character aliases, relationships, age/time states, actions, and episode
ranges before binding. Fix ledger errors at the source. Do not compensate for a
wrong identity by choosing a vaguely similar shot.

Once the approved story-plan SHA-256 is written, visual alignment is strictly
downstream. It may adjust safe source in/out points inside already-bound events
and scenes, but it must not change the narrative family/profile, central
question, causal spine, hook, narration or dialogue text, event IDs or order,
or payoff.

## Build semantic beats

Group one to three adjacent sentences only when they describe the same event or
one continuous causal action. Split when the character, action, location, time
state, or event changes. This normally yields about 7–11 narration-picture
clips for a two-minute recap, not one clip per sentence.

Create `planning/narration-beat-maps/<job-id>.json`:

```json
{
  "schema": "narration-beat-map-v1",
  "video_id": "recap-01",
  "approved_narration_text": "她被送到医院后医生要求立刻手术……",
  "story_plan_sha256": "...",
  "beats": [
    {
      "beat_id": "N1-B02",
      "text": "医生宣布她必须立刻接受手术",
      "tts_start": 12.17,
      "tts_end": 18.02,
      "factual": true,
      "event_ids": ["E01-02"],
      "continuity_group": "医院抢救",
      "requirements": {
        "characters": ["周青云", "医生"],
        "action": "医生宣布必须手术",
        "location": "医院",
        "time_state": "火灾后",
        "emotion": "紧急"
      },
      "bindings": [
        {
          "clip_id": "C02",
          "coverage_start": 12.17,
          "coverage_end": 18.02,
          "match_type": "exact",
          "review_status": "passed",
          "contradictions": [],
          "evidence_frames": ["qc/frames/N1-B02-start.jpg", "qc/frames/N1-B02-mid.jpg", "qc/frames/N1-B02-end.jpg"]
        }
      ]
    }
  ],
  "clips": [
    {
      "clip_id": "C02",
      "episode": 1,
      "source_start": 102.24,
      "source_end": 112.93,
      "timeline_start": 12.17,
      "timeline_end": 22.86,
      "event_ids": ["E01-02"],
      "safe_in": true,
      "safe_out": true,
      "source_playback_speed": 1.0
    }
  ],
  "preview": {
    "path": "qc/alignment-preview.mp4",
    "review_status": "passed"
  }
}
```

The concatenated beat text must round-trip exactly to
`approved_narration_text` after whitespace normalization. Never write an event
title into `text` merely to make a manifest look bound.

## Bind by event, then preserve continuity

1. Retrieve candidates only through the beat's event IDs and adjacent events in
   the same scene. Never retrieve by narration-word similarity after lock.
2. Prefer an exact event range showing the required character and action.
3. Extend inside the same complete scene to include setup, gesture, reaction,
   or a stable cut boundary.
4. Let the previous verified scene continue over an adjacent explanatory beat
   when it remains contextually correct.
5. Use a neutral transition only when exact/context coverage already meets the
   hard gate and the shot introduces no false fact.
6. If no valid footage proves a factual sentence, first search the same event
   and its already-bound adjacent reaction. If none exists, fail that job before
   story lock or mark it `visual-coverage-pending` after lock. Never rewrite a
   locked sentence, add an event, or change the story's central question or
   causal spine to satisfy footage.

## Match grades and thresholds

| Grade | Meaning | Gate |
|---|---|---:|
| `exact` | character, action, place, time state, and event directly match | clips ≥50%; duration ≥55%, target 60–65% |
| `context` | same scene/person or adjacent causal reaction, no contradiction | exact + context duration ≥90% |
| `neutral` | establishing/object/walk/silent reaction, no false fact | duration ≤10% |
| `contradiction` | wrong person/action/place/time/emotion | count = 0 |

Also require `unboundBeatCount=0`. Read the selected Profile for its
exact-clip ratio, exact-duration ratio, average-shot duration, and
under-five-second policy. Do not use P01's stricter picture floor as a global
gate. Keep at most four picture cuts in a rolling 30-second narration window
unless an approved Profile override explicitly defines a different density.

Measure beat duration from the mastered narration, not the pre-master TTS
timestamps. When a reviewed `safe_out` source range exceeds the mastered beat
by no more than 0.25 seconds, the builder may shorten only that excess and must
record `mastered_timing_trim`; anything larger or lacking a reviewed safe exit
is a hard failure. Never speed up drama footage to hide this mismatch.

The builder must derive clip timeline positions from the actual B-roll cursor:
`clip_duration + hold_after` in render order. It must not reconstruct picture
timing by proportionally scaling pre-master TTS durations. This same cursor is
used by the motion preflight and encoded cut-boundary audit.

## Preview before expensive processing

First run the frame-budget preflight against final mastered narration and the
materialized B-roll plan. It uses deterministic arithmetic, no visual model:

```powershell
python scripts/validate_motion_coverage.py `
  --job production/recap-01/job.json `
  --broll production/recap-01/broll-audit.json `
  --output production/recap-01/qc/motion-coverage-audit.json
```

Require `status=passed`, zero shortfall, timeline mismatch, and hold-budget
blocks, and `maximumClipHoldFrames<=3`. `hold_after` defaults to zero; the
three-frame allowance is only for rounding. Do not use `tpad`, cloned final
frames, or a still image to replace missing motion.

On failure, make one targeted safe-range repair inside the same already-bound
event/scene and run the preflight once more. A second failure becomes
`visual-coverage-pending`; continue the batch without VSR or rendering that
item. This cap prevents an open-ended QC loop.

After the preflight passes, render exactly one 540×960 preview from the locked
beat map before VSR/STTN. Inspect the
start, middle, and end of every beat. Confirm identity, action, location,
chronology, emotion, continuous motion, and cut safety. Store evidence frames
and route only low-confidence or identity-sensitive beats to extra visual
review.

Do not begin VSR or final rendering until:

```powershell
python scripts/validate_motion_coverage.py `
  --job production/recap-01/job.json `
  --broll production/recap-01/broll-audit.json `
  --output production/recap-01/qc/motion-coverage-audit.json

python scripts/build_semantic_alignment_map.py `
  --config configs/job.json --job-number 1 `
  --render-job production/recap-01/job.json `
  --broll production/recap-01/broll-audit.json `
  --review qc/semantic-visual-audit/recap-01/audit-result.json `
  --evidence-root qc/semantic-visual-audit/recap-01/frames `
  --preview qc/semantic-visual-audit/recap-01/alignment-preview.mp4 `
  --story-plan-output planning/selected/recap-01.json `
  --output planning/narration-beat-maps/recap-01.json

python scripts/validate_semantic_alignment.py planning/narration-beat-maps/recap-01.json `
  --event-ledger planning/event-scene-ledger.json `
  --story-plan planning/selected/recap-01.json `
  --output production/recap-01/qc/semantic-alignment-audit.json
```

exits successfully. Narration, timing, or event changes invalidate the story
lock and return to planning. A source-range or EDL change reruns only the motion
preflight, one preview if not yet approved, and the affected alignment/VSR/QC
artifacts.
