#!/usr/bin/env python3
"""Build a reconstruction manifest and HyperFrames skeleton from a source video."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import shutil
import subprocess
import sys
import os
from pathlib import Path
from typing import Any


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def command(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, encoding="utf-8", errors="replace", capture_output=True, check=check)


def media_tool(name: str) -> str | None:
    """Resolve ffmpeg/ffprobe from an explicit environment variable or PATH."""
    configured = os.environ.get(name.upper()) or os.environ.get(f"{name.upper()}_BINARY")
    if configured and Path(configured).is_file():
        return configured
    script_root = Path(__file__).resolve().parents[4]
    roots = list(dict.fromkeys([Path.cwd().resolve(), script_root]))
    candidates = {"ffmpeg": [], "ffprobe": []}
    for root in roots:
        candidates["ffmpeg"].extend([
            root / "node_modules/ffmpeg-static/ffmpeg.exe",
            root / "harness/video-reverse-engineer/node_modules/ffmpeg-static/ffmpeg.exe",
            root / "harness/qishui-ad-production/node_modules/ffmpeg-static/ffmpeg.exe",
            root / "videos/qishui-promo-5pack/node_modules/ffmpeg-static/ffmpeg.exe",
        ])
        candidates["ffprobe"].extend([
            root / "node_modules/ffprobe-static/bin/win32/x64/ffprobe.exe",
            root / "harness/video-reverse-engineer/node_modules/ffprobe-static/bin/win32/x64/ffprobe.exe",
            root / "harness/qishui-ad-production/node_modules/ffprobe-static/bin/win32/x64/ffprobe.exe",
            root / "videos/qishui-promo-5pack/node_modules/ffprobe-static/bin/win32/x64/ffprobe.exe",
        ])
    discovered = next((str(path) for path in candidates.get(name, []) if path.is_file()), None)
    return discovered or shutil.which(name)


def gsap_runtime() -> Path:
    """Resolve the local GSAP browser runtime used by compiled HyperFrames packages."""
    configured = os.environ.get("GSAP_RUNTIME")
    script_root = Path(__file__).resolve().parents[4]
    candidates = [
        Path(configured) if configured else None,
        Path.cwd().resolve() / "node_modules/gsap/dist/gsap.min.js",
        script_root / "node_modules/gsap/dist/gsap.min.js",
        script_root / "harness/video-reverse-engineer/node_modules/gsap/dist/gsap.min.js",
        script_root / "harness/qishui-ad-production/node_modules/gsap/dist/gsap.min.js",
    ]
    discovered = next((path for path in candidates if path and path.is_file()), None)
    if not discovered:
        raise RuntimeError(
            "GSAP runtime is unavailable. Install the project harness dependencies "
            "or set GSAP_RUNTIME to gsap.min.js."
        )
    return discovered


def ratio(value: str | None) -> float:
    if not value or value == "0/0":
        return 0.0
    if "/" in value:
        a, b = value.split("/", 1)
        return float(a) / float(b) if float(b) else 0.0
    return float(value)


def probe(video: Path) -> dict[str, Any]:
    exe = media_tool("ffprobe")
    if not exe:
        raise RuntimeError("ffprobe is required on PATH")
    raw = json.loads(command([exe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)]).stdout)
    vs = next((s for s in raw.get("streams", []) if s.get("codec_type") == "video"), {})
    aus = [s for s in raw.get("streams", []) if s.get("codec_type") == "audio"]
    duration = float(raw.get("format", {}).get("duration") or vs.get("duration") or 0)
    if duration <= 0:
        raise RuntimeError("video duration is unavailable or zero")
    return {
        "duration": round(duration, 6),
        "width": int(vs.get("width") or 0),
        "height": int(vs.get("height") or 0),
        "fps": ratio(vs.get("avg_frame_rate") or vs.get("r_frame_rate")),
        "videoCodec": vs.get("codec_name"),
        "audioStreams": len(aus),
        "audioCodec": aus[0].get("codec_name") if aus else None,
        "sampleRate": int(aus[0].get("sample_rate") or 0) if aus else 0,
        "channels": int(aus[0].get("channels") or 0) if aus else 0,
    }


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def detect_with_scenedetect(video: Path) -> tuple[list[float], list[dict[str, Any]]]:
    try:
        from scenedetect import AdaptiveDetector, ThresholdDetector, detect  # type: ignore
    except Exception:
        return [], []
    points: list[float] = []
    evidence: list[dict[str, Any]] = []
    for detector, method in ((AdaptiveDetector(), "adaptive"), (ThresholdDetector(), "threshold-fade")):
        try:
            scenes = detect(str(video), detector)
            for _, end in scenes[:-1]:
                t = round(end.seconds, 6)
                points.append(t)
                evidence.append({"time": t, "source": "scenedetect", "method": method, "confidence": 0.84})
        except Exception:
            continue
    return points, evidence


def detect_with_ffmpeg(video: Path, threshold: float) -> tuple[list[float], list[dict[str, Any]], str | None]:
    exe = media_tool("ffmpeg")
    if not exe:
        raise RuntimeError("ffmpeg is required on PATH")
    vf = f"select=gt(scene\\,{threshold}),showinfo"
    proc = command([exe, "-hide_banner", "-i", str(video), "-vf", vf, "-an", "-f", "null", "-"], check=False)
    points = [float(v) for v in re.findall(r"pts_time:([0-9.]+)", proc.stderr)]
    evidence = [{"time": round(t, 6), "source": "ffmpeg", "method": f"scene>{threshold}", "confidence": 0.72} for t in points]
    error = None if proc.returncode == 0 else "FFmpeg scene/showinfo filter failed; this binary may be a reduced build."
    return points, evidence, error


def black_intervals(video: Path) -> list[dict[str, float]]:
    exe = media_tool("ffmpeg")
    if not exe:
        return []
    proc = command([exe, "-hide_banner", "-i", str(video), "-vf", "blackdetect=d=0.06:pix_th=0.10", "-an", "-f", "null", "-"], check=False)
    rows = []
    for start, end in re.findall(r"black_start:([0-9.]+).*?black_end:([0-9.]+)", proc.stderr):
        rows.append({"start": float(start), "end": float(end)})
    return rows


def silence_intervals(video: Path) -> list[dict[str, Any]]:
    exe = media_tool("ffmpeg")
    if not exe:
        return []
    proc = command([exe, "-hide_banner", "-i", str(video), "-af", "silencedetect=noise=-38dB:d=0.20", "-vn", "-f", "null", "-"], check=False)
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", proc.stderr)]
    ends = [(float(a), float(b)) for a, b in re.findall(r"silence_end: ([0-9.]+) \| silence_duration: ([0-9.]+)", proc.stderr)]
    result = []
    for index, (end, duration) in enumerate(ends):
        start = starts[index] if index < len(starts) else max(0.0, end - duration)
        result.append({"type": "silence", "range": {"start": round(start, 6), "end": round(end, 6)}, "duration": round(duration, 6), "confidence": 0.94})
    return result


def merge_boundaries(duration: float, candidates: list[float], min_shot: float = 0.30) -> list[float]:
    candidates = sorted(t for t in candidates if min_shot <= t <= duration - min_shot)
    merged: list[float] = []
    for t in candidates:
        if not merged or t - merged[-1] > 0.12:
            merged.append(t)
        else:
            merged[-1] = round((merged[-1] + t) / 2, 6)
    points = [0.0]
    for t in merged:
        if t - points[-1] >= min_shot:
            points.append(round(t, 6))
    if duration - points[-1] < min_shot and len(points) > 1:
        points.pop()
    points.append(round(duration, 6))
    return points


def normalize_words(path: Path | None) -> list[dict[str, Any]]:
    if not path:
        return []
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    raw: list[dict[str, Any]] = []
    if isinstance(data, list):
        raw = data
    elif isinstance(data.get("words"), list):
        raw = data["words"]
    elif isinstance(data.get("word_segments"), list):
        raw = data["word_segments"]
    else:
        for segment in data.get("segments", []):
            raw.extend(segment.get("words", []))
    words = []
    for item in raw:
        text = item.get("text", item.get("word", ""))
        start = item.get("start", item.get("start_time"))
        end = item.get("end", item.get("end_time"))
        if text is None or start is None or end is None:
            continue
        words.append({
            "text": str(text), "start": round(float(start), 6), "end": round(float(end), 6),
            "speaker": item.get("speaker", item.get("speaker_id")), "confidence": item.get("confidence")
        })
    return sorted(words, key=lambda w: (w["start"], w["end"]))


def align_approved_script(transcript_path: Path | None, script_path: Path | None) -> tuple[list[dict[str, Any]] | None, str | None]:
    """Use approved text as truth while retaining ASR segment timing."""
    if not transcript_path or not script_path:
        return None, None
    data = json.loads(transcript_path.read_text(encoding="utf-8-sig"))
    segments = data.get("segments") if isinstance(data, dict) else None
    lines = [line.strip() for line in script_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    if not isinstance(segments, list) or len(lines) != len(segments):
        return None, f"approved script has {len(lines)} lines but transcript has {len(segments or [])} segments"
    result: list[dict[str, Any]] = []
    token_pattern = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*|[0-9]+(?:\.[0-9]+)?|[\u3400-\u9fff]|[^\s]")
    for line, segment in zip(lines, segments):
        start, end = float(segment["start"]), float(segment["end"])
        tokens = token_pattern.findall(line)
        if not tokens:
            continue
        weights = [max(1, len(token)) for token in tokens]; total = sum(weights); cursor = start
        for index, (token, weight) in enumerate(zip(tokens, weights)):
            token_end = end if index == len(tokens) - 1 else cursor + (end - start) * weight / total
            result.append({"text": token, "start": round(cursor, 6), "end": round(token_end, 6),
                           "speaker": segment.get("speaker"), "confidence": None, "textSource": "approved-script"})
            cursor = token_end
    return result, None


def load_transnet_boundaries(path: Path | None, fps: float) -> tuple[list[float], list[dict[str, Any]]]:
    """Load TransNetV2 JSON without coupling the skill to one inference wrapper."""
    if not path:
        return [], []
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    raw = data.get("boundaries", data.get("shots", [])) if isinstance(data, dict) else data
    points: list[float] = []
    for item in raw:
        if isinstance(item, (int, float)):
            points.append(float(item))
        elif isinstance(item, dict):
            if "time" in item: points.append(float(item["time"]))
            elif "frame" in item and fps: points.append(float(item["frame"]) / fps)
            elif "start" in item: points.append(float(item["start"]))
            elif "start_time" in item: points.append(float(item["start_time"]))
            elif "start_frame" in item and fps: points.append(float(item["start_frame"]) / fps)
    evidence = [{"time": round(t, 6), "source": "transnetv2", "method": "neural-shot-boundary", "confidence": 0.86} for t in points]
    return sorted(set(points)), evidence


def shot_words(words: list[dict[str, Any]], start: float, end: float) -> list[dict[str, Any]]:
    return [w for w in words if w["end"] > start and w["start"] < end]


def make_beats(words: list[dict[str, Any]], start: float, end: float) -> list[dict[str, Any]]:
    if not words:
        return [{"id": "beat-001", "range": {"start": start, "end": end}, "text": "", "reason": "visual-state interval"}]
    groups: list[list[dict[str, Any]]] = [[]]
    for index, word in enumerate(words):
        groups[-1].append(word)
        gap = words[index + 1]["start"] - word["end"] if index + 1 < len(words) else 0
        if index + 1 < len(words) and (gap >= 0.5 or re.search(r"[。！？!?；;]$", word["text"])):
            groups.append([])
    return [{
        "id": f"beat-{i:03d}",
        "range": {"start": max(start, g[0]["start"]), "end": min(end, g[-1]["end"])},
        "text": "".join(w["text"] for w in g), "reason": "speech phrase"
    } for i, g in enumerate((g for g in groups if g), 1)]


def camera_motion(video: Path, shots: list[dict[str, Any]], width: int, height: int) -> tuple[bool, str | None]:
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except Exception as exc:
        return False, str(exc)
    cap = cv2.VideoCapture(str(video))
    try:
        for shot in shots:
            start, end = shot["range"]["start"], shot["range"]["end"]
            times = np.linspace(start, end, max(2, min(10, int((end - start) * 3) + 1)))
            frames = []
            for t in times:
                cap.set(cv2.CAP_PROP_POS_MSEC, float(t) * 1000)
                ok, frame = cap.read()
                if ok:
                    frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
            txs: list[float] = []; tys: list[float] = []; scales: list[float] = []; rots: list[float] = []
            for a, b in zip(frames, frames[1:]):
                pts = cv2.goodFeaturesToTrack(a, maxCorners=250, qualityLevel=0.01, minDistance=8)
                if pts is None:
                    continue
                nxt, status, _ = cv2.calcOpticalFlowPyrLK(a, b, pts, None)
                if nxt is None or status is None:
                    continue
                src, dst = pts[status.ravel() == 1], nxt[status.ravel() == 1]
                if len(src) < 8:
                    continue
                matrix, _ = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC)
                if matrix is None:
                    continue
                txs.append(float(matrix[0, 2]) / max(1, width)); tys.append(float(matrix[1, 2]) / max(1, height))
                scales.append(math.sqrt(float(matrix[0, 0]) ** 2 + float(matrix[0, 1]) ** 2))
                rots.append(math.degrees(math.atan2(float(matrix[1, 0]), float(matrix[0, 0]))))
            tx, ty = sum(txs), sum(tys)
            scale = math.prod(scales) if scales else 1.0
            rotation = sum(rots)
            if scale > 1.035: kind = "zoom_in"
            elif scale < 0.965: kind = "zoom_out"
            elif abs(tx) > abs(ty) and abs(tx) > 0.025: kind = "pan_right" if tx > 0 else "pan_left"
            elif abs(ty) > 0.025: kind = "tilt_down" if ty > 0 else "tilt_up"
            else: kind = "static_or_subject_motion"
            shot["camera"] = {
                "type": kind, "translation": {"x": round(tx, 5), "y": round(ty, 5)},
                "scale": round(scale, 5), "rotationDegrees": round(rotation, 4),
                "jitter": round(float(np.std(txs + tys)), 6) if txs or tys else 0.0,
                "confidence": 0.78 if len(txs) >= 2 else 0.42,
            }
            shot["evidence"].append({"source": "opencv", "method": "sparse-optical-flow+affine", "range": shot["range"], "confidence": shot["camera"]["confidence"]})
    finally:
        cap.release()
    return True, None


def transition_for(time: float, blacks: list[dict[str, float]], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    fade = next((x for x in blacks if x["start"] - 0.15 <= time <= x["end"] + 0.15), None)
    nearby = [x for x in evidence if abs(x["time"] - time) <= 0.2]
    return {
        "type": "fade_through_black" if fade else "hard_cut",
        "start": round((fade or {}).get("start", time), 6),
        "duration": round((fade["end"] - fade["start"]) if fade else 0.0, 6),
        "direction": None, "outgoing": {}, "incoming": {}, "audioBridge": None,
        "continuity": "temporal" if fade else "unknown", "confidence": max([x["confidence"] for x in nearby] or [0.65]),
    }


def apply_semantics(manifest: dict[str, Any], semantic: dict[str, Any], flags: list[dict[str, Any]]) -> None:
    manifest["narrative"].update(semantic.get("video", {}))
    if semantic.get("globalStyle"):
        manifest["globalStyle"] = semantic["globalStyle"]
    if semantic.get("sequences"):
        manifest["sequences"] = semantic["sequences"]
    by_id = {s["id"]: s for s in manifest["shots"]}
    allowed = {"narrativeFunction", "reasonToExist", "beats", "composition", "subjects", "visibleExpression", "inferredNarrativeEmotion", "actions", "layers", "textElements", "continuityAnchors", "reconstruction", "confidence", "evidence"}
    for shot_id, observation in semantic.get("shots", {}).items():
        if shot_id not in by_id:
            flags.append(flag("warning", shot_id, "semantic_unknown_shot", "Semantic observations reference an unknown shot."))
            continue
        shot = by_id[shot_id]
        if "spokenDelivery" in observation:
            shot.setdefault("voice", {})["spokenDelivery"] = observation["spokenDelivery"]
        if "camera" in observation:
            measured = shot.get("camera") or {}; described = observation["camera"]
            if measured.get("confidence", 0) >= 0.7 and measured.get("type") not in (None, "unknown") and measured.get("type") != described.get("type"):
                flags.append(flag("warning", shot_id, "camera_conflict", f"Measured={measured.get('type')}; semantic={described.get('type')}", [measured, described]))
                shot["camera"] = {**measured, "semanticInterpretation": described}
            else:
                shot["camera"] = described
        for key in allowed:
            if key in observation:
                shot[key] = observation[key]
        for key in ("transitionIn", "transitionOut"):
            candidate = observation.get(key)
            if not candidate:
                continue
            old = shot.get(key, {})
            if candidate.get("type") and old.get("type") and candidate["type"] != old["type"]:
                semantic_wins = float(candidate.get("confidence", 0)) >= float(old.get("confidence", 0))
                flags.append(flag("info" if semantic_wins else "warning", shot_id, "transition_conflict", f"Algorithm={old['type']}; semantic={candidate['type']}", [old, candidate]))
                if semantic_wins:
                    candidate = {**candidate, "algorithmInterpretation": old}
                else:
                    candidate = {**old, "semanticInterpretation": candidate}
            shot[key] = candidate
    for conflict in semantic.get("conflicts", []):
        flags.append(flag("warning", conflict.get("scope", "video"), "semantic_conflict", conflict.get("message", str(conflict)), [conflict]))


def flag(severity: str, scope: str, code: str, message: str, evidence: list[Any] | None = None) -> dict[str, Any]:
    return {"id": "", "severity": severity, "scope": scope, "code": code, "message": message, "evidence": evidence or []}


def validate_geometry(value: Any, path: str, flags: list[dict[str, Any]]) -> None:
    if isinstance(value, dict):
        if all(k in value for k in ("x", "y", "width", "height")):
            if any(not isinstance(value[k], (int, float)) or not 0 <= value[k] <= 1 for k in ("x", "y", "width", "height")):
                flags.append(flag("error", path, "geometry_out_of_range", "Normalized geometry must stay within [0,1].", [value]))
        for k, v in value.items(): validate_geometry(v, f"{path}.{k}", flags)
    elif isinstance(value, list):
        for i, v in enumerate(value): validate_geometry(v, f"{path}[{i}]", flags)


def compile_hyperframes(out: Path, manifest: dict[str, Any]) -> None:
    hf = out / "hyperframes"; shot_dir = hf / "compositions" / "shots"; shot_dir.mkdir(parents=True, exist_ok=True)
    vendor_dir = hf / "vendor"; vendor_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(gsap_runtime(), vendor_dir / "gsap.min.js")
    width, height, duration = manifest["source"]["width"], manifest["source"]["height"], manifest["source"]["duration"]
    source_value = manifest["source"].get("path")
    source_path = Path(source_value) if source_value else Path("source-video.mp4")
    source_href = Path(os.path.relpath(source_path, hf)).as_posix() if source_value else ""
    hosts = []; main_tweens = []
    storyboard = ["---", f"format: {width}x{height}", f"message: {json.dumps(manifest['narrative'].get('theme') or 'Reconstruct the source video')}", f"arc: {json.dumps(' → '.join(x.get('function','unknown') for x in manifest['sequences']))}", "---", ""]
    for index, shot in enumerate(manifest["shots"], 1):
        sid = shot["id"]; start = shot["range"]["start"]; dur = round(shot["range"]["end"] - start, 6)
        transition = shot.get("transitionIn") or {}; transition_type = transition.get("type", "hard_cut"); effect_id = transition.get("effectId", "")
        hosts.append(f'  <div id="host-{sid}" class="clip" data-composition-id="{sid}" data-composition-src="compositions/shots/{sid}.html" data-width="{width}" data-height="{height}" data-start="{start}" data-duration="{dur}" data-track-index="1" data-transition-type="{html.escape(str(transition_type))}" data-transition-effect="{html.escape(str(effect_id))}"></div>')
        transition_duration = min(float(transition.get("duration", 0) or 0), dur)
        if index > 1 and transition_duration > 0 and transition_type in ("fade", "cross_dissolve", "custom"):
            initial_scale = 0.96 if effect_id == "blur-zoom-reveal" else 1.0
            main_tweens.append(f'vreTl.fromTo("#host-{sid}", {{opacity:0,scale:{initial_scale}}}, {{opacity:1,scale:1,duration:{transition_duration:.6f},ease:"power2.out"}}, {start:.6f});')
        camera = shot.get("camera", {}); tr = camera.get("translation", {})
        tx, ty = float(tr.get("x", 0)) * width, float(tr.get("y", 0)) * height
        scale = float(camera.get("scale", 1)); rotation = float(camera.get("rotationDegrees", 0))
        title = html.escape(shot.get("narrativeFunction") or "Unknown function")
        prompt = html.escape((shot.get("reconstruction") or {}).get("mediaPrompt") or "Replace this slot with source-matched media; preserve composition and continuity anchors.")
        slot_font = max(10, min(32, round(height * 0.04))); meta_font = max(8, min(22, round(height * 0.025)))
        sub = f'''<!DOCTYPE html><html><body><template>
<style>
  #{sid}-root{{position:relative;width:{width}px;height:{height}px;overflow:hidden;background:#0b0d12;color:#f5f7ff;font-family:system-ui,sans-serif}}
  #{sid}-scene{{position:absolute;inset:0;overflow:hidden}}
  #{sid}-fill{{position:absolute;inset:0;background:radial-gradient(circle at 50% 42%,#222a3b,#0b0d12 68%)}}
  #{sid}-camera{{position:absolute;inset:0;will-change:transform}}
  #{sid}-slot{{position:absolute;left:8%;top:10%;width:84%;height:72%;border:3px solid #65718d;background:#161b27;display:grid;place-items:center;padding:5%;font-size:{slot_font}px;text-align:center}}
  #{sid}-meta{{position:absolute;left:5%;right:5%;bottom:5%;font:{meta_font}px ui-monospace,monospace;color:#aab4ca}}
</style>
<div id="{sid}-root" data-composition-id="{sid}" data-width="{width}" data-height="{height}" data-start="0" data-duration="{dur}">
  <div id="{sid}-scene" class="clip" data-start="0" data-duration="{dur}" data-track-index="0">
    <div id="{sid}-fill"></div><div id="{sid}-camera" data-layout-allow-overflow><div id="{sid}-slot" data-media-slot="true" data-generation-prompt="{prompt}">MEDIA SLOT · {sid}</div></div>
    <div id="{sid}-meta">{sid} · {title} · {start:.3f}s–{shot['range']['end']:.3f}s</div>
  </div>
</div>
<script>
  const tl = gsap.timeline({{paused:true}});
  tl.fromTo("#{sid}-camera", {{x:0,y:0,scale:1,rotation:0}}, {{x:{tx:.3f},y:{ty:.3f},scale:{scale:.6f},rotation:{rotation:.4f},duration:{dur},ease:"power1.inOut"}}, 0);
  window.__timelines["{sid}"] = tl;
</script>
</template></body></html>'''
        (shot_dir / f"{sid}.html").write_text(sub, encoding="utf-8")
        storyboard += [f"## Frame {index} — {sid}", "", f"- scene: {shot.get('reasonToExist') or 'Reconstruction media slot'}", f"- duration: {dur}s", f"- transition_in: {shot.get('transitionIn',{}).get('type','cut')}", "- status: built", f"- voiceover: {json.dumps(''.join(w['text'] for w in shot.get('words',[])), ensure_ascii=False)}", f"- src: compositions/shots/{sid}.html", "", f"Narrative function: {shot.get('narrativeFunction') or 'unknown'}. Camera: {camera.get('type','unknown')}.", ""]
    index_html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width={width},height={height}"><title>Video reconstruction</title><script>if(location.protocol==="file:"){{location.replace("preview.html");}}</script><script src="vendor/gsap.min.js"></script><style>*{{box-sizing:border-box}}html,body{{margin:0;width:{width}px;height:{height}px;overflow:hidden;background:#000}}#vre-main{{position:relative;width:{width}px;height:{height}px;overflow:hidden}}</style></head><body>
<div id="vre-main" data-composition-id="vre-main" data-width="{width}" data-height="{height}" data-start="0" data-duration="{duration}">
{chr(10).join(hosts)}
</div><script>window.__timelines=window.__timelines||{{}};const vreTl=gsap.timeline({{paused:true}});{''.join(main_tweens)}window.__timelines["vre-main"]=vreTl;</script></body></html>'''
    (hf / "index.html").write_text(index_html, encoding="utf-8")
    (hf / "STORYBOARD.md").write_text("\n".join(storyboard), encoding="utf-8")
    viewer_payload = {
        "sourceHref": source_href,
        "sourceName": source_path.name,
        "duration": duration,
        "width": width,
        "height": height,
        "narrative": manifest.get("narrative", {}),
        "globalStyle": manifest.get("globalStyle", {}),
        "shots": [
            {
                "id": shot["id"],
                "range": shot["range"],
                "narration": "".join(word.get("text", "") for word in shot.get("words", [])),
                "function": shot.get("narrativeFunction"),
                "purpose": shot.get("reasonToExist"),
                "spokenDelivery": (shot.get("voice") or {}).get("spokenDelivery", {}),
                "composition": shot.get("composition", {}),
                "camera": shot.get("camera", {}),
                "subjects": shot.get("subjects", []),
                "visibleExpression": shot.get("visibleExpression", []),
                "narrativeEmotion": shot.get("inferredNarrativeEmotion", []),
                "actions": shot.get("actions", []),
                "transitionIn": shot.get("transitionIn", {}),
                "transitionOut": shot.get("transitionOut", {}),
                "reconstruction": shot.get("reconstruction", {}),
            }
            for shot in manifest.get("shots", [])
        ],
    }
    payload_json = json.dumps(viewer_payload, ensure_ascii=False).replace("</", "<\\/")
    preview_html = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>视频拆解镜头浏览器</title>
<style>
:root{{--paper:#f7f8ed;--ink:#171914;--muted:#677064;--brand:#42a85a;--line:#cad4c4;--panel:#fffef7;--accent:#efffb9}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 system-ui,"Microsoft YaHei",sans-serif}}
.app{{min-height:100vh;display:grid;grid-template-columns:minmax(320px,42vw) 1fr;gap:22px;padding:22px;max-width:1500px;margin:auto}}
.stage-column{{position:sticky;top:22px;align-self:start}}.eyebrow{{font:700 12px/1 ui-monospace,monospace;letter-spacing:.13em;color:var(--brand);text-transform:uppercase}}
h1{{font-size:clamp(26px,3vw,48px);line-height:1.05;margin:9px 0 12px}}.summary{{color:var(--muted);max-width:60ch;margin-bottom:16px}}
.video-shell{{position:relative;width:min(100%,440px);aspect-ratio:{width}/{height};background:#111;border:3px solid var(--ink);border-radius:20px;overflow:hidden;box-shadow:10px 10px 0 var(--accent)}}
video{{width:100%;height:100%;object-fit:contain;background:#000;display:block}}.geometry{{position:absolute;inset:0;pointer-events:none}}.box{{position:absolute;border:2px solid #ff4f73;background:#ff4f7320;color:white;font:700 11px/1.2 ui-monospace,monospace;padding:3px;text-shadow:0 1px 2px #000}}
.source-error{{display:none;margin-top:14px;padding:12px;border:2px solid #b73434;background:#fff0f0;color:#7e1e1e;border-radius:10px}}.toolbar{{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:16px}}
button,.toggle{{border:2px solid var(--ink);background:var(--panel);color:var(--ink);padding:9px 12px;border-radius:999px;font-weight:700;cursor:pointer}}button:hover,button.active{{background:var(--accent)}}
.panel{{min-width:0}}.shot-nav{{display:flex;gap:8px;overflow:auto;padding:4px 2px 13px;scrollbar-width:thin}}.shot-nav button{{flex:0 0 auto}}
.card{{background:var(--panel);border:2px solid var(--ink);border-radius:18px;padding:clamp(18px,3vw,34px);box-shadow:8px 8px 0 #dce6d6}}.time{{font:700 13px ui-monospace,monospace;color:var(--brand)}}
.narration{{font-size:clamp(25px,3vw,44px);line-height:1.25;margin:10px 0 20px;font-weight:900}}.purpose{{font-size:18px;margin:0 0 22px}}
.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}}details{{border-top:1px solid var(--line);padding:12px 0}}summary{{cursor:pointer;font-weight:800}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;color:#3e473c;background:#f1f4ec;border-radius:10px;padding:12px;margin-bottom:0}}
.plain{{background:#f1f4ec;border-radius:10px;padding:12px;margin-top:8px}}.footer-note{{margin-top:18px;color:var(--muted);font-size:13px}}code{{font-family:ui-monospace,monospace}}
@media(max-width:900px){{.app{{grid-template-columns:1fr;padding:14px}}.stage-column{{position:static}}.video-shell{{margin:auto}}.grid{{grid-template-columns:1fr}}}}
</style></head><body><main class="app">
<section class="stage-column"><div class="eyebrow">VIDEO REVERSE ENGINEER · HUMAN VIEW</div><h1>视频拆解镜头浏览器</h1><p class="summary" id="summary"></p>
<div class="video-shell"><video id="video" controls preload="metadata"></video><div class="geometry" id="geometry"></div></div>
<div class="source-error" id="sourceError">无法加载原视频。请确认拆解文件夹仍与原视频位于同一工作目录，或重新运行解析。</div>
<div class="toolbar"><button id="restart">从本镜头开始播放</button><label class="toggle"><input id="showGeometry" type="checkbox"> 显示构图框</label></div>
<p class="footer-note">双击 <code>index.html</code> 会进入本页；HyperFrames CLI 仍然读取原始工程时间线。</p></section>
<section class="panel"><nav class="shot-nav" id="shotNav" aria-label="镜头列表"></nav><article class="card"><div class="time" id="time"></div><div class="narration" id="narration"></div><p class="purpose" id="purpose"></p>
<div class="grid"><details open><summary>构图</summary><pre id="composition"></pre></details><details open><summary>镜头与运动</summary><pre id="camera"></pre></details><details><summary>主体与位置</summary><pre id="subjects"></pre></details><details><summary>表情与叙事情绪</summary><pre id="emotion"></pre></details><details><summary>声音表达</summary><pre id="delivery"></pre></details><details><summary>转场</summary><pre id="transition"></pre></details><details><summary>动作</summary><pre id="actions"></pre></details><details open><summary>重建时需要的素材</summary><pre id="reconstruction"></pre></details></div>
</article></section></main>
<script id="vre-data" type="application/json">{payload_json}</script><script>
const data=JSON.parse(document.getElementById('vre-data').textContent);const video=document.getElementById('video');video.src=data.sourceHref;
const nav=document.getElementById('shotNav'),geom=document.getElementById('geometry'),show=document.getElementById('showGeometry');let current=0;
document.getElementById('summary').textContent=`${{data.narrative.theme||'视频结构拆解'}}｜${{data.shots.length}} 个镜头｜${{Number(data.duration).toFixed(2)}} 秒`;
const pretty=v=>JSON.stringify(v??{{}},null,2);const label=(v,fallback='未标注')=>v||fallback;
function addBox(g,name){{if(!g||[g.x,g.y,g.width,g.height].some(v=>typeof v!=='number'))return;const el=document.createElement('div');el.className='box';el.textContent=name;Object.assign(el.style,{{left:`${{g.x*100}}%`,top:`${{g.y*100}}%`,width:`${{g.width*100}}%`,height:`${{g.height*100}}%`}});geom.appendChild(el)}}
function drawGeometry(shot){{geom.innerHTML='';if(!show.checked)return;(data.globalStyle.layoutZones||[]).forEach(z=>addBox(z.geometry,z.id));(shot.subjects||[]).forEach((s,i)=>addBox(s.geometry,s.id||`主体${{i+1}}`))}}
function select(i,seek=true){{current=i;const s=data.shots[i];[...nav.children].forEach((b,n)=>b.classList.toggle('active',n===i));document.getElementById('time').textContent=`${{s.id}} · ${{s.range.start.toFixed(3)}}–${{s.range.end.toFixed(3)}}s · ${{label(s.function)}}`;document.getElementById('narration').textContent=s.narration||'（此镜头没有口播）';document.getElementById('purpose').textContent=`镜头存在的理由：${{label(s.purpose)}}`;document.getElementById('composition').textContent=pretty(s.composition);document.getElementById('camera').textContent=pretty(s.camera);document.getElementById('subjects').textContent=pretty(s.subjects);document.getElementById('emotion').textContent=pretty({{visibleExpression:s.visibleExpression,narrativeEmotion:s.narrativeEmotion}});document.getElementById('delivery').textContent=pretty(s.spokenDelivery);document.getElementById('transition').textContent=pretty({{transitionIn:s.transitionIn,transitionOut:s.transitionOut}});document.getElementById('actions').textContent=pretty(s.actions);document.getElementById('reconstruction').textContent=pretty(s.reconstruction);drawGeometry(s);if(seek)video.currentTime=s.range.start}}
data.shots.forEach((s,i)=>{{const b=document.createElement('button');b.textContent=String(i+1).padStart(2,'0');b.title=`${{s.range.start.toFixed(2)}}s · ${{s.narration}}`;b.onclick=()=>select(i,true);nav.appendChild(b)}});
video.addEventListener('error',()=>document.getElementById('sourceError').style.display='block');video.addEventListener('loadedmetadata',()=>{{if(video.currentTime===0)video.currentTime=Math.min(.2,Math.max(0,data.duration-.01))}});video.addEventListener('timeupdate',()=>{{const i=data.shots.findIndex(s=>video.currentTime>=s.range.start&&video.currentTime<s.range.end);if(i>=0&&i!==current)select(i,false)}});show.onchange=()=>drawGeometry(data.shots[current]);document.getElementById('restart').onclick=()=>{{video.currentTime=data.shots[current].range.start;video.play()}};select(0,false);
</script></body></html>'''
    (hf / "preview.html").write_text(preview_html, encoding="utf-8")
    readme = f'''# 请先看：案例视频拆解包

直接双击 `index.html` 会自动打开中文镜头浏览器。它会播放原视频，并允许点击镜头编号查看对应的文案、构图、表情、镜头运动、转场和重建素材要求。

## 这几个文件分别做什么

- `preview.html`：给人看的交互式镜头浏览器，不需要安装依赖。
- `index.html`：HyperFrames 的正式工程入口；本地双击时会转到浏览器页面。
- `STORYBOARD.md`：按镜头排列的简版故事板。
- `compositions/shots/*.html`：每个镜头的代码化构图与运动槽位。
- `../report.md`：最完整的中文拆解报告。
- `../reconstruction-manifest.json`：后续 AI 模型和剪辑程序使用的唯一事实源。

## MEDIA SLOT 是什么

它表示该位置需要真人、表情包、真实 UI 或复杂场景素材。HTML 只负责结构和运动，不会假装能凭代码还原真人外观。具体约束在每个镜头的 `reconstruction` 字段中。

原视频：`{source_href}`
'''
    (hf / "README-请先看.md").write_text(readme, encoding="utf-8")
    dump(hf / "package.json", {"private": True, "dependencies": {"gsap": "^3.13.0"}})


def export_audio_material(video: Path, out: Path) -> Path:
    exe = media_tool("ffmpeg")
    if not exe:
        raise RuntimeError("ffmpeg is required to export audio")
    audio = out / "audio" / "source-audio.wav"; audio.parent.mkdir(parents=True, exist_ok=True)
    command([exe, "-y", "-hide_banner", "-loglevel", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(audio)])
    return audio


def write_materials_index(out: Path, video: Path, has_hyperframes: bool) -> None:
    source_video = Path(os.path.relpath(video, out)).as_posix()
    value = {
        "使用说明": "hyperframes/README-请先看.md" if has_hyperframes else "report.md",
        "人类可读报告": "report.md",
        "原视频": source_video,
        "确认文案": "approved-script.txt",
        "原始音频": "audio/source-audio.wav",
        "叙事结构": "narrative-arc.json",
        "镜头图": "shot-graph.json",
        "模型事实源": "reconstruction-manifest.json",
        "人工复核项": "review-flags.json",
        "HyperFrames工程": "hyperframes/" if has_hyperframes else None,
        "可视化镜头浏览器": "hyperframes/preview.html" if has_hyperframes else None,
        "交付图片": [],
        "说明": "真人、表情包和真实 UI 以 media-slot 表示；固定品牌框架、构图、时间和运动优先代码化。",
    }
    dump(out / "materials-index.json", value)


def report_text(manifest: dict[str, Any], flags: list[dict[str, Any]]) -> str:
    compact = lambda value: json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    lines = ["# Video reverse-engineering report", "", f"- Duration: {manifest['source']['duration']:.3f}s", f"- Format: {manifest['source']['width']}×{manifest['source']['height']} @ {manifest['source']['fps']:.3f} fps", f"- Shots: {len(manifest['shots'])}", f"- Transcript tokens: {len(manifest['audio']['words'])}", f"- Review flags: {len(flags)}", "", "## Narrative", "", f"- Theme: {manifest['narrative'].get('theme') or 'Pending semantic review'}", f"- Audience: {manifest['narrative'].get('audience') or 'unknown'}", f"- Type: {manifest['narrative'].get('narrativeType') or 'unknown'}", f"- Emotion arc: {' → '.join(manifest['narrative'].get('emotionArc') or [])}", "", "## Sequences", ""]
    for sequence in manifest.get("sequences", []):
        lines.append(f"- **{sequence.get('id')} {sequence.get('range',{}).get('start',0):.3f}–{sequence.get('range',{}).get('end',0):.3f}s · {sequence.get('function')}** — {sequence.get('reason','')}")
    lines += ["", "## Global reconstruction style", "", f"```json\n{json.dumps(manifest.get('globalStyle',{}),ensure_ascii=False,indent=2)}\n```", "", "## Shots", ""]
    for shot in manifest["shots"]:
        text = "".join(w["text"] for w in shot.get("words", []))
        lines += [f"### {shot['id']} · {shot['range']['start']:.3f}–{shot['range']['end']:.3f}s", "",
                  f"- Function: {shot.get('narrativeFunction') or 'unknown'}", f"- Purpose: {shot.get('reasonToExist') or 'unknown'}",
                  f"- Narration: {text or '(not available)'}", f"- Spoken delivery: {compact(shot.get('voice',{}).get('spokenDelivery',{}))}",
                  f"- Composition: {compact(shot.get('composition',{}))}", f"- Camera: {compact(shot.get('camera',{}))}",
                  f"- Subjects: {compact(shot.get('subjects',[]))}", f"- Visible expression: {compact(shot.get('visibleExpression',[]))}",
                  f"- Narrative emotion: {compact(shot.get('inferredNarrativeEmotion',[]))}", f"- Actions: {compact(shot.get('actions',[]))}",
                  f"- Transition in: {compact(shot.get('transitionIn',{}))}", f"- Transition out: {compact(shot.get('transitionOut',{}))}",
                  f"- Reconstruction: {compact(shot.get('reconstruction',{}))}", ""]
    lines += ["## Review flags", ""] + [f"- [{x['severity']}] `{x['scope']}` `{x['code']}` — {x['message']}" for x in flags]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path); ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--mode", choices=("deep", "fast"), default="deep"); ap.add_argument("--target", choices=("hyperframes", "manifest"), default="hyperframes")
    ap.add_argument("--language", default="auto"); ap.add_argument("--transcript-json", type=Path); ap.add_argument("--semantic-json", type=Path)
    ap.add_argument("--approved-script", type=Path, help="Canonical subtitle/narration text; ASR still supplies timing")
    ap.add_argument("--transnet-json", type=Path, help="Optional TransNetV2 boundary JSON")
    ap.add_argument(
        "--visual-proxy",
        type=Path,
        help="Optional equal-duration proxy used only for frame-level detection and camera motion",
    )
    ap.add_argument("--scene-threshold", type=float, default=0.10)
    ap.add_argument("--min-shot-duration", type=float, default=0.30)
    ap.add_argument("--export-audio", action="store_true", help="Export mono 16 kHz WAV into audio/source-audio.wav")
    ap.add_argument("--skip-hash", action="store_true")
    args = ap.parse_args(); video = args.input.resolve(); out = args.out.resolve()
    if not video.is_file(): raise SystemExit(f"input does not exist: {video}")
    visual_video = args.visual_proxy.resolve() if args.visual_proxy else video
    if not visual_video.is_file(): raise SystemExit(f"visual proxy does not exist: {visual_video}")
    out.mkdir(parents=True, exist_ok=True)
    meta = probe(video); visual_meta = probe(visual_video); words = normalize_words(args.transcript_json); flags: list[dict[str, Any]] = []
    if abs(float(visual_meta["duration"]) - float(meta["duration"])) > 0.25:
        raise SystemExit(
            f"visual proxy duration mismatch: source={meta['duration']}, proxy={visual_meta['duration']}"
        )
    aligned_words, alignment_error = align_approved_script(args.transcript_json, args.approved_script)
    if aligned_words is not None:
        words = aligned_words
    elif alignment_error:
        flags.append(flag("error", "audio", "approved_script_alignment_failed", alignment_error))
    sd_candidates, sd_evidence = detect_with_scenedetect(visual_video)
    ff_candidates, ff_evidence, ff_error = detect_with_ffmpeg(visual_video, args.scene_threshold)
    tn_candidates, tn_evidence = load_transnet_boundaries(args.transnet_json, meta["fps"])
    candidates = sd_candidates + ff_candidates + tn_candidates
    boundary_evidence = sd_evidence + ff_evidence + tn_evidence
    detector = "+".join(x for x, present in (("PySceneDetect", bool(sd_candidates)), ("FFmpeg", ff_error is None), ("TransNetV2", bool(tn_candidates))) if present) or "Unavailable"
    if not sd_candidates and ff_error is None:
        flags.append(flag("info", "video", "detector_fallback", "PySceneDetect unavailable or returned no cuts; used FFmpeg scene detection."))
    if ff_error:
        severity = "warning" if (sd_candidates or tn_candidates) else "error"
        flags.append(flag(severity, "video", "frame_detector_unavailable", ff_error))
    blacks = black_intervals(visual_video); candidates += [x for row in blacks for x in (row["start"], row["end"])]
    boundaries = merge_boundaries(meta["duration"], candidates, args.min_shot_duration)
    boundary_confidence = 0.84 if (sd_candidates or tn_candidates) else (0.68 if ff_error is None else 0.20)
    shots = []
    for i, (start, end) in enumerate(zip(boundaries, boundaries[1:]), 1):
        sid = f"shot-{i:03d}"; sw = shot_words(words, start, end)
        shots.append({
            "id": sid, "range": {"start": start, "end": end}, "beats": make_beats(sw, start, end),
            "narrativeFunction": None, "reasonToExist": None, "words": sw,
            "voice": {"spokenDelivery": {"status": "unknown"}, "wordCount": len(sw)},
            "composition": {"status": "unknown", "coordinateSystem": "normalized-top-left"},
            "camera": {"type": "unknown", "confidence": 0.0}, "subjects": [], "visibleExpression": [],
            "inferredNarrativeEmotion": [], "expressions": [], "actions": [], "layers": [], "textElements": [],
            "transitionIn": {"type": "none", "start": start, "duration": 0, "confidence": 1.0} if i == 1 else transition_for(start, blacks, boundary_evidence),
            "transitionOut": {"type": "none", "start": end, "duration": 0, "confidence": 1.0},
            "continuityAnchors": [], "reconstruction": {"strategy": "media-slot", "codeFirst": True},
            "confidence": {"boundary": boundary_confidence, "semantic": 0.0},
            "evidence": [{"source": detector.lower(), "method": "shot-boundary-fusion", "range": {"start": start, "end": end}, "confidence": boundary_confidence}],
        })
    for i in range(len(shots) - 1): shots[i]["transitionOut"] = shots[i + 1]["transitionIn"]
    camera_ok, camera_error = camera_motion(visual_video, shots, visual_meta["width"], visual_meta["height"])
    if not camera_ok: flags.append(flag("warning", "video", "camera_motion_unavailable", f"OpenCV motion analysis unavailable: {camera_error}"))
    if not words: flags.append(flag("error", "audio", "transcript_missing", "Provide word-level ASR with --transcript-json; text was not invented."))
    semantic = json.loads(args.semantic_json.read_text(encoding="utf-8-sig")) if args.semantic_json else None
    if not semantic: flags.append(flag("warning", "video", "semantic_review_missing", "Narrative, composition, subjects, and performance need semantic observations."))
    approved_script = args.approved_script.read_text(encoding="utf-8-sig") if args.approved_script else None
    source = {"path": str(video), **meta, "sizeBytes": video.stat().st_size, "sha256": None if args.skip_hash else sha256(video)}
    exported_audio = export_audio_material(video, out) if args.export_audio else None
    manifest = {
        "schemaVersion": "1.0", "source": source,
        "globalStyle": {"status": "unknown"},
        "narrative": {"theme": None, "audience": None, "narrativeType": None, "visualGrammar": [], "emotionArc": []},
        "audio": {"language": args.language, "words": words, "events": silence_intervals(video),
                  "source": "approved-script+asr-timing" if approved_script and aligned_words is not None else ("asr" if words else "unavailable"),
                  "approvedScript": approved_script, "prosody": {"status": "pending-semantic-or-acoustic-analysis"},
                  "materials": [{"type": "source-audio", "path": str(exported_audio), "sampleRate": 16000, "channels": 1}] if exported_audio else []},
        "sequences": [{"id": "sequence-001", "range": {"start": 0.0, "end": meta["duration"]}, "function": "unknown", "reason": "pending semantic review", "confidence": 0.0}],
        "shots": shots, "reviewFlags": flags,
        "analysis": {"mode": args.mode, "boundaryDetector": detector, "sceneThreshold": args.scene_threshold,
                     "minShotDuration": args.min_shot_duration, "temporaryImagesDelivered": False,
                     "semanticProvider": "external-contract" if semantic else None,
                     "visualProxy": str(visual_video) if visual_video != video else None},
    }
    if semantic: apply_semantics(manifest, semantic, flags)
    for index in range(len(manifest["shots"]) - 1):
        outgoing = manifest["shots"][index].get("transitionOut") or {}
        if outgoing.get("type") not in (None, "none"):
            manifest["shots"][index + 1]["transitionIn"] = outgoing
    if semantic and all((shot.get("camera") or {}).get("type") not in (None, "unknown") for shot in manifest["shots"]):
        flags[:] = [item for item in flags if item.get("code") != "camera_motion_unavailable"]
        manifest["audio"]["prosody"] = {
            "status": "semantic-per-shot",
            "shots": {shot["id"]: shot.get("voice", {}).get("spokenDelivery", {}) for shot in manifest["shots"]}
        }
    validate_geometry(manifest, "manifest", flags)
    for n, item in enumerate(flags, 1): item["id"] = f"review-{n:03d}"
    dump(out / "reconstruction-manifest.json", manifest)
    dump(out / "narrative-arc.json", {"narrative": manifest["narrative"], "sequences": manifest["sequences"]})
    dump(out / "transcript.words.json", {"language": args.language, "words": words})
    dump(out / "audio-plan.json", manifest["audio"])
    dump(out / "shot-graph.json", {"boundaries": boundaries, "shots": shots})
    dump(out / "review-flags.json", flags)
    (out / "report.md").write_text(report_text(manifest, flags), encoding="utf-8")
    if args.target == "hyperframes": compile_hyperframes(out, manifest)
    write_materials_index(out, video, args.target == "hyperframes")
    print(json.dumps({"output": str(out), "shots": len(shots), "words": len(words), "reviewFlags": len(flags)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
