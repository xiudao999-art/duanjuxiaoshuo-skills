from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import wave
from pathlib import Path


REQUIRED_SUFFIXES = (
    ".wav",
    ".raw.mp3",
    ".text.json",
    ".words.json",
    ".words.response.json",
    ".mastered.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / handle.getframerate()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stage and verify an immutable narration WAV/word-timing cache."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--ids", help="Comma-separated narration IDs; defaults to every source WAV stem.")
    parser.add_argument("--output-manifest", type=Path)
    args = parser.parse_args()

    if not args.source.is_dir():
        raise FileNotFoundError(f"missing narration cache: {args.source}")
    ids = (
        [value.strip() for value in args.ids.split(",") if value.strip()]
        if args.ids
        else sorted(path.stem for path in args.source.glob("*.wav"))
    )
    if not ids:
        raise RuntimeError("no narration WAV files found")

    args.destination.mkdir(parents=True, exist_ok=True)
    rows = []
    for narration_id in ids:
        files = []
        for suffix in REQUIRED_SUFFIXES:
            source = args.source / f"{narration_id}{suffix}"
            if not source.is_file():
                raise FileNotFoundError(f"missing locked narration artifact: {source}")
            destination = args.destination / source.name
            source_hash = sha256(source)
            if not destination.is_file() or sha256(destination) != source_hash:
                shutil.copy2(source, destination)
            destination_hash = sha256(destination)
            if destination_hash != source_hash:
                raise RuntimeError(f"narration cache hash mismatch after staging: {destination}")
            files.append({
                "name": source.name,
                "bytes": destination.stat().st_size,
                "sha256": destination_hash,
            })
        wav = args.destination / f"{narration_id}.wav"
        rows.append({
            "id": narration_id,
            "duration": round(wav_duration(wav), 6),
            "files": files,
        })

    manifest = {
        "schema": "locked-narration-cache-v1",
        "source": str(args.source.resolve()),
        "destination": str(args.destination.resolve()),
        "ids": ids,
        "entries": rows,
    }
    output = args.output_manifest or (args.destination / "narration-lock-manifest.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "passed",
        "ids": ids,
        "manifest": str(output),
        "durations": {row["id"]: row["duration"] for row in rows},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
