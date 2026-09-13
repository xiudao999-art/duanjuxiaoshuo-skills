from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def value(row: dict, *keys: str):
    for key in keys:
        if row.get(key) is not None:
            return row[key]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a locked beat map and EDL from reviewed indexed shots.")
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--beats", type=Path, required=True)
    parser.add_argument("--reviewed", type=Path, required=True)
    parser.add_argument("--story-plan", type=Path, required=True)
    parser.add_argument("--beat-map", type=Path, required=True)
    parser.add_argument("--edl", type=Path, required=True)
    args = parser.parse_args()

    index = json.loads(args.index.read_text(encoding="utf-8-sig"))
    beat_doc = json.loads(args.beats.read_text(encoding="utf-8-sig"))
    reviewed = json.loads(args.reviewed.read_text(encoding="utf-8-sig"))
    shots = {str(value(row, "shot_id", "shotId")): row for row in index.get("shots", [])}
    episodes = {str(value(row, "episode_id", "episodeId")): row for row in index.get("episodes", [])}
    selections: dict[str, list[dict]] = defaultdict(list)
    for row in reviewed.get("selections", []):
        selections[str(value(row, "beat_id", "beatId") or "")].append(row)

    beat_rows, clip_rows, edl_rows = [], [], []
    for beat in beat_doc.get("beats", []):
        beat_id = str(value(beat, "beat_id", "beatId") or "")
        chosen = selections.get(beat_id, [])
        if not chosen:
            raise ValueError(f"No reviewed selection for beat {beat_id}")
        bindings = []
        for order, selection in enumerate(chosen, start=1):
            if selection.get("review_status") != "passed":
                raise ValueError(f"Selection for {beat_id} is not reviewed as passed")
            shot_id = str(value(selection, "shot_id", "shotId") or "")
            if shot_id not in shots:
                raise ValueError(f"Unknown shot {shot_id} for beat {beat_id}")
            shot = shots[shot_id]
            indexed_start = float(value(shot, "start", "source_start", "sourceStart"))
            indexed_end = float(value(shot, "end", "source_end", "sourceEnd"))
            source_start = float(value(selection, "source_start", "sourceStart") if value(selection, "source_start", "sourceStart") is not None else indexed_start)
            source_end = float(value(selection, "source_end", "sourceEnd") if value(selection, "source_end", "sourceEnd") is not None else indexed_end)
            if source_start < indexed_start - 1e-6 or source_end > indexed_end + 1e-6 or source_end <= source_start:
                raise ValueError(f"Reviewed range for {beat_id}/{shot_id} leaves indexed shot")
            if shot.get("safe_in") is not True or shot.get("safe_out") is not True:
                raise ValueError(f"Shot {shot_id} lacks safe reviewed boundaries")

            if len(chosen) == 1:
                coverage_start = float(value(beat, "tts_start", "ttsStart") or 0)
                coverage_end = float(value(beat, "tts_end", "ttsEnd") or 0)
            else:
                coverage_start = value(selection, "coverage_start", "coverageStart")
                coverage_end = value(selection, "coverage_end", "coverageEnd")
                if coverage_start is None or coverage_end is None:
                    raise ValueError(f"Multiple selections for {beat_id} require coverage_start/coverage_end")
                coverage_start, coverage_end = float(coverage_start), float(coverage_end)
            clip_id = f"{beat_id}-C{order:02d}"
            episode_id = str(value(shot, "episode_id", "episodeId") or "")
            clip = {
                "clip_id": clip_id,
                "shot_id": shot_id,
                "scene_id": value(shot, "scene_id", "sceneId"),
                "episode_id": episode_id,
                "episode": episodes.get(episode_id, {}).get("episode"),
                "source_path": episodes.get(episode_id, {}).get("source_path"),
                "source_start": source_start,
                "source_end": source_end,
                "timeline_start": coverage_start,
                "timeline_end": coverage_end,
                "event_ids": value(shot, "event_ids", "eventIds") or [],
                "safe_in": True,
                "safe_out": True,
                "source_playback_speed": 1.0,
                "dialogue_state": value(shot, "dialogue_state", "dialogueState"),
            }
            clip_rows.append(clip)
            edl_rows.append(clip.copy())
            bindings.append({
                "clip_id": clip_id,
                "coverage_start": coverage_start,
                "coverage_end": coverage_end,
                "match_type": selection.get("match_type"),
                "review_status": "passed",
                "contradictions": selection.get("contradictions") or [],
                "evidence_frames": selection.get("evidence_frames") or [],
                "notes": selection.get("notes", ""),
            })
        beat_rows.append({**beat, "bindings": bindings})

    beat_map = {
        "schema": "narration-beat-map-v1",
        "video_id": beat_doc.get("video_id"),
        "narrative_profile": beat_doc.get("narrative_profile"),
        "approved_narration_text": beat_doc.get("approved_narration_text", ""),
        "source_index_sha256": sha256(args.index),
        "story_plan_sha256": sha256(args.story_plan),
        "beats": beat_rows,
        "clips": clip_rows,
    }
    edl = {
        "schema": "short-drama-edl-v1",
        "video_id": beat_doc.get("video_id"),
        "source_index_sha256": beat_map["source_index_sha256"],
        "story_plan_sha256": beat_map["story_plan_sha256"],
        "clips": sorted(edl_rows, key=lambda row: (row["timeline_start"], row["clip_id"])),
    }
    for path, payload in ((args.beat_map, beat_map), (args.edl, edl)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"beat_map": str(args.beat_map), "edl": str(args.edl), "beats": len(beat_rows), "clips": len(clip_rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
