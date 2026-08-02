---
name: continuous-story-video
description: Plan, generate, diagnose, repair, and edit continuous AI story videos from scripts, storyboards, first/end frames, reference images, generated clips, or multimodal video tools such as Seedance. Use when a user needs a multi-shot narrative video with stable characters, scenes, props, camera continuity, first-frame/end-frame strategy, hard-cut versus continuous-shot decisions, prompt timing, hidden-cut diagnosis, frame-diff QA, or iterative repairs for scene jumps, reference pollution, prop teleporting, reverse motion, or mismatched transitions.
---

# Continuous Story Video

Use this skill to make AI-generated story videos feel continuous instead of stitched together from unrelated nice images. Treat generation as a directing, continuity, and QA problem: decide which transitions should be continuous, which should be hard cuts, build stable references, write prompts that match reachable camera motion, inspect the exact seconds near starts and ends, and repair the true cause of each break.

If the target generator is Seedance/Jimeng, also use `$seedance-video-director` for platform-specific mode routing and prompt style. This skill adds the continuity workflow around it.

## Core Rule

Never assume first frame plus end frame means a shot can connect. A first/end-frame pair is valid only when the camera can naturally move from A to B within the duration while preserving:

- the same scene region or a believable adjacent region
- the same character identity, scale, pose progression, and costume
- the same object positions and prop causality
- the same camera side, height, and subject relationship
- one dominant action or one dominant framing change

If any of these fail, use a hard cut, insert shot, montage, video extension, or redraw the end frame from the first frame and the intended motion.

## Workflow

### 1. Read The Whole Story Before Making Assets

Extract the story beats first. For each beat, write:

- dramatic function: setup, discovery, rescue, gift, montage, setback, comfort, release, epilogue, title card
- emotional direction: curiosity to worry, cold to warm, shame to relief, etc.
- continuity anchors: character, costume, prop, location, weather, light, sound motif
- time relationship to adjacent beats: same moment, omitted time, later that day, many days later, memory, symbolic insert

Do not route shots by image order alone. A storyboard panel can be a useful visual reference while still being a hard cut in the final edit.

### 2. Classify Every Boundary

Make a boundary table before writing prompts.

Use **continuous shot** when the next image is the same action in the same space and the camera can travel naturally.

Use **tail-frame to next first-frame** when the action result carries across a scene change, such as "wrapped kitten" becoming "girl holding wrapped kitten on the way home". The final pose/object state must match even if the background changes.

Use **hard cut** when time, emotion, location, or camera language changes on purpose. Do not hide story jumps as fake continuous motion.

Use **montage** when the story says "many times", "from then on", "every day", or shows repeated objects/actions. Montage wants visible cuts, not morphing continuity.

Use **insert shot** when cutting from a calm wide/mid shot to a symbolic detail such as a bell in a hand. This is a film cut, not a camera move.

Use **video extension or chain generation** when the next beat must continue from the true previous video ending and the generator supports extension. If the user requires one 15s segment, enforce timing in the prompt and reduce reference contamination instead.

### 3. Build An Asset Bible Before Polished First Frames

For recurring stories, create stable references before generating final frames:

- large wide-angle scene plates for every recurring location
- pure-white-background character three-view sheets for every recurring character
- pure-white-background prop/entity sheets for important objects
- rough storyboard panels only as composition references, not identity sources
- a frame-to-scene-region map: each first/end frame must cite the scene plate and the exact area it uses

Do not generate first frames from unrelated panels without scene and character references. If two frames are supposed to be in the same room but the background differs, fix the frame assets before video generation.

For each final first/end frame prompt, explicitly say how references are used:

- image 1: target composition or first frame
- image 2: same character identity, do not copy background
- image 3: scene plate, use left window corner / desk area / alley wall section
- image 4: prop sheet, keep the same bell/leaf/box design

### 4. Validate First/End Frames Before Calling Video

