from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


PROFILE_FLOORS = {
    "P01_dual_time_conflict": {"exact_clip": 0.50, "exact_duration": 0.55, "average_shot": 7.0, "forbid_under_five": True},
    "P02_agency_counterattack": {"exact_clip": 0.40, "exact_duration": 0.45, "average_shot": 6.0, "forbid_under_five": False},
    "P03_relationship_arc": {"exact_clip": 0.35, "exact_duration": 0.40, "average_shot": 6.0, "forbid_under_five": False},
    "P04_reveal_investigation": {"exact_clip": 0.45, "exact_duration": 0.50, "average_shot": 6.0, "forbid_under_five": False},
    "P05_contrast_anthology": {"exact_clip": 0.25, "exact_duration": 0.30, "average_shot": 4.5, "forbid_under_five": False},
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized(text: str) -> str:
    return re.sub(r"\s+", "", str(text or ""))


def value(row: dict, *keys: str):
    for key in keys:
        if row.get(key) is not None:
            return row[key]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate locked short-drama script-to-clip bindings.")
    parser.add_argument("beat_map", type=Path)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--story-plan", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    beat_map = json.loads(args.beat_map.read_text(encoding="utf-8-sig"))
    index = json.loads(args.index.read_text(encoding="utf-8-sig"))
    issues: list[dict] = []
    if beat_map.get("source_index_sha256") != sha256(args.index):
        issues.append({"type": "source-index-hash-mismatch"})
    if beat_map.get("story_plan_sha256") != sha256(args.story_plan):
        issues.append({"type": "story-plan-hash-mismatch"})

    known_events = {str(value(row, "event_id", "eventId")) for row in index.get("events", [])}
    known_shots = {str(value(row, "shot_id", "shotId")): row for row in index.get("shots", [])}
    scene_events: dict[str, set[str]] = {}
    for row in index.get("shots", []):
        scene_id = str(value(row, "scene_id", "sceneId") or "")
        scene_events.setdefault(scene_id, set()).update(str(item) for item in (value(row, "event_ids", "eventIds") or []))
    clips = {str(value(row, "clip_id", "clipId")): row for row in beat_map.get("clips", [])}
    roundtrip = normalized("".join(str(beat.get("text") or "") for beat in beat_map.get("beats", []))) == normalized(beat_map.get("approved_narration_text", ""))
    if not roundtrip:
        issues.append({"type": "script-roundtrip"})

    unbound = 0
    grade_duration: Counter[str] = Counter()
    grade_count: Counter[str] = Counter()
    used_clip_ids: list[str] = []
    for beat in beat_map.get("beats", []):
        beat_id = str(value(beat, "beat_id", "beatId") or "")
        event_ids = {str(item) for item in (value(beat, "event_ids", "eventIds") or [])}
        unknown = sorted(event_ids - known_events)
        if unknown:
            issues.append({"type": "beat-unknown-event", "beat_id": beat_id, "event_ids": unknown})
        if beat.get("factual", True) and not event_ids:
            unbound += 1
            issues.append({"type": "unbound-factual-beat", "beat_id": beat_id})
        bindings = beat.get("bindings") or []
        if not bindings:
            unbound += 1
            issues.append({"type": "beat-without-clip", "beat_id": beat_id})
        for binding in bindings:
            clip_id = str(value(binding, "clip_id", "clipId") or "")
            used_clip_ids.append(clip_id)
            clip = clips.get(clip_id)
            if not clip:
                issues.append({"type": "unknown-clip", "beat_id": beat_id, "clip_id": clip_id})
                continue
            shot_id = str(value(clip, "shot_id", "shotId") or "")
            shot = known_shots.get(shot_id)
            if not shot:
                issues.append({"type": "unknown-shot", "clip_id": clip_id, "shot_id": shot_id})
                continue
            shot_events = {str(item) for item in (value(shot, "event_ids", "eventIds") or [])}
            grade = str(binding.get("match_type") or "")
            scene_id = str(value(shot, "scene_id", "sceneId") or "")
            if grade == "exact" and event_ids and not (event_ids & shot_events):
                issues.append({"type": "clip-event-mismatch", "beat_id": beat_id, "clip_id": clip_id})
            if grade == "context" and event_ids and not (event_ids & scene_events.get(scene_id, set())):
                issues.append({"type": "clip-scene-context-mismatch", "beat_id": beat_id, "clip_id": clip_id})
            source_start, source_end = float(clip.get("source_start", 0)), float(clip.get("source_end", 0))
            shot_start = float(value(shot, "start", "source_start", "sourceStart") or 0)
            shot_end = float(value(shot, "end", "source_end", "sourceEnd") or 0)
            if source_start < shot_start - 1e-6 or source_end > shot_end + 1e-6 or source_end <= source_start:
                issues.append({"type": "clip-range-outside-shot", "clip_id": clip_id})
            if clip.get("safe_in") is not True or clip.get("safe_out") is not True:
                issues.append({"type": "unsafe-clip-boundary", "clip_id": clip_id})
            if float(clip.get("source_playback_speed", 0)) != 1.0:
                issues.append({"type": "source-speed", "clip_id": clip_id})
            if grade not in {"exact", "context", "neutral", "contradiction"}:
                issues.append({"type": "invalid-match-grade", "beat_id": beat_id, "grade": grade})
                continue
            duration = max(0.0, float(binding.get("coverage_end", 0)) - float(binding.get("coverage_start", 0)))
            grade_duration[grade] += duration
            grade_count[grade] += 1
            if binding.get("review_status") != "passed":
                issues.append({"type": "unreviewed-binding", "beat_id": beat_id, "clip_id": clip_id})
            if binding.get("contradictions"):
                issues.append({"type": "declared-contradiction", "beat_id": beat_id, "clip_id": clip_id})

    duplicates = sorted(clip_id for clip_id, count in Counter(used_clip_ids).items() if clip_id and count > 1)
    if duplicates:
        issues.append({"type": "reused-clip", "clip_ids": duplicates})
    total_duration = sum(grade_duration.values())
    total_count = sum(grade_count.values())
    exact_clip_ratio = grade_count["exact"] / total_count if total_count else 0.0
    exact_duration_ratio = grade_duration["exact"] / total_duration if total_duration else 0.0
    exact_context_ratio = (grade_duration["exact"] + grade_duration["context"]) / total_duration if total_duration else 0.0
    shot_durations = [max(0.0, float(row.get("source_end", 0)) - float(row.get("source_start", 0))) for row in clips.values()]
    average_shot = sum(shot_durations) / len(shot_durations) if shot_durations else 0.0
    profile = str(beat_map.get("narrative_profile") or "")
    floor = PROFILE_FLOORS.get(profile)
    if not floor:
        issues.append({"type": "unknown-narrative-profile", "profile": profile})
    else:
        if exact_clip_ratio < floor["exact_clip"]:
            issues.append({"type": "profile-exact-clip-floor", "actual": exact_clip_ratio, "required": floor["exact_clip"]})
        if exact_duration_ratio < floor["exact_duration"]:
            issues.append({"type": "profile-exact-duration-floor", "actual": exact_duration_ratio, "required": floor["exact_duration"]})
        if average_shot < floor["average_shot"]:
            issues.append({"type": "profile-average-shot-floor", "actual": average_shot, "required": floor["average_shot"]})
        if floor["forbid_under_five"] and any(duration < 5.0 for duration in shot_durations):
            issues.append({"type": "profile-under-five-shot"})
    if exact_context_ratio < 0.90:
        issues.append({"type": "exact-context-duration-floor", "actual": exact_context_ratio, "required": 0.90})
    if grade_count["contradiction"]:
        issues.append({"type": "contradiction-count", "count": grade_count["contradiction"]})

    metrics = {
        "scriptRoundtrip": roundtrip,
        "unboundBeatCount": unbound,
        "exactClipRatio": round(exact_clip_ratio, 6),
        "exactDurationRatio": round(exact_duration_ratio, 6),
        "exactOrContextDurationRatio": round(exact_context_ratio, 6),
        "averageShotSeconds": round(average_shot, 6),
        "contradictionCount": grade_count["contradiction"],
    }
    audit = {"schema": "script-clip-binding-audit-v1", "status": "passed" if not issues else "failed", "narrativeProfile": profile, "metrics": metrics, "issues": issues}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
