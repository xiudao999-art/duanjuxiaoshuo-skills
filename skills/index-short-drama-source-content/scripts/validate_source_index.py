from __future__ import annotations

import argparse
import json
from pathlib import Path


ID_FIELDS = {
    "episodes": "episode_id",
    "utterances": "utterance_id",
    "characters": "character_id",
    "scenes": "scene_id",
    "events": "event_id",
    "shots": "shot_id",
}


def number(row: dict, *keys: str) -> float | None:
    for key in keys:
        if row.get(key) is not None:
            try:
                return float(row[key])
            except (TypeError, ValueError):
                return None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a short-drama source content index.")
    parser.add_argument("index", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    data = json.loads(args.index.read_text(encoding="utf-8-sig"))
    issues: list[dict] = []
    if data.get("schema") != "short-drama-source-index-v1":
        issues.append({"type": "schema", "message": "expected short-drama-source-index-v1"})

    ids: dict[str, set[str]] = {}
    for group, field in ID_FIELDS.items():
        rows = data.get(group)
        if not isinstance(rows, list):
            issues.append({"type": "missing-group", "group": group})
            rows = []
        values = [str(row.get(field) or "").strip() for row in rows if isinstance(row, dict)]
        missing = [i for i, value in enumerate(values) if not value]
        duplicates = sorted({value for value in values if value and values.count(value) > 1})
        if missing:
            issues.append({"type": "missing-id", "group": group, "rows": missing})
        if duplicates:
            issues.append({"type": "duplicate-id", "group": group, "ids": duplicates})
        ids[group] = {value for value in values if value}

    episode_duration = {
        str(row.get("episode_id")): number(row, "duration")
        for row in data.get("episodes", [])
        if isinstance(row, dict)
    }
    for group in ("utterances", "scenes", "shots"):
        for row in data.get(group, []):
            row_id = str(row.get(ID_FIELDS[group]) or "")
            episode_id = str(row.get("episode_id") or "")
            start, end = number(row, "start", "source_start"), number(row, "end", "source_end")
            if episode_id not in ids["episodes"]:
                issues.append({"type": "unknown-episode", "group": group, "id": row_id, "episode_id": episode_id})
            if start is None or end is None or start < 0 or end <= start:
                issues.append({"type": "invalid-range", "group": group, "id": row_id, "start": start, "end": end})
            elif episode_duration.get(episode_id) is not None and end > episode_duration[episode_id] + 0.12:
                issues.append({"type": "range-outside-episode", "group": group, "id": row_id, "end": end})

    for shot in data.get("shots", []):
        shot_id = str(shot.get("shot_id") or "")
        if str(shot.get("scene_id") or "") not in ids["scenes"]:
            issues.append({"type": "unknown-scene", "shot_id": shot_id})
        if shot.get("safe_in") is not True or shot.get("safe_out") is not True:
            issues.append({"type": "unreviewed-shot-boundary", "shot_id": shot_id})
        if not str(shot.get("dialogue_state") or "").strip():
            issues.append({"type": "missing-dialogue-state", "shot_id": shot_id})
        unknown = sorted(set(map(str, shot.get("event_ids") or [])) - ids["events"])
        if unknown:
            issues.append({"type": "shot-unknown-event", "shot_id": shot_id, "event_ids": unknown})

    for event in data.get("events", []):
        event_id = str(event.get("event_id") or "")
        evidence = event.get("evidence") or []
        if not evidence:
            issues.append({"type": "event-without-evidence", "event_id": event_id})
        for item in evidence:
            if str(item.get("episode_id") or "") not in ids["episodes"]:
                issues.append({"type": "event-evidence-unknown-episode", "event_id": event_id})
            if not any(item.get(key) for key in ("scene_id", "shot_id", "utterance_id")):
                issues.append({"type": "event-evidence-without-record", "event_id": event_id})
            for key, group in (("scene_id", "scenes"), ("shot_id", "shots"), ("utterance_id", "utterances")):
                ref = str(item.get(key) or "")
                if ref and ref not in ids[group]:
                    issues.append({"type": "event-evidence-unknown-record", "event_id": event_id, "field": key, "id": ref})

    audit = {
        "schema": "short-drama-source-index-audit-v1",
        "status": "passed" if not issues else "failed",
        "counts": {group: len(data.get(group, [])) for group in ID_FIELDS},
        "issues": issues,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
