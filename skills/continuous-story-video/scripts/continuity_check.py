#!/usr/bin/env python3
"""Extract contact sheets and frame-diff peaks for video continuity QA."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


def parse_range(value: str) -> tuple[float, float]:
    if ":" not in value:
        raise argparse.ArgumentTypeError("range must be start:end seconds")
    start_s, end_s = value.split(":", 1)
    start = float(start_s)
    end = float(end_s)
    if end <= start:
        raise argparse.ArgumentTypeError("range end must be greater than start")
    return start, end


def run_ffmpeg(args: list[str]) -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg was not found on PATH")
    proc = subprocess.run(["ffmpeg", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr)


def extract_frames(video: Path, start: float, end: float, fps: float, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("frame_*.jpg"):
        old.unlink()
    run_ffmpeg(
        [
            "-y",
            "-ss",
            f"{start:.3f}",
            "-i",
            str(video),
            "-t",
            f"{end - start:.3f}",
            "-vf",
            f"fps={fps},scale=96:-1",
            str(out_dir / "frame_%05d.jpg"),
        ]
    )
    return sorted(out_dir.glob("frame_*.jpg"))


def mean_abs_diff(a: Image.Image, b: Image.Image) -> float:
    left = a.convert("RGB")
    right = b.convert("RGB")
    if left.size != right.size:
        raise ValueError("frame sizes differ")
    stat = ImageStat.Stat(ImageChops.difference(left, right))
    return sum(stat.mean) / len(stat.mean)


def make_sheet(frames: list[Path], out_path: Path, max_width: int = 3600) -> None:
    if not frames:
        return
    images = [Image.open(p).convert("RGB") for p in frames]
    w, h = images[0].size
    cols = max(1, min(len(images), max_width // w))
    rows = math.ceil(len(images) / cols)
    sheet = Image.new("RGB", (cols * w, rows * h), "white")
    for idx, img in enumerate(images):
        sheet.paste(img, ((idx % cols) * w, (idx // cols) * h))
    sheet.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--range", dest="ranges", required=True, action="append", type=parse_range)
    parser.add_argument("--fps", type=float, default=12.0, help="fps for frame-diff analysis")
    parser.add_argument("--sheet-fps", type=float, default=8.0, help="fps for visual contact sheet")
    parser.add_argument("--out-dir", type=Path, default=Path("continuity-checks"))
    parser.add_argument("--top", type=int, default=12)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = []

    for index, (start, end) in enumerate(args.ranges, 1):
        tag = f"{start:g}-{end:g}".replace(".", "p")
        frame_dir = args.out_dir / f"frames_{index}_{tag}"
        frames = extract_frames(args.video, start, end, args.fps, frame_dir)
        diffs = []
        previous = None
        for i, frame_path in enumerate(frames):
            image = Image.open(frame_path)
            if previous is not None:
                diffs.append({"time": start + i / args.fps, "diff": mean_abs_diff(previous, image)})
            previous = image

        sheet_dir = args.out_dir / f"sheet_frames_{index}_{tag}"
        sheet_frames = extract_frames(args.video, start, end, args.sheet_fps, sheet_dir)
        sheet_path = args.out_dir / f"sheet_{index}_{tag}.jpg"
        make_sheet(sheet_frames, sheet_path)

        top = sorted(diffs, key=lambda row: row["diff"], reverse=True)[: args.top]
        report.append(
            {
                "range": [start, end],
                "analysis_fps": args.fps,
                "sheet": str(sheet_path),
                "top_diffs": top,
            }
        )

        print(f"Range {start:g}-{end:g}s")
        print(f"  sheet: {sheet_path}")
        for row in top:
            print(f"  {row['time']:.3f}s diff={row['diff']:.2f}")

    report_path = args.out_dir / "continuity_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
