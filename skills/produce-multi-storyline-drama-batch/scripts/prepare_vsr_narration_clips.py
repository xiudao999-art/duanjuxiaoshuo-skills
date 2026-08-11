from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import time
from collections import defaultdict
from pathlib import Path


WIDTH = 1080
HEIGHT = 1920
FPS = 25

SHORT_DRAMA_SUBTITLE_STYLE = "short-drama-vsr-tight-rail-1080x1920"
SHORT_DRAMA_RAIL = {
    "enabled": True,
    "mode": "fullwidth-tight-gaussian-blur-only",
    "x": 0,
    "y": 1318,
    "width": 1080,
    "height": 90,
    "blurSigma": 28,
    "blurSteps": 3,
    "darkOpacity": 0.0,
    "captionBaseline": 1385,
    "targetVerticalPaddingPx": [6, 12],
}
SHORT_DRAMA_CAPTION_STYLE = {
    "normalSize": 64,
    "accentSize": 64,
    "highlightSize": 64,
    "maxWidth": 920,
    "weight": 850,
    "edgeWidth": 1.15,
    "shadowStroke": 1.5,
}


def resolve_short_drama_rail(config: dict) -> dict:
    """Resolve the visible rail independently from the STTN mask map."""
    cover = ((config.get("output") or {}).get("narrationSourceSubtitleCover") or {})
    configured = cover.get("rail")
    rail = dict(SHORT_DRAMA_RAIL)
    if isinstance(configured, dict):
        rail.update(configured)
    expected = {
        "enabled": True, "x": 0, "y": 1318, "width": 1080, "height": 90,
        "blurSigma": 28.0, "darkOpacity": 0.0, "captionBaseline": 1385,
    }
    actual = {
        "enabled": bool(rail.get("enabled", True)),
        "x": int(rail.get("x", 0)), "y": int(rail.get("y", 1318)),
        "width": int(rail.get("width", 1080)), "height": int(rail.get("height", 90)),
        "blurSigma": float(rail.get("blurSigma", 28.0)),
        "darkOpacity": float(rail.get("darkOpacity", 0.0)),
        "captionBaseline": int(rail.get("captionBaseline", 1385)),
    }
    if actual != expected:
        raise RuntimeError(
            "short-drama subtitle rail differs from the locked global profile; "
            f"expected={expected} actual={actual}"
        )
    baseline = int(config.get("caption_baseline_px", 1385))
    if baseline != 1385:
        raise RuntimeError(f"short-drama caption baseline must be 1385, got {baseline}")
    rail.update(actual)
    return rail


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(command: list[str], cwd: Path | None = None) -> None:
    print(" ".join(command), flush=True)
    subprocess.run(command, cwd=str(cwd) if cwd else None, check=True)


def stream_types(path: Path) -> set[str]:
    if not path.exists() or path.stat().st_size < 1024:
        return set()
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "stream=codec_type",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def frame_count(path: Path) -> int:
    if "video" not in stream_types(path):
        return 0
    metadata = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=nb_frames", "-of", "default=nw=1:nk=1", str(path),
        ],
        capture_output=True, text=True, check=False, encoding="utf-8",
    )
    value = metadata.stdout.strip()
    if value.isdigit():
        return int(value)
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
            "-show_entries", "stream=nb_read_frames", "-of", "default=nw=1:nk=1", str(path),
        ],
        capture_output=True, text=True, check=True, encoding="utf-8",
    )
    return int(result.stdout.strip())


def wait_for_gpu_memory(max_used_mib: int, poll_seconds: int, stable_polls: int) -> None:
    consecutive = 0
    while True:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, check=False, encoding="utf-8",
        )
        try:
            used = max(int(line.strip()) for line in result.stdout.splitlines() if line.strip())
        except (ValueError, TypeError):
            print("GPU memory query unavailable; attempting STTN without a wait", flush=True)
            return
        if used <= max_used_mib:
            consecutive += 1
            print(f"GPU candidate idle: {used} MiB ({consecutive}/{stable_polls})", flush=True)
            if consecutive >= stable_polls:
                print(f"GPU memory stably ready: {used} MiB <= {max_used_mib} MiB", flush=True)
                return
        else:
            consecutive = 0
            print(f"GPU busy: {used} MiB > {max_used_mib} MiB; waiting {poll_seconds}s", flush=True)
        time.sleep(poll_seconds)


def ensure_silent_audio(video_only: Path, output: Path) -> None:
    """Give VSR a valid AAC track; its backend always attempts audio recovery."""
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(video_only), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-map", "0:v:0", "-map", "1:a:0", "-shortest", "-c:v", "copy",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(output),
    ])


def source_for_episode(root: Path, episode: int) -> Path:
    candidates = list(dict.fromkeys([root / f"{episode}.mp4", root / f"{episode:02d}.mp4"]))
    matches = [path for path in candidates if path.exists()]
    if len(matches) != 1:
        raise RuntimeError(f"episode {episode} source is not unique: {matches}")
    return matches[0]


