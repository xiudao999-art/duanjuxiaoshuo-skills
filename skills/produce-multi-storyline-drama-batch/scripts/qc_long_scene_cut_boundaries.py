from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def read_frame(cap: cv2.VideoCapture, seconds: float) -> np.ndarray:
    cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, seconds) * 1000.0)
    ok, frame = cap.read()
    if not ok:
        raise RuntimeError(f"cannot decode frame at {seconds:.3f}s")
    return frame


def distance(a: np.ndarray, b: np.ndarray) -> float:
    aa = cv2.resize(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), (96, 54))
    bb = cv2.resize(cv2.cvtColor(b, cv2.COLOR_BGR2GRAY), (96, 54))
    return float(np.mean(np.abs(aa.astype(np.float32) - bb.astype(np.float32))) / 255.0)


def collect_cuts(job: dict, audit: list[dict]) -> list[dict]:
    cuts: list[dict] = []
    timeline = job["timeline"]
    for left, right in zip(timeline, timeline[1:]):
        cuts.append({
            "time": float(left["timelineEnd"]),
            "kind": "block",
            "label": f"{left.get('type')} -> {right.get('type')}",
        })
    narration_starts = {
        item.get("id"): float(item["timelineStart"])
        for item in timeline
        if item.get("type") == "narration"
    }
    for block in audit:
        elapsed = 0.0
        clips = block["clips"]
        for index, clip in enumerate(clips[:-1]):
            elapsed += float(clip["clip_duration"])
            cuts.append({
                "time": narration_starts[block["block"]] + elapsed,
                "kind": "picture",
                "label": (
                    f"{block['block']} {clip['scene_id']} -> "
                    f"{clips[index + 1]['scene_id']}"
                ),
            })
    return sorted(cuts, key=lambda item: item["time"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument(
        "--production-root",
        type=Path,
        help="Optional isolated production cache containing recap-* directories.",
    )
    args = parser.parse_args()
    font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 19)
    small = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 16)
    offsets = [-1.5, -0.12, -0.08, -0.04, 0.0, 0.04, 0.08, 0.12, 1.5]
    all_results = []
    production_root = args.production_root or (args.output_root / "recap-production")
    productions = sorted(
        path for path in production_root.glob("recap-*")
        if path.is_dir() and (path / "job.json").is_file() and (path / "broll-audit.json").is_file()
    )
    if not productions:
        raise RuntimeError(f"no completed recap production directories found under {production_root}")
    for production in productions:
        recap_id = production.name
        delivery = next((args.output_root / "deliveries" / recap_id).glob("*.mp4"))
        job = json.loads((production / "job.json").read_text(encoding="utf-8-sig"))
        audit = json.loads((production / "broll-audit.json").read_text(encoding="utf-8-sig"))
        cuts = collect_cuts(job, audit)
        cap = cv2.VideoCapture(str(delivery))
        duration = float(job["totalDurationOutput"])
        rows = []
        flash_candidates = []
        for cut_index, cut in enumerate(cuts):
            frames = [read_frame(cap, min(duration - 0.04, cut["time"] + offset)) for offset in offsets]
            local = frames[2:8]
            distances = [distance(a, b) for a, b in zip(local, local[1:])]
            triplet_flags = []
            for i in range(1, len(local) - 1):
                left = distance(local[i - 1], local[i])
                right = distance(local[i], local[i + 1])
                bridge = distance(local[i - 1], local[i + 1])
                if left > 0.26 and right > 0.26 and bridge < 0.11:
                    triplet_flags.append(i)
            if triplet_flags:
                flash_candidates.append({"cut": cut_index + 1, "time": cut["time"], "frames": triplet_flags})
            rows.append((cut, frames, distances))
        cap.release()

        thumb_w, thumb_h, header = 150, 267, 60
        canvas = Image.new("RGB", (thumb_w * len(offsets), (thumb_h + header) * len(rows)), "#111111")
        draw = ImageDraw.Draw(canvas)
        for row_index, (cut, frames, distances) in enumerate(rows):
            y = row_index * (thumb_h + header)
            draw.text((8, y + 4), f"#{row_index + 1:02d} {cut['time']:.3f}s {cut['kind']} {cut['label']}", font=font, fill="white")
            draw.text((8, y + 31), "adjacent diff " + " ".join(f"{v:.3f}" for v in distances), font=small, fill="#ffe680")
            for column, (offset, frame) in enumerate(zip(offsets, frames)):
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(rgb)
                image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
                x = column * thumb_w + (thumb_w - image.width) // 2
                py = y + header + (thumb_h - image.height) // 2
                canvas.paste(image, (x, py))
                draw.text((column * thumb_w + 4, y + header + 3), f"{offset:+.2f}", font=small, fill="#b8ff2f", stroke_width=2, stroke_fill="black")
        qc_dir = production / "qc"
        qc_dir.mkdir(parents=True, exist_ok=True)
        sheet = qc_dir / "encoded-cut-boundary-contact-sheet.jpg"
        canvas.save(sheet, quality=89)
        result = {
            "recap": recap_id,
            "delivery": str(delivery),
            "cutCount": len(cuts),
            "flashCandidates": flash_candidates,
            "status": "passed" if not flash_candidates else "review",
            "contactSheet": str(sheet),
            "cuts": cuts,
        }
        (qc_dir / "encoded-cut-boundary-audit.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        all_results.append(result)
        print(json.dumps({k: result[k] for k in ("recap", "cutCount", "flashCandidates", "status")}, ensure_ascii=False))
    (args.output_root / "encoded-cut-boundary-summary.json").write_text(
        json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