For each proposed shot, compare the first frame, end frame, and any prior/next frame. Reject the pair if it requires hidden editing.

Common failure classes:

- **Action overload**: one short shot asks for walking, stopping, crouching, reaching, picking up, and reframing. Split the action or extend the duration.
- **Camera/subject switch**: exterior box view to inside-box close-up, mid shot to macro tear, front view to over-shoulder. Treat as a cut unless there is a true transition frame.
- **Scene-region mismatch**: same named location but different wall, window, light, or ground color. Fix by using the same scene-plate region.
- **Reference pollution**: a strong late medium/wide reference causes the first seconds to become medium/wide. Remove or weaken the late reference, or time-gate it in the prompt.
- **Prop teleporting**: an object appears on a table/hand without being picked up, pushed, carried, or shown in prior frames. Add causal action or redraw the target frame.
- **Pose reversal**: walking direction, body orientation, or hand use reverses between references. Regenerate the target with the previous frame as reference.
- **End-frame unreachable**: the end frame is aesthetically good but not the physical result of the shot's action. Redraw it from the shot's first frame plus motion description.

### 5. Choose The Generation Mode Per Segment

Do not force one mode across the whole film.

Use **first/end-frame video** for reachable motion between two well-matched frames.

Use **first-frame only** when the shot has atmosphere and small action but no strict end pose.

Use **all-purpose multimodal reference** when the shot needs character sheets, scene plates, props, motion reference, or audio rhythm. Label every file role.

Use **reference video** when a movement rhythm matters more than exact identity. Say "use video 1 only for motion/camera, not character or background" if needed.

Use **video extension** when the previous real video ending must be preserved and platform support is available.

Use **postproduction edit** for text cards, title reveal, clean fades, and simple black screens. Do not ask video generators to render precise final text unless unavoidable.

Use **montage generation** only when fast cuts are intended. Otherwise generate separate short shots and edit them.

### 6. Write Prompts As Timed Continuity Contracts

A prompt for a continuous story shot should be structured by time, not just vibe.

Include:

- the exact first-frame state
- the exact end-state or target if using an end frame
- one dominant camera behavior
- action order with timestamps
- what must stay fixed
- what must not happen
- how late references are time-scoped
- object causality

Template:

```text
Use image 1 as the first frame and starting composition. Use image 2 only as the final-state reference after 11.5s; do not let image 2 affect the first 0-8s. Use image 3 only for character identity. Use image 4 only for the room layout.

0-4s: keep the same close/mid composition as image 1. The character remains seated at the desk; only small breathing, tears, hand movement, and eye motion happen. No camera jump, no new angle.
4-8s: the prop enters causally from the floor/hand/previous position. Show how it moves. Keep the same desk, window, lamp, and floor geometry.
8-11.5s: begin a very slow pullback and slight rise, not a cut. Gradually reveal the full desk, chair, character upper body, and the companion character.
11.5-15s: only after the frame has already become a stable medium shot, complete the hug/action and settle toward image 2.

No hidden cuts, no sudden change of wall/window/light, no switching to macro close-up, no prop appearing from nowhere, no reverse walking.
```

When the user insists on a 15s single segment, do not solve by adding many strong reference images. Strong late references can contaminate the start. Prefer:

- one stable first frame
- identity/scene/prop references with restricted roles
- timed prompt language that delays the wider/closer composition
- a final frame only if it is reachable and explicitly time-gated
- no extra transition image unless it is subtle and derived from both the before and after frames

### 7. Generate Frames In Dependency Order

Generate shared references first, then first/end frames, then video segments.

For continuous chains:

1. Generate or choose shot A first frame.
2. Generate shot A end frame from shot A first frame plus motion prompt.
3. Generate shot A video.
4. Extract the **true last usable frame** from shot A video.
5. Use that true frame as shot B first frame if B must be continuous.

Do not use a planned Gemini end frame as the next first frame if the actual video ended differently. The viewer sees the generated video, not the planned still.

