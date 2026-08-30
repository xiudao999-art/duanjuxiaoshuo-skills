from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_text(value: str) -> str:
    return re.sub(r"\s+", "", str(value or ""))


def as_rows(value) -> list[dict]:
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    if isinstance(value, dict):
        for key in ("events", "scenes", "event_ledger", "eventLedger", "rows"):
            if isinstance(value.get(key), list):
                return [row for row in value[key] if isinstance(row, dict)]
        rows = [row for row in value.values() if isinstance(row, dict) and (row.get("event_id") or row.get("eventId"))]
        if rows:
            return rows
    return []


def event_id(row: dict) -> str:
    return str(row.get("event_id") or row.get("eventId") or row.get("scene_id") or row.get("sceneId") or "").strip()


def number(row: dict, *keys: str) -> float | None:
    for key in keys:
        if row.get(key) is not None:
            try:
                return float(row[key])
            except (TypeError, ValueError):
                return None
    return None


def event_overlaps_clip(event: dict, clip: dict) -> bool:
    event_episode = number(event, "episode")
    clip_episode = number(clip, "episode")
    event_start = number(event, "source_start", "sourceStart", "start")
    event_end = number(event, "source_end", "sourceEnd", "end")
    clip_start = number(clip, "source_start", "sourceStart")
    clip_end = number(clip, "source_end", "sourceEnd")
    if None in (event_episode, clip_episode, event_start, event_end, clip_start, clip_end):
        return False
    return int(event_episode) == int(clip_episode) and min(event_end, clip_end) > max(event_start, clip_start)


def intervals_length(intervals: list[tuple[float, float]]) -> float:
    merged: list[list[float]] = []
    for start, end in sorted(intervals):
        if end <= start:
            continue
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return sum(end - start for start, end in merged)


