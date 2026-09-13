from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_rows(path: Path) -> list[dict]:
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    value = load_json(path)
    if isinstance(value, list):
        return value
    for key in ("rows", "items", path.stem.replace("-", "_")):
        if isinstance(value, dict) and isinstance(value.get(key), list):
            return value[key]
    raise ValueError(f"{path} does not contain a row list")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble reviewed short-drama index components.")
    parser.add_argument("--episodes", type=Path, required=True)
    parser.add_argument("--utterances", type=Path, required=True)
    parser.add_argument("--characters", type=Path, required=True)
    parser.add_argument("--scenes", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--shots", type=Path, required=True)
    parser.add_argument("--story-graph", type=Path, required=True)
    parser.add_argument("--series-id", default="")
    parser.add_argument("--title", default="")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    paths = {
        "episodes": args.episodes,
        "utterances": args.utterances,
        "characters": args.characters,
        "scenes": args.scenes,
        "events": args.events,
        "shots": args.shots,
        "story_graph": args.story_graph,
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing index components: " + ", ".join(missing))

    characters_value = load_json(args.characters)
    characters = characters_value if isinstance(characters_value, list) else characters_value.get("characters", [])
    payload = {
        "schema": "short-drama-source-index-v1",
        "series_id": args.series_id,
        "title": args.title,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "episodes": load_rows(args.episodes),
        "utterances": load_rows(args.utterances),
        "characters": characters,
        "scenes": load_rows(args.scenes),
        "events": load_rows(args.events),
        "shots": load_rows(args.shots),
        "story_graph": load_json(args.story_graph),
        "component_hashes": {name: sha256(path) for name, path in paths.items()},
        "component_paths": {name: str(path.resolve()) for name, path in paths.items()},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    counts = {key: len(payload[key]) for key in ("episodes", "utterances", "characters", "scenes", "events", "shots")}
    print(json.dumps({"output": str(args.output), "counts": counts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