For a multi-shot chain:

```text
shot 1 first -> shot 1 generated tail = shot 2 first
shot 2 first -> shot 2 generated tail = shot 3 first
shot 3 first -> shot 3 generated tail = shot 4 first
```

For hard cuts, do not chain true tail frames. Instead make the cut intentional with contrast, sound, fade, or title/time change.

### 8. Diagnose Breaks By The Exact Second

When the user reports a jump, first locate whether it is:

- a concat boundary
- inside a generated segment
- caused by an end-frame target
- caused by a reference image
- caused by a missing causal prop/action
- caused by postproduction scaling/cropping

Inspect at least one second before and after the reported time. For suspected hidden cuts, also inspect dense frames every 0.1-0.25s. Do not only compare segment first and last frames.

Use the bundled script:

```bash
python C:/Users/VAIO/.codex/skills/continuous-story-video/scripts/continuity_check.py \
  --video path/to/video.mp4 \
  --range 38.4:40.8 \
  --range 20:25 \
  --fps 12 \
  --sheet-fps 8 \
  --out-dir path/to/checks
```

The script creates contact sheets and prints the highest frame-diff peaks. A high peak is not automatically wrong; verify the sheet visually. Character movement can be high, but a wall/window/scale/background replacement is a real continuity break.

### 9. Repair The Cause, Not The Symptom

Use the diagnosis to pick the repair:

- If the end frame is too close/far, redraw the end frame from the first frame and motion prompt.
- If a mid-shot suddenly changes scene region, regenerate the first/end frames using the same scene-plate area.
- If a late reference pollutes the beginning, remove that reference or weaken/time-gate it; do not add more references blindly.
- If a prop appears suddenly, add an earlier action showing it on the floor/table/hand, or adjust the prompt so it is pushed, picked up, carried, and then placed.
- If movement reverses, regenerate the target still with the previous frame as reference and lock direction.
- If the generator hides a cut inside a shot, reduce event count, use extension, or make the cut intentional in editing.
- If the user requires an unbroken 15s shot, keep the 15s but simplify the action path and bring the camera to the needed framing early enough.

Example repairs learned from this workflow:

- A 5s shot from room wide to hand close-up caused a hidden cut. Redraw the tail as a same-camera medium endpoint instead of a close-up.
- A 15s night scene jumped before the hug because the prompt kept a close picking-up action too long. Add a slow pullback starting several seconds earlier, then perform the hug after the medium frame is already established.
- Adding a strong medium transition image fixed the later jump but contaminated the first seconds. Remove or weaken that image and use time-scoped prompt control.
- A bell should not appear in the hand/table unless the shot shows how it moves from floor to hand/table.

### 10. Compose With Intentional Transitions

After segment generation, edit according to the boundary table:

- continuous boundaries: align last/first frames and avoid extra fades
- tail-to-head boundaries: cut on matching action result
- hard cuts: use contrast intentionally, often with sound or lighting change
- montage: use short cuts and rhythmic object motion
- insert shots: cut directly to the detail, then return or end
- title cards: create in postproduction for clean text

Maintain consistent resolution, frame rate, aspect ratio, and color handling in the final compose command. Do not let the editor introduce scaling or crop jumps.

### 11. Final QA Checklist

Before delivering, verify:

- all user-reported seconds and adjacent seconds
- one second near every segment start and end
- all continuous boundaries
- all hard cuts are intentional and motivated
- no character identity drift
- no scene background swaps inside a "same place" shot
- no prop teleporting or duplication
- no reverse walking or impossible body turn
- no late-reference pollution at the beginning of a long shot
- no text generated by video model when clean post text was required
- final file duration, fps, resolution, and aspect ratio
- uploaded links and local paths point to the latest version

When reporting back, name the strategy and the checks performed. Include contact sheets or exact seconds when the user has been reviewing visual continuity.