def masks_for_episode(mask_map: dict, episode: int) -> list[list[int]]:
    masks = (mask_map.get("episodes") or {}).get(str(episode), mask_map.get("defaultMasks"))
    if not masks:
        raise RuntimeError(f"episode {episode} has no reviewed VSR mask")
    result = []
    for mask in masks:
        if len(mask) != 4:
            raise RuntimeError(f"invalid mask for episode {episode}: {mask}")
        ymin, ymax, xmin, xmax = [int(value) for value in mask]
        if not (0 <= ymin < ymax < HEIGHT and 0 <= xmin < xmax < WIDTH):
            raise RuntimeError(f"out-of-bounds mask for episode {episode}: {mask}")
        result.append([ymin, ymax, xmin, xmax])
    return result


def clip_key(episode: int, start: float, end: float, masks: list[list[int]]) -> str:
    payload = json.dumps(
        {"episode": episode, "start": round(start, 3), "end": round(end, 3), "masks": masks},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def rail_filter(rail: dict) -> str:
    x = int(rail.get("x", 0))
    y = int(rail.get("y", 1318))
    width = int(rail.get("width", 1080))
    height = int(rail.get("height", 90))
    blur_sigma = min(60.0, max(2.0, float(rail.get("blurSigma", 28.0))))
    opacity = min(0.85, max(0.0, float(rail.get("darkOpacity", 0.0))))
    if x < 0 or y < 0 or width <= 0 or height <= 0 or x + width > WIDTH or y + height > HEIGHT:
        raise RuntimeError(f"invalid residual rail geometry: {rail}")
    tint = (
        f"[mosaic]drawbox=x={x}:y={y}:w={width}:h={height}:"
        f"color=black@{opacity:.3f}:t=fill,setsar=1,format=yuv420p[vout]"
        if opacity > 0
        else "[mosaic]setsar=1,format=yuv420p[vout]"
    )
    return (
        f"[0:v]split=2[base][band];"
        f"[band]crop={width}:{height}:{x}:{y},"
        f"gblur=sigma={blur_sigma:.2f}:steps=3[blurred];"
        f"[base][blurred]overlay={x}:{y}[mosaic];"
        f"{tint}"
    )


def merge_overlapping_clips(clips: list[dict], gap_tolerance: float = 0.04) -> list[dict]:
    """Merge overlapping source ranges before the expensive STTN pass.

    The final bindings still point to every exact reviewed EDL range.  This
    only removes duplicated model work when several recap jobs reuse or nest
    the same source footage.
    """
    merged: list[dict] = []
    for clip in sorted(clips, key=lambda item: (int(item["episode"]), float(item["start"]), float(item["end"]))):
        episode = int(clip["episode"])
        start = float(clip["start"])
        end = float(clip["end"])
        if (
            merged
            and int(merged[-1]["episode"]) == episode
            and start <= float(merged[-1]["end"]) + gap_tolerance
        ):
            merged[-1]["end"] = max(float(merged[-1]["end"]), end)
            merged[-1]["clips"].append(clip)
        else:
            merged.append({"episode": episode, "start": start, "end": end, "clips": [clip]})
    return merged


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("--mask-map", type=Path, required=True)
    parser.add_argument("--output-config", type=Path, required=True)
    parser.add_argument("--vsr-root", type=Path, default=Path(r"D:\codex\短剧剪辑\tools\video-subtitle-remover"))
    parser.add_argument("--work-root", type=Path, help="Optional VSR scratch root on a volume with sufficient free space.")
    parser.add_argument("--max-batch-frames", type=int, default=450, help="Maximum frames per STTN invocation.")
    parser.add_argument("--max-idle-gpu-memory-mib", type=int, default=1800)
    parser.add_argument("--gpu-poll-seconds", type=int, default=20)
    parser.add_argument("--gpu-stable-polls", type=int, default=4)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.max_batch_frames < 100:
        raise RuntimeError("--max-batch-frames must be at least 100")

    config = load(args.config)
    mask_map = load(args.mask_map)
    review_status = str(mask_map.get("reviewStatus", "")).strip().lower()
    review_evidence = Path(str(mask_map.get("reviewEvidence", "")).strip())
    if not review_status.startswith("reviewed"):
        raise RuntimeError("VSR mask map has not passed representative-frame review")
    if not str(review_evidence) or not review_evidence.exists():
        raise RuntimeError(f"VSR mask review evidence is missing: {review_evidence}")
    source_root = Path(config["source_root"])
    work_root = args.work_root or (Path(config["production_scratch_root"]) / "vsr-sttn-narration")
    raw_root = work_root / "raw"
    batch_root = work_root / "batches"
    cleaned_root = work_root / "cleaned-with-rail"
    vsr_python = args.vsr_root / ".venv-gpu" / "Scripts" / "python.exe"
    vsr_main = args.vsr_root / "backend" / "main.py"
    if not vsr_python.exists() or not vsr_main.exists():
        raise RuntimeError(f"VSR/STTN runtime missing under {args.vsr_root}")

    bindings = []
    unique = {}
    rail = resolve_short_drama_rail(config)
    for job in config["jobs"]:
        manual = job.get("manual_broll") or {}
        for block_id, specs in manual.items():
            for spec_index, spec in enumerate(specs):
                episode = int(spec["episode"])
                start = float(spec["start"])
                end = float(spec.get("end", start + float(spec.get("duration", 0))))
                if end <= start:
                    raise RuntimeError(f"invalid final EDL range: job={job['number']} {block_id} {spec}")
                masks = masks_for_episode(mask_map, episode)
                key = clip_key(episode, start, end, masks)
                unique.setdefault(key, {
                    "key": key,
                    "episode": episode,
                    "start": start,
                    "end": end,
                    "duration": end - start,
                    "masks": masks,
                })
                bindings.append((job, block_id, spec_index, key))

    groups = defaultdict(list)
    for clip in unique.values():
        groups[json.dumps(clip["masks"], sort_keys=True)].append(clip)

    plan = {
        "schema": "vsr-sttn-narration-plan-v1",
        "tool": str(args.vsr_root),
        "mode": "sttn-auto",
        "preserveOriginalComposition": True,
        "maskReviewStatus": mask_map["reviewStatus"],
        "maskReviewEvidence": str(review_evidence),
        "clipCount": len(unique),
        "groupCount": len(groups),
        "groups": [],
    }
    if args.dry_run:
        for group_index, clips in enumerate(groups.values(), 1):
            plan["groups"].append({
                "group": group_index,
                "masks": clips[0]["masks"],
                "clips": [{key: value for key, value in clip.items() if key != "masks"} for clip in clips],
            })
        dump(args.output_config.with_suffix(".vsr-plan.json"), plan)
        print(json.dumps({"dryRun": True, "clips": len(unique), "groups": len(groups)}, ensure_ascii=False))
        return

    raw_root.mkdir(parents=True, exist_ok=True)
    batch_root.mkdir(parents=True, exist_ok=True)
    cleaned_root.mkdir(parents=True, exist_ok=True)
    cleaned_paths = {}
    executed_batch_count = 0
    for group_index, clips in enumerate(groups.values(), 1):
        merged_ranges = merge_overlapping_clips(clips)
        entries = []
        for range_index, merged in enumerate(merged_ranges, 1):
            range_duration = float(merged["end"]) - float(merged["start"])
            range_frames = max(1, round(range_duration * FPS))
            raw = raw_root / f"group-{group_index:02d}-range-{range_index:03d}.mp4"
            if not raw.exists() or frame_count(raw) != range_frames:
                run([
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-ss", f"{merged['start']:.3f}", "-i", str(source_for_episode(source_root, merged["episode"])),
                    "-vf", (
                        f"fps={FPS},scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease:flags=lanczos,"
                        f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:black,setsar=1"
                    ),
                    "-frames:v", str(range_frames), "-an", "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "14", "-pix_fmt", "yuv420p", str(raw),
                ])
            raw_frames = frame_count(raw)
            source_terminal_clamp_frames = range_frames - raw_frames
            if not (0 <= source_terminal_clamp_frames <= 3):
                raise RuntimeError(
                    f"source range frame mismatch: {raw} expected={range_frames} actual={raw_frames}"
                )
            entries.append({
                "rangeIndex": range_index,
                "merged": merged,
                "raw": raw,
                "frames": raw_frames,
                "plannedFrames": range_frames,
                "sourceTerminalClampFrames": source_terminal_clamp_frames,
            })

        chunks = []
        for entry in entries:
            if not chunks or sum(item["frames"] for item in chunks[-1]) + entry["frames"] > args.max_batch_frames:
                chunks.append([])
            chunks[-1].append(entry)

        for chunk_index, chunk in enumerate(chunks, 1):
            executed_batch_count += 1
            prefix = f"group-{group_index:02d}-chunk-{chunk_index:03d}"
            list_file = batch_root / f"{prefix}.txt"
            list_file.write_text("\n".join(f"file '{item['raw'].as_posix()}'" for item in chunk) + "\n", encoding="utf-8")
            before_video = batch_root / f"{prefix}-before-video.mp4"
            before = batch_root / f"{prefix}-before.mp4"
            sttn = batch_root / f"{prefix}-sttn.mp4"
            expected_frames = sum(item["frames"] for item in chunk)
            if frame_count(before_video) != expected_frames:
                run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-an", "-c", "copy", str(before_video)])
            if frame_count(before) != expected_frames or stream_types(before) != {"video", "audio"}:
                before.unlink(missing_ok=True)
                ensure_silent_audio(before_video, before)
            existing_sttn_frames = frame_count(sttn)
            if not (expected_frames - 3 <= existing_sttn_frames <= expected_frames):
                if sttn.exists():
                    stale = sttn.with_suffix(sttn.suffix + f".incomplete-{frame_count(sttn)}f")
                    sttn.replace(stale)
                command = [str(vsr_python), str(vsr_main), "-i", str(before), "-o", str(sttn)]
                for mask in clips[0]["masks"]:
                    command += ["-c", *[str(value) for value in mask]]
                command += ["--inpaint-mode", "sttn-auto"]
                wait_for_gpu_memory(args.max_idle_gpu_memory_mib, args.gpu_poll_seconds, args.gpu_stable_polls)
                run(command, cwd=args.vsr_root)
            actual_frames = frame_count(sttn)
            terminal_clamp_frames = expected_frames - actual_frames
            if not (0 <= terminal_clamp_frames <= 3):
                raise RuntimeError(f"VSR/STTN frame mismatch: {sttn} expected={expected_frames} actual={actual_frames}")

            segment_map = []
            cursor = 0
            for item in chunk:
                merged = item["merged"]
                for clip in merged["clips"]:
                    relative_start = max(0, round((float(clip["start"]) - float(merged["start"])) * FPS))
                    frames = max(1, round(float(clip["duration"]) * FPS))
                    start_frame = cursor + relative_start
                    end_frame = min(cursor + relative_start + frames, actual_frames)
                    if end_frame <= start_frame:
                        raise RuntimeError(f"terminal clamp removed a complete clip: {clip}")
                    segment_map.append({
                        "clip": clip, "startFrame": start_frame,
                        "endFrame": end_frame, "frames": end_frame - start_frame,
                        "mergedRange": item["rangeIndex"],
                    })
                cursor += item["frames"]

            for segment in segment_map:
                clip = segment["clip"]
                cleaned = cleaned_root / f"{clip['key']}.mp4"
                if not cleaned.exists():
                    base_filter = f"trim=start_frame={segment['startFrame']}:end_frame={segment['endFrame']},setpts=PTS-STARTPTS,setsar=1"
                    temp = cleaned.with_name(cleaned.stem + "-sttn-only.mp4")
                    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(sttn), "-vf", base_filter, "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", str(temp)])
                    if rail.get("enabled", True):
                        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(temp), "-filter_complex", rail_filter(rail), "-map", "[vout]", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", str(cleaned)])
                        temp.unlink(missing_ok=True)
                    else:
                        temp.replace(cleaned)
                cleaned_paths[clip["key"]] = cleaned

            plan["groups"].append({
                "group": group_index, "chunk": chunk_index, "masks": clips[0]["masks"],
                "input": str(before), "sttnOutput": str(sttn), "modelInputFrames": expected_frames,
                "actualOutputFrames": actual_frames, "terminalClampFrames": terminal_clamp_frames,
                "sourceRanges": [{
                    "range": item["rangeIndex"],
                    "plannedFrames": item["plannedFrames"],
                    "actualFrames": item["frames"],
                    "terminalClampFrames": item["sourceTerminalClampFrames"],
                } for item in chunk],
                "clips": [segment | {"clip": segment["clip"]["key"]} for segment in segment_map],
            })

    plan["executedBatchCount"] = executed_batch_count

    for job, block_id, spec_index, key in bindings:
        spec = job["manual_broll"][block_id][spec_index]
        spec["precleaned_path"] = str(cleaned_paths[key])
        spec["hard_subtitle_policy"] = "inpainted-sttn-auto+fullwidth-gaussian-blur-rail"
        spec["preserve_original_composition"] = True
    config["subtitle_style_profile"] = SHORT_DRAMA_SUBTITLE_STYLE
    config["caption_baseline_px"] = int(rail["captionBaseline"])
    caption_style = dict(config.get("caption_style") or {})
    caption_style.update(SHORT_DRAMA_CAPTION_STYLE)
    config["caption_style"] = caption_style
    output = config.setdefault("output", {})
    cover = dict(output.get("narrationSourceSubtitleCover") or {})
    cover.update({
        "enabled": True,
        "mode": "vsr-sttn-precleaned",
        "styleProfile": SHORT_DRAMA_SUBTITLE_STYLE,
        "maskMap": str(args.mask_map),
        "plan": str(work_root / "vsr-plan.json"),
        "rail": rail,
    })
    output["narrationSourceSubtitleCover"] = cover
    dump(work_root / "vsr-plan.json", plan)
    dump(args.output_config, config)
    print(json.dumps({"outputConfig": str(args.output_config), "clips": len(unique), "groups": len(groups)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