def resolve_evidence_path(map_path: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else map_path.parent / candidate


def rolling_cut_count(clips: list[dict]) -> int:
    starts = sorted(float(row.get("timeline_start") or 0) for row in clips)
    boundaries = starts[1:]
    if not boundaries:
        return 0
    maximum = 0
    for start in boundaries:
        maximum = max(maximum, sum(1 for value in boundaries if start <= value < start + 30.0))
    return maximum


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate narration-to-picture semantic alignment without changing the story plan.")
    parser.add_argument("beat_map", type=Path)
    parser.add_argument("--event-ledger", type=Path, required=True)
    parser.add_argument("--story-plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    data = load(args.beat_map)
    profile = str(data.get("narrative_profile") or "P01_dual_time_conflict")
    profile_rules = {
        "P01_dual_time_conflict": (0.50, 0.55, 7.0, True),
        "P02_agency_counterattack": (0.40, 0.45, 6.0, False),
        "P03_relationship_progression": (0.35, 0.40, 6.0, False),
        "P03_relationship_arc": (0.35, 0.40, 6.0, False),
        "P04_reveal_investigation": (0.45, 0.50, 6.0, False),
        "P05_contrast_anthology": (0.25, 0.30, 4.5, False),
    }
    exact_clip_floor, exact_duration_floor, average_clip_floor, no_under_five = profile_rules.get(
        profile, profile_rules["P01_dual_time_conflict"]
    )
    beats = [row for row in data.get("beats", []) if isinstance(row, dict)]
    clips = [row for row in data.get("clips", []) if isinstance(row, dict)]
    ledger_rows = as_rows(load(args.event_ledger))
    ledger = {event_id(row): row for row in ledger_rows if event_id(row)}
    clip_index = {str(row.get("clip_id") or "").strip(): row for row in clips if str(row.get("clip_id") or "").strip()}

    issues: list[dict] = []
    joined_text = "".join(str(row.get("text") or "") for row in beats)
    approved_text = str(data.get("approved_narration_text") or "")
    script_roundtrip = bool(approved_text) and normalized_text(joined_text) == normalized_text(approved_text)
    if not script_roundtrip:
        issues.append({"type": "script-roundtrip", "message": "Beat text does not equal approved narration text."})

    expected_story_hash = sha256(args.story_plan)
    story_hash_matches = str(data.get("story_plan_sha256") or "").lower() == expected_story_hash.lower()
    if not story_hash_matches:
        issues.append({"type": "story-plan-hash", "message": "Beat map is not locked to the supplied story plan."})

    total_duration = 0.0
    exact_intervals: list[tuple[float, float]] = []
    exact_context_intervals: list[tuple[float, float]] = []
    neutral_intervals: list[tuple[float, float]] = []
    all_coverage_intervals: list[tuple[float, float]] = []
    exact_clip_ids: set[str] = set()
    used_clip_ids: set[str] = set()
    contradiction_count = 0
    unbound_count = 0
    evidence_missing_count = 0
    ledger_unresolved_count = 0

    for beat in beats:
        beat_id = str(beat.get("beat_id") or "").strip()
        start = float(beat.get("tts_start") or 0)
        end = float(beat.get("tts_end") or 0)
        if not beat_id or end <= start:
            issues.append({"type": "invalid-beat", "beat": beat_id})
            continue
        total_duration += end - start
        beat_events = {str(value) for value in beat.get("event_ids", []) if str(value)}
        if bool(beat.get("factual", True)) and not beat_events:
            unbound_count += 1
            issues.append({"type": "missing-event-binding", "beat": beat_id})
        unknown_events = sorted(value for value in beat_events if value not in ledger)
        if unknown_events:
            ledger_unresolved_count += len(unknown_events)
            issues.append({"type": "unknown-event", "beat": beat_id, "event_ids": unknown_events})

        beat_supported = False
        for binding in beat.get("bindings", []):
            if not isinstance(binding, dict):
                continue
            clip_id_value = str(binding.get("clip_id") or "").strip()
            clip = clip_index.get(clip_id_value)
            if clip is None:
                issues.append({"type": "unknown-clip", "beat": beat_id, "clip_id": clip_id_value})
                continue
            used_clip_ids.add(clip_id_value)
            coverage_start = max(start, float(binding.get("coverage_start") or start))
            coverage_end = min(end, float(binding.get("coverage_end") or end))
            match_type = str(binding.get("match_type") or "").strip().lower()
            contradictions = binding.get("contradictions") or []
            if contradictions or match_type == "contradiction":
                contradiction_count += max(1, len(contradictions))
                issues.append({"type": "contradiction", "beat": beat_id, "clip_id": clip_id_value, "details": contradictions})
            if binding.get("review_status") != "passed":
                issues.append({"type": "unreviewed-binding", "beat": beat_id, "clip_id": clip_id_value})
            evidence = [str(value) for value in binding.get("evidence_frames", []) if str(value)]
            if len(evidence) < 3 or any(not resolve_evidence_path(args.beat_map, value).is_file() for value in evidence):
                evidence_missing_count += 1
                issues.append({"type": "missing-evidence-frames", "beat": beat_id, "clip_id": clip_id_value})
            if coverage_end <= coverage_start:
                issues.append({"type": "invalid-coverage", "beat": beat_id, "clip_id": clip_id_value})
                continue
            clip_timeline_start = float(clip.get("timeline_start") or 0)
            clip_timeline_end = float(clip.get("timeline_end") or 0)
            if coverage_start < clip_timeline_start - 0.001 or coverage_end > clip_timeline_end + 0.001:
                issues.append({"type": "coverage-outside-clip", "beat": beat_id, "clip_id": clip_id_value})
            all_coverage_intervals.append((coverage_start, coverage_end))
            if match_type == "exact":
                clip_events = {str(value) for value in clip.get("event_ids", []) if str(value)}
                shared_events = beat_events.intersection(clip_events)
                if not shared_events:
                    issues.append({"type": "exact-event-mismatch", "beat": beat_id, "clip_id": clip_id_value})
                elif not any(event_overlaps_clip(ledger[value], clip) for value in shared_events if value in ledger):
                    issues.append({"type": "exact-source-range-mismatch", "beat": beat_id, "clip_id": clip_id_value})
                else:
                    beat_supported = True
                exact_clip_ids.add(clip_id_value)
                exact_intervals.append((coverage_start, coverage_end))
                exact_context_intervals.append((coverage_start, coverage_end))
            elif match_type == "context":
                beat_supported = True
                exact_context_intervals.append((coverage_start, coverage_end))
            elif match_type == "neutral":
                neutral_intervals.append((coverage_start, coverage_end))
            else:
                issues.append({"type": "invalid-match-type", "beat": beat_id, "clip_id": clip_id_value, "value": match_type})
        if bool(beat.get("factual", True)) and not beat_supported:
            unbound_count += 1
            issues.append({"type": "unbound-factual-beat", "beat": beat_id})

    clip_durations: list[float] = []
    playback_mismatch_count = 0
    picture_hold_over_three_frames_count = 0
    maximum_picture_hold_seconds = 0.0
    mastered_timing_trim_count = 0
    maximum_mastered_timing_trim = 0.0
    unsafe_boundary_count = 0
    for clip_id_value in sorted(used_clip_ids):
        clip = clip_index[clip_id_value]
        source_duration = float(clip.get("source_end") or 0) - float(clip.get("source_start") or 0)
        timeline_duration = float(clip.get("timeline_end") or 0) - float(clip.get("timeline_start") or 0)
        hold_after = float(clip.get("hold_after") or 0)
        mastered_timing_trim = float(clip.get("mastered_timing_trim") or 0)
        clip_durations.append(source_duration)
        maximum_picture_hold_seconds = max(maximum_picture_hold_seconds, hold_after)
        if mastered_timing_trim > 0:
            mastered_timing_trim_count += 1
            maximum_mastered_timing_trim = max(maximum_mastered_timing_trim, mastered_timing_trim)
        if mastered_timing_trim < 0 or mastered_timing_trim > 0.25:
            issues.append({"type": "invalid-mastered-timing-trim", "clip_id": clip_id_value, "trim": mastered_timing_trim})
        if hold_after < 0 or hold_after > 0.12:
            picture_hold_over_three_frames_count += 1
            issues.append({"type": "invalid-final-frame-hold", "clip_id": clip_id_value, "hold_after": hold_after})
        if abs((source_duration + hold_after) - timeline_duration) > 0.12 or abs(float(clip.get("source_playback_speed") or 0) - 1.0) > 0.001:
            playback_mismatch_count += 1
            issues.append({"type": "source-playback-mismatch", "clip_id": clip_id_value})
        if clip.get("safe_in") is not True or clip.get("safe_out") is not True:
            unsafe_boundary_count += 1
            issues.append({"type": "unsafe-cut-boundary", "clip_id": clip_id_value})
        clip_events = [str(value) for value in clip.get("event_ids", []) if str(value)]
        missing = [value for value in clip_events if value not in ledger]
        if missing:
            ledger_unresolved_count += len(missing)
            issues.append({"type": "clip-unknown-event", "clip_id": clip_id_value, "event_ids": missing})
        elif clip_events and not any(event_overlaps_clip(ledger[value], clip) for value in clip_events):
            issues.append({"type": "clip-source-range-mismatch", "clip_id": clip_id_value, "event_ids": clip_events})

    exact_duration = intervals_length(exact_intervals)
    exact_context_duration = intervals_length(exact_context_intervals)
    neutral_duration = intervals_length(neutral_intervals)
    visual_coverage_duration = intervals_length(all_coverage_intervals)
    used_clip_count = len(used_clip_ids)
    metrics = {
        "scriptRoundtrip": script_roundtrip,
        "storyPlanHashMatches": story_hash_matches,
        "eventLedgerResolved": ledger_unresolved_count == 0,
        "beatCount": len(beats),
        "usedSourceClipCount": used_clip_count,
        "exactMatchClipRatio": len(exact_clip_ids) / used_clip_count if used_clip_count else 0.0,
        "exactMatchDurationRatio": exact_duration / total_duration if total_duration else 0.0,
        "exactOrContextDurationRatio": exact_context_duration / total_duration if total_duration else 0.0,
        "neutralDurationRatio": neutral_duration / total_duration if total_duration else 0.0,
        "visualCoverageRatio": visual_coverage_duration / total_duration if total_duration else 0.0,
        "averageSourceClipDuration": sum(clip_durations) / len(clip_durations) if clip_durations else 0.0,
        "sourceClipUnder5SecondsCount": sum(value < 5.0 for value in clip_durations),
        "maximumCutsPerRolling30Seconds": rolling_cut_count([clip_index[value] for value in used_clip_ids]),
        "contradictionCount": contradiction_count,
        "unboundBeatCount": unbound_count,
        "missingEvidenceFrameSetCount": evidence_missing_count,
        "sourcePlaybackMismatchCount": playback_mismatch_count,
        "pictureHoldOverThreeFramesCount": picture_hold_over_three_frames_count,
        "maximumPictureHoldSeconds": maximum_picture_hold_seconds,
        "masteredTimingTrimCount": mastered_timing_trim_count,
        "maximumMasteredTimingTrim": maximum_mastered_timing_trim,
        "unsafeBoundaryCount": unsafe_boundary_count,
    }

    preview = data.get("preview") or {}
    preview_path = resolve_evidence_path(args.beat_map, str(preview.get("path") or "")) if preview.get("path") else None
    preview_passed = preview.get("review_status") == "passed" and bool(preview_path and preview_path.is_file())
    metrics["lowResolutionPreviewPassed"] = preview_passed
    if not preview_passed:
        issues.append({"type": "preview-not-reviewed"})

    gates = {
        "scriptRoundtrip": metrics["scriptRoundtrip"],
        "storyPlanHashMatches": metrics["storyPlanHashMatches"],
        "eventLedgerResolved": metrics["eventLedgerResolved"],
        "exactMatchClipRatio": metrics["exactMatchClipRatio"] >= exact_clip_floor,
        "exactMatchDurationRatio": metrics["exactMatchDurationRatio"] >= exact_duration_floor,
        "exactOrContextDurationRatio": metrics["exactOrContextDurationRatio"] >= 0.90,
        "neutralDurationRatio": metrics["neutralDurationRatio"] <= 0.10,
        "visualCoverageRatio": metrics["visualCoverageRatio"] >= 0.999,
        "averageSourceClipDuration": metrics["averageSourceClipDuration"] >= average_clip_floor,
        "sourceClipUnder5SecondsCount": (
            metrics["sourceClipUnder5SecondsCount"] == 0 if no_under_five else True
        ),
        "maximumCutsPerRolling30Seconds": metrics["maximumCutsPerRolling30Seconds"] <= 4,
        "contradictionCount": metrics["contradictionCount"] == 0,
        "unboundBeatCount": metrics["unboundBeatCount"] == 0,
        "evidenceFrames": metrics["missingEvidenceFrameSetCount"] == 0,
        "sourcePlayback": metrics["sourcePlaybackMismatchCount"] == 0,
        "pictureHoldAtMostThreeFrames": metrics["pictureHoldOverThreeFramesCount"] == 0,
        "masteredTimingTrimAtMostQuarterSecond": metrics["maximumMasteredTimingTrim"] <= 0.25,
        "safeBoundaries": metrics["unsafeBoundaryCount"] == 0,
        "lowResolutionPreviewPassed": metrics["lowResolutionPreviewPassed"],
    }
    report = {
        "schema": "semantic-alignment-audit-v1",
        "video_id": data.get("video_id"),
        "status": "passed" if all(gates.values()) and not issues else "failed",
        "metrics": metrics,
        "gates": gates,
        "issues": issues,
        "inputs": {
            "beatMap": str(args.beat_map.resolve()),
            "eventLedger": str(args.event_ledger.resolve()),
            "storyPlan": str(args.story_plan.resolve()),
            "storyPlanSha256": expected_story_hash,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "metrics": metrics, "issueCount": len(issues)}, ensure_ascii=False, indent=2))
    if report["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
