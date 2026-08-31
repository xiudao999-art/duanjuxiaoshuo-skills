#!/usr/bin/env python3
"""Extract a clean cover frame and standardize final cover dimensions with ffmpeg."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def require_binary(name: str) -> None:
    if not shutil.which(name):
        raise SystemExit(f"Required binary not found on PATH: {name}")


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def probe(path: Path) -> dict:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)["streams"][0]


def extract(args: argparse.Namespace) -> None:
    if args.source_time is None and args.output_time is None:
        raise SystemExit("Provide --source-time or --output-time")
    if args.source_time is not None and args.output_time is not None:
        raise SystemExit("Use only one of --source-time or --output-time")
    if args.speed <= 0:
        raise SystemExit("--speed must be positive")

    source_time = args.source_time
    if source_time is None:
        source_time = args.output_time * args.speed

    args.out.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{source_time:.6f}",
            "-i",
            str(args.input),
            "-frames:v",
            "1",
            "-q:v",
            str(args.quality),
            str(args.out),
        ]
    )
    info = probe(args.out)
    print(
        json.dumps(
            {
                "operation": "extract",
                "source_time": source_time,
                "output_time": args.output_time,
                "speed": args.speed,
                "output": str(args.out.resolve()),
                "width": info["width"],
                "height": info["height"],
            },
            ensure_ascii=False,
        )
    )


def finalize(args: argparse.Namespace) -> None:
    if args.width <= 0 or args.height <= 0:
        raise SystemExit("--width and --height must be positive")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    video_filter = (
        f"scale={args.width}:{args.height}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={args.width}:{args.height}"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(args.input),
            "-vf",
            video_filter,
            "-frames:v",
            "1",
            str(args.out),
        ]
    )
    info = probe(args.out)
    if info["width"] != args.width or info["height"] != args.height:
        raise SystemExit(f"Unexpected output dimensions: {info}")
    print(
        json.dumps(
            {
                "operation": "finalize",
                "output": str(args.out.resolve()),
                "width": info["width"],
                "height": info["height"],
            },
            ensure_ascii=False,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser("extract")
    extract_parser.add_argument("--input", type=Path, required=True)
    extract_parser.add_argument("--out", type=Path, required=True)
    extract_parser.add_argument("--source-time", type=float)
    extract_parser.add_argument("--output-time", type=float)
    extract_parser.add_argument("--speed", type=float, default=1.0)
    extract_parser.add_argument("--quality", type=int, default=1)
    extract_parser.set_defaults(func=extract)

    finalize_parser = subparsers.add_parser("finalize")
    finalize_parser.add_argument("--input", type=Path, required=True)
    finalize_parser.add_argument("--out", type=Path, required=True)
    finalize_parser.add_argument("--width", type=int, default=1440)
    finalize_parser.add_argument("--height", type=int, default=2560)
    finalize_parser.set_defaults(func=finalize)

    return parser


def main() -> None:
    require_binary("ffmpeg")
    require_binary("ffprobe")
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
