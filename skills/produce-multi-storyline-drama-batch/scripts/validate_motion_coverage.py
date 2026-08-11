from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def frames(seconds: float, fps: int) -> int:
    return round(max(0.0, float(seconds)) * fps)


def audit_motion_coverage(
    job: dict,
    broll: list[dict],
    fps: int = 25,
    max_hold_frames: int = 3,
) -> dict:
    if fps <= 0 or max_hold_frames < 0:
        raise ValueError("fps must be positive and max_hold_frames must be non-negative")

    narration = {
        str(row.get("id") or ""): row
        for row in job.get("timeline", [])
        if row.get("type") == "narration" and str(row.get("id") or "")
    }
    issues: list[dict] = []
    blocks: list[dict] = []
    total_target_frames = 0
    total_moving_frames = 0
    total_hold_frames = 0
    maximum_clip_hold_frames = 0

    for block in broll if isinstance(broll, list) else []:
        block_id = str(block.get("block") or "")
        timeline = narration.get(block_id)
        if timeline is None:
            issues.append({"type": "missing-narration-block", "block": block_id})
            continue
        clips = [row for row in block.get("clips", []) if isinstance(row, dict)]
        if not clips:
            issues.append({"type": "missing-motion-clips", "block": block_id})
            continue

        duration = float(timeline.get("duration") or 0)
        if duration <= 0:
            duration = float(timeline.get("timelineEnd") or 0) - float(timeline.get("timelineStart") or 0)
        target_frames = frames(duration, fps)
        moving_frames = 0
        hold_frames = 0
        clip_rows = []
        for index, clip in enumerate(clips, 1):
            clip_duration = float(clip.get("clip_duration") or 0)
            hold_after = float(clip.get("hold_after") or 0)
            clip_frames = frames(clip_duration, fps)
            clip_hold_frames = frames(hold_after, fps)
            moving_frames += clip_frames
            hold_frames += clip_hold_frames
            maximum_clip_hold_frames = max(maximum_clip_hold_frames, clip_hold_frames)
            clip_rows.append({
                "clip": index,
                "beatId": clip.get("beat_id"),
                "sceneId": clip.get("scene_id"),
                "movingFrames": clip_frames,
                "holdFrames": clip_hold_frames,
            })
            if clip_frames <= 0:
                issues.append({"type": "empty-motion-clip", "block": block_id, "clip": index})
            if clip_hold_frames > max_hold_frames:
                issues.append({
                    "type": "clip-hold-over-budget",
                    "block": block_id,
                    "clip": index,
                    "holdFrames": clip_hold_frames,
                    "maximum": max_hold_frames,
                })

        assembled_frames = moving_frames + hold_frames
        motion_shortfall_frames = max(0, target_frames - moving_frames)
        timeline_delta_frames = assembled_frames - target_frames
        if motion_shortfall_frames > max_hold_frames:
            issues.append({
                "type": "moving-picture-shortfall",
                "block": block_id,
                "shortfallFrames": motion_shortfall_frames,
                "shortfallSeconds": round(motion_shortfall_frames / fps, 3),
            })
        if hold_frames > max_hold_frames:
            issues.append({
                "type": "block-hold-over-budget",
                "block": block_id,
                "holdFrames": hold_frames,
                "maximum": max_hold_frames,
            })
        if abs(timeline_delta_frames) > 1:
            issues.append({
                "type": "picture-timeline-frame-mismatch",
                "block": block_id,
                "deltaFrames": timeline_delta_frames,
            })

        total_target_frames += target_frames
        total_moving_frames += moving_frames
        total_hold_frames += hold_frames
        blocks.append({
            "block": block_id,
            "targetFrames": target_frames,
            "movingFrames": moving_frames,
            "declaredHoldFrames": hold_frames,
            "motionShortfallFrames": motion_shortfall_frames,
            "timelineDeltaFrames": timeline_delta_frames,
            "clips": clip_rows,
        })

    missing = sorted(set(narration).difference(str(row.get("block") or "") for row in broll if isinstance(row, dict)))
    for block_id in missing:
        issues.append({"type": "narration-block-without-broll", "block": block_id})

    metrics = {
        "fps": fps,
        "blockCount": len(blocks),
        "clipCount": sum(len(row["clips"]) for row in blocks),
        "targetFrames": total_target_frames,
        "movingFrames": total_moving_frames,
        "declaredHoldFrames": total_hold_frames,
        "movingCoverageRatio": total_moving_frames / total_target_frames if total_target_frames else 0.0,
        "maximumClipHoldFrames": maximum_clip_hold_frames,
        "maximumAllowedHoldFramesPerBlock": max_hold_frames,
        "blocksWithMotionShortfallCount": sum(row["motionShortfallFrames"] > max_hold_frames for row in blocks),
        "blocksWithTimelineMismatchCount": sum(abs(row["timelineDeltaFrames"]) > 1 for row in blocks),
        "blocksOverHoldBudgetCount": sum(row["declaredHoldFrames"] > max_hold_frames for row in blocks),
    }
    return {
        "schema": "motion-coverage-audit-v1",
        "status": "passed" if not issues and blocks else "failed",
        "metrics": metrics,
        "blocks": blocks,
        "issues": issues,
        "repairPolicy": {
            "storyPlanMutable": False,
            "maxTargetedRepairPasses": 1,
            "onSecondFailure": "mark-visual-coverage-pending-and-continue-batch",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fail fast when narration B-roll lacks moving-frame coverage.")
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--broll", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fps", type=int, default=25)
    parser.add_argument("--max-hold-frames", type=int, default=3)
    args = parser.parse_args()
    report = audit_motion_coverage(load(args.job), load(args.broll), args.fps, args.max_hold_frames)
    dump(args.output, report)
    print(json.dumps({"status": report["status"], "metrics": report["metrics"], "issueCount": len(report["issues"])}, ensure_ascii=False, indent=2))
    if report["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
