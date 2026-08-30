from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


STORY_FIELDS = (
    "number", "title", "episodes", "family_id", "family_label",
    "story_type", "story_type_label", "narrative_profile",
    "central_question", "hook_promise", "payoff_evidence",
    "episode_bridge_rationale", "required_slot_map", "event_grades",
    "narration", "dialogues", "dialogue_slots", "hook",
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def require_file(path: Path, label: str) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"missing {label}: {path}")
    return path.resolve()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a story-locked narration beat map from a reviewed recap EDL.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--job-number", type=int, required=True)
    parser.add_argument("--render-job", type=Path, required=True)
    parser.add_argument("--broll", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--story-plan-output", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    config = load(args.config)
    source_job = next((row for row in config.get("jobs", []) if int(row.get("number", -1)) == args.job_number), None)
    if source_job is None:
        raise RuntimeError(f"job {args.job_number} not found in {args.config}")
    story_plan = {field: source_job[field] for field in STORY_FIELDS if field in source_job}
    dump(args.story_plan_output, story_plan)
    story_hash = digest(args.story_plan_output)

    render_job = load(args.render_job)
    broll = load(args.broll)
    review = load(args.review)
    if review.get("metrics", {}).get("passes") is not True:
        raise RuntimeError("visual review did not pass")
    review_by_beat = {str(row.get("beat_id")): row for row in review.get("mappings", [])}
    narration_timeline = {
        str(row.get("id")): row for row in render_job.get("timeline", []) if row.get("type") == "narration"
    }

    beats = []
    clips = []
    approved_parts = []
    for block in broll:
        block_id = str(block.get("block") or "")
        timeline = narration_timeline.get(block_id)
        if timeline is None:
            raise RuntimeError(f"missing narration timeline for {block_id}")
        block_text = str(block.get("text") or "")
        if block_text != str(timeline.get("text") or ""):
            raise RuntimeError(f"narration text mismatch for {block_id}")
        rows = list(block.get("clips") or [])
        if not rows:
            raise RuntimeError(f"no reviewed clips for {block_id}")
        if "".join(str(row.get("beat_text") or row.get("narration_sentence") or "") for row in rows) != block_text:
            raise RuntimeError(f"beat text does not round-trip for {block_id}")
        raw_end = max(float(row.get("tts_end") or 0) for row in rows)
        # The reviewed picture rail covers the full narration block, including an
        # intentional tail pad.  Use that full duration for beat-to-picture
        # mapping; using speechDuration alone leaves the tail visually unbound
        # and shifts the final beat away from the actual edit timeline.
        mapped_duration = float(timeline.get("duration") or timeline.get("speechDuration") or 0)
        if raw_end <= 0 or mapped_duration <= 0:
            raise RuntimeError(f"invalid timing basis for {block_id}")
        timing_scale = mapped_duration / raw_end
        block_start = float(timeline.get("timelineStart") or 0)
        picture_cursor = block_start
        approved_parts.append(block_text)

        for index, row in enumerate(rows):
            beat_id = str(row.get("beat_id") or "")
            if not beat_id:
                raise RuntimeError(f"missing beat_id in {block_id}")
            reviewed = review_by_beat.get(beat_id)
            if reviewed is None:
                raise RuntimeError(f"missing reviewed mapping for {beat_id}")
            evidence = [require_file(args.evidence_root / f"{beat_id}-{frame}.jpg", f"evidence frame {beat_id}-{frame}") for frame in (1, 2, 3)]
            beat_start = block_start + float(row.get("tts_start") or 0) * timing_scale
            beat_end = block_start + float(row.get("tts_end") or 0) * timing_scale
            source_start = float(row.get("clip_start") or row.get("start") or 0)
            source_duration = float(row.get("clip_duration") or 0)
            if source_duration <= 0:
                source_duration = float(row.get("end") or 0) - source_start
            reviewed_source_duration = float(row.get("reviewed_clip_duration") or source_duration)
            reviewed_source_end = source_start + reviewed_source_duration
            mastered_timing_trim = max(0.0, reviewed_source_duration - source_duration)
            if mastered_timing_trim > 0.25:
                raise RuntimeError(
                    "reviewed source range was shortened by more than 0.25 seconds "
                    f"after narration mastering: {beat_id}"
                )
            if mastered_timing_trim > 0 and row.get("safe_out") is not True:
                raise RuntimeError(f"mastered-timing trim requires a reviewed safe exit: {beat_id}")
            source_end = source_start + source_duration
            hold_after = max(0.0, float(row.get("hold_after") or 0))
            clip_timeline_start = picture_cursor
            clip_timeline_end = clip_timeline_start + source_duration + hold_after
            picture_cursor = clip_timeline_end
            coverage_start = max(beat_start, clip_timeline_start)
            coverage_end = min(beat_end, clip_timeline_end)
            event_value = str(row.get("event_id") or row.get("scene_id") or "")
            if not event_value:
                raise RuntimeError(f"missing event binding for {beat_id}")
            clip_id = f"{beat_id}-C01"
            match_type = str(reviewed.get("match_type") or row.get("match_type") or "")
            contradiction = bool(reviewed.get("contradiction", row.get("contradiction", False)))
            beats.append({
                "beat_id": beat_id,
                "text": str(row.get("beat_text") or row.get("narration_sentence") or ""),
                "tts_start": round(beat_start, 6),
                "tts_end": round(beat_end, 6),
                "factual": True,
                "event_ids": [event_value],
                "continuity_group": str(row.get("scene_id") or event_value),
                "requirements": {
                    "characters": row.get("required_character") or [],
                    "action": row.get("required_action") or "",
                    "location": row.get("required_location") or "",
                    "time_state": row.get("required_time_state") or "",
                    "emotion": row.get("required_emotion") or "",
                },
                "bindings": [{
                    "clip_id": clip_id,
                    "coverage_start": round(coverage_start, 6),
                    "coverage_end": round(coverage_end, 6),
                    "match_type": match_type,
                    "review_status": "passed" if not contradiction else "failed",
                    "contradictions": [] if not contradiction else ["visual review marked contradiction"],
                    "review_confidence": reviewed.get("confidence"),
                    "review_rationale": reviewed.get("rationale"),
                    "evidence_frames": [str(path) for path in evidence],
                }],
            })
            clips.append({
                "clip_id": clip_id,
                "episode": int(row["episode"]),
                "source_start": round(source_start, 6),
                "source_end": round(source_end, 6),
                "reviewed_source_end": round(reviewed_source_end, 6),
                "mastered_timing_trim": round(mastered_timing_trim, 6),
                "timeline_start": round(clip_timeline_start, 6),
                "timeline_end": round(clip_timeline_end, 6),
                "hold_after": round(hold_after, 6),
                "event_ids": [event_value],
                "safe_in": row.get("safe_in") is True,
                "safe_out": row.get("safe_out") is True,
                "source_playback_speed": 1.0,
            })

        block_end = float(timeline.get("timelineEnd") or (block_start + float(timeline.get("duration") or 0)))
        if abs(picture_cursor - block_end) > 1.0 / 25.0 + 0.001:
            raise RuntimeError(
                f"actual B-roll timeline does not cover narration block within one frame: "
                f"{block_id} picture_end={picture_cursor:.6f} block_end={block_end:.6f}"
            )

    preview = require_file(args.preview, "alignment preview")
    result = {
        "schema": "narration-beat-map-v1",
        "video_id": str(render_job.get("id") or f"recap-{args.job_number:02d}"),
        "approved_narration_text": "".join(approved_parts),
        "story_plan_sha256": story_hash,
        "story_plan": str(args.story_plan_output.resolve()),
        "review_source": str(args.review.resolve()),
        "beats": beats,
        "clips": clips,
        "preview": {"path": str(preview), "review_status": "passed"},
    }
    dump(args.output, result)
    print(json.dumps({"output": str(args.output), "beats": len(beats), "clips": len(clips), "storyPlanSha256": story_hash}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
