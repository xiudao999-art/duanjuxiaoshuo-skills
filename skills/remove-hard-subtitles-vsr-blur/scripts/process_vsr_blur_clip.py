from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


REFERENCE_WIDTH = 1080
REFERENCE_HEIGHT = 1920
DEFAULT_VSR_ROOT = Path(r"D:\codex\短剧剪辑\tools\video-subtitle-remover")


def run(command: list[str]) -> None:
    print(" ".join(command), flush=True)
    subprocess.run(command, check=True)


def probe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,sample_aspect_ratio,r_frame_rate",
            "-of", "json", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    streams = json.loads(result.stdout).get("streams") or []
    if len(streams) != 1:
        raise RuntimeError(f"expected one video stream: {path}")
    return streams[0]


def scaled_mask(mask: list[int], width: int, height: int) -> list[int]:
    ymin, ymax, xmin, xmax = mask
    values = [
        round(ymin * height / REFERENCE_HEIGHT),
        round(ymax * height / REFERENCE_HEIGHT),
        round(xmin * width / REFERENCE_WIDTH),
        round(xmax * width / REFERENCE_WIDTH),
    ]
    symin, symax, sxmin, sxmax = values
    if not (0 <= symin < symax < height and 0 <= sxmin < sxmax < width):
        raise RuntimeError(f"scaled mask is outside {width}x{height}: {values}")
    return values


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove burned subtitles with VSR/STTN and add a full-width blur-only one-line rail."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--mask", nargs=4, type=int, action="append", metavar=("YMIN", "YMAX", "XMIN", "XMAX"),
        default=None, help="Reviewed 1080x1920-normalized STTN mask; repeat for multiple rectangles.",
    )
    parser.add_argument("--rail-y", type=int, default=1318)
    parser.add_argument("--rail-height", type=int, default=90)
    parser.add_argument("--blur-sigma", type=float, default=28.0)
    parser.add_argument("--vsr-root", type=Path, default=DEFAULT_VSR_ROOT)
    parser.add_argument("--already-inpainted", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.input.exists():
        raise RuntimeError(f"input does not exist: {args.input}")
    if args.input.resolve() == args.output.resolve():
        raise RuntimeError("input and output must be different paths")
    masks = args.mask or [[1275, 1415, 0, 1079]]
    if not 2.0 <= args.blur_sigma <= 60.0:
        raise RuntimeError("blur sigma must be between 2 and 60")
    if args.rail_height <= 0:
        raise RuntimeError("rail height must be positive")

    source = probe(args.input)
    width = int(source["width"])
    height = int(source["height"])
    if abs(width / height - 9 / 16) > 0.01:
        raise RuntimeError(f"source must be 9:16 before subtitle repair: {width}x{height}")

    actual_masks = [scaled_mask(mask, width, height) for mask in masks]
    rail_y = round(args.rail_y * height / REFERENCE_HEIGHT)
    rail_height = round(args.rail_height * height / REFERENCE_HEIGHT)
    if not (0 <= rail_y < rail_y + rail_height <= height):
        raise RuntimeError("blur rail is outside the frame")

    plan = {
        "input": str(args.input.resolve()),
        "output": str(args.output.resolve()),
        "source": source,
        "mode": "already-inpainted" if args.already_inpainted else "sttn-auto",
        "normalizedMasks": masks,
        "actualMasks": actual_masks,
        "rail": {
            "x": 0,
            "y": rail_y,
            "width": width,
            "height": rail_height,
            "blurSigma": args.blur_sigma,
            "darkOpacity": 0.0,
        },
        "preserveOriginalComposition": True,
    }
    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vsr-blur-") as temp_name:
        temp_dir = Path(temp_name)
        inpainted = args.input if args.already_inpainted else temp_dir / "sttn-inpainted.mp4"
        if not args.already_inpainted:
            vsr_python = args.vsr_root / ".venv-gpu" / "Scripts" / "python.exe"
            vsr_main = args.vsr_root / "backend" / "main.py"
            if not vsr_python.exists() or not vsr_main.exists():
                raise RuntimeError(f"VSR/STTN runtime missing under {args.vsr_root}")
            command = [str(vsr_python), str(vsr_main), "-i", str(args.input), "-o", str(inpainted)]
            for mask in actual_masks:
                command += ["-c", *[str(value) for value in mask]]
            command += ["--inpaint-mode", "sttn-auto"]
            run(command)

        filter_graph = (
            f"[0:v]split=2[base][band];"
            f"[band]crop={width}:{rail_height}:0:{rail_y},"
            f"gblur=sigma={args.blur_sigma:.2f}:steps=3[blurred];"
            f"[base][blurred]overlay=0:{rail_y},setsar=1,format=yuv420p[vout]"
        )
        run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(inpainted), "-filter_complex", filter_graph,
            "-map", "[vout]", "-map", "0:a?", "-c:v", "libx264",
            "-preset", "veryfast", "-crf", "16", "-c:a", "copy",
            "-movflags", "+faststart", str(args.output),
        ])

    result = probe(args.output)
    if int(result["width"]) != width or int(result["height"]) != height:
        raise RuntimeError(f"output dimensions changed: {result}")
    sidecar = args.output.with_suffix(args.output.suffix + ".vsr-blur.json")
    sidecar.write_text(json.dumps(plan | {"result": result}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "manifest": str(sidecar)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
