from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def values(row: dict, *keys: str) -> list[str]:
    for key in keys:
        value = row.get(key)
        if value is not None:
            if isinstance(value, list):
                return [str(item).strip() for item in value if str(item).strip()]
            return [str(value).strip()] if str(value).strip() else []
    return []


def tokens(value) -> set[str]:
    text = " ".join(value if isinstance(value, list) else [str(value or "")])
    return {part for part in re.split(r"[\s,，。；;、/|]+", text) if part}


def overlap_score(required, actual, weight: float) -> float:
    need, have = tokens(required), tokens(actual)
    if not need:
        return 0.0
    return weight * len(need & have) / len(need)


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank indexed shots for event-bound script beats.")
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--beats", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=8)
    args = parser.parse_args()

    index = json.loads(args.index.read_text(encoding="utf-8-sig"))
    beat_doc = json.loads(args.beats.read_text(encoding="utf-8-sig"))
    shots = index.get("shots", [])
    results = []

    for beat in beat_doc.get("beats", []):
        beat_id = str(beat.get("beat_id") or "")
        required_events = set(values(beat, "event_ids", "eventIds"))
        if beat.get("factual", True) and not required_events:
            results.append({"beat_id": beat_id, "status": "unresolved-story-binding", "candidates": []})
            continue

        direct = [shot for shot in shots if required_events & set(values(shot, "event_ids", "eventIds"))]
        direct_scenes = {str(shot.get("scene_id") or shot.get("sceneId") or "") for shot in direct}
        pool = [
            shot for shot in shots
            if shot in direct or str(shot.get("scene_id") or shot.get("sceneId") or "") in direct_scenes
        ]
        requirements = beat.get("requirements") or {}
        ranked = []
        for shot in pool:
            shot_events = set(values(shot, "event_ids", "eventIds"))
            direct_event = bool(required_events & shot_events)
            score = 55.0 if direct_event else 22.0
            score += overlap_score(requirements.get("characters", []), values(shot, "characters"), 16.0)
            score += overlap_score(requirements.get("action", ""), values(shot, "action"), 8.0)
            score += overlap_score(requirements.get("location", ""), values(shot, "location"), 7.0)
            score += overlap_score(requirements.get("time_state", ""), values(shot, "time_state", "timeState"), 5.0)
            score += overlap_score(requirements.get("emotion", ""), values(shot, "emotion"), 3.0)
            score += overlap_score(requirements.get("objects", []), values(shot, "objects"), 3.0)
            if shot.get("safe_in") is True and shot.get("safe_out") is True:
                score += 4.0
            try:
                score += max(0.0, min(1.0, float(shot.get("visual_quality", 0)))) * 4.0
            except (TypeError, ValueError):
                pass
            ranked.append({
                "shot_id": shot.get("shot_id") or shot.get("shotId"),
                "scene_id": shot.get("scene_id") or shot.get("sceneId"),
                "episode_id": shot.get("episode_id") or shot.get("episodeId"),
                "start": shot.get("start", shot.get("source_start")),
                "end": shot.get("end", shot.get("source_end")),
                "event_ids": values(shot, "event_ids", "eventIds"),
                "candidate_type": "exact-event" if direct_event else "same-scene-context",
                "score": round(score, 3),
                "requires_visual_review": True,
            })
        ranked.sort(key=lambda row: (-row["score"], str(row["shot_id"])))
        results.append({
            "beat_id": beat_id,
            "status": "candidates-found" if ranked else "no-indexed-evidence",
            "required_event_ids": sorted(required_events),
            "candidates": ranked[: max(1, args.top_k)],
        })

    output = {"schema": "short-drama-binding-candidates-v1", "video_id": beat_doc.get("video_id"), "beats": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    unresolved = sum(row["status"] != "candidates-found" for row in results)
    print(json.dumps({"output": str(args.output), "beats": len(results), "unresolved": unresolved}, ensure_ascii=False))
    return 0 if unresolved == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
