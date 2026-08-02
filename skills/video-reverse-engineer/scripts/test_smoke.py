#!/usr/bin/env python3
"""Generate a synthetic cut, analyze it, and validate all core artifacts."""

from __future__ import annotations

import json
import importlib.util
import math
import struct
import wave
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    here = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("vre_analyzer", here / "analyze_video.py")
    analyzer = importlib.util.module_from_spec(spec); spec.loader.exec_module(analyzer)
    with tempfile.TemporaryDirectory(prefix="vre-contract-") as td:
        out = Path(td)
        shot = {"id": "shot-001", "range": {"start": 0.0, "end": 2.0}, "narrativeFunction": "hook",
                "reasonToExist": "compiler test", "words": [], "camera": {"type": "pan_left", "translation": {"x": -0.1, "y": 0}, "scale": 1, "rotationDegrees": 0},
                "transitionIn": {"type": "none"}, "reconstruction": {}}
        analyzer.compile_hyperframes(out, {"source": {"width": 320, "height": 180, "duration": 2.0, "fps": 24},
                                           "narrative": {"theme": "test"}, "sequences": [{"function": "hook"}], "shots": [shot]})
        required = ["hyperframes/index.html", "hyperframes/STORYBOARD.md", "hyperframes/vendor/gsap.min.js", "hyperframes/compositions/shots/shot-001.html"]
        missing = [name for name in required if not (out / name).is_file()]
        if missing: raise RuntimeError(f"compiler missing artifacts: {missing}")
        sub = (out / "hyperframes/compositions/shots/shot-001.html").read_text(encoding="utf-8")
        if 'window.__timelines["shot-001"]' not in sub or 'data-media-slot="true"' not in sub:
            raise RuntimeError("sub-composition contract is incomplete")
        print("OK: HyperFrames compiler contract")
    ffmpeg = analyzer.media_tool("ffmpeg")
    if not ffmpeg:
        print("SKIP: ffmpeg is unavailable")
        return 0
    with tempfile.TemporaryDirectory(prefix="vre-smoke-") as td:
        root = Path(td); video = root / "cut.mp4"; transcript = root / "words.json"; out = root / "analysis"
        raw_video = root / "frames.rgb"; raw_audio = root / "tone.wav"; width, height, fps = 160, 90, 24
        red = bytes((220, 20, 20)) * (width * height); blue = bytes((20, 40, 220)) * (width * height)
        with raw_video.open("wb") as stream:
            for frame in range(fps * 3): stream.write(red if frame < fps * 1.5 else blue)
        with wave.open(str(raw_audio), "wb") as wav:
            wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(48000)
            wav.writeframes(b"".join(struct.pack("<h", int(5000 * math.sin(2 * math.pi * 440 * i / 48000))) for i in range(48000 * 3)))
        cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pixel_format", "rgb24",
               "-video_size", f"{width}x{height}", "-framerate", str(fps), "-i", str(raw_video), "-i", str(raw_audio),
               "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(video)]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            print("SKIP: ffmpeg cannot synthesize the fixture (reduced build)")
            return 0
        transcript.write_text(json.dumps({"words": [
            {"text": "测试", "start": 0.2, "end": 0.7, "speaker": "S0"},
            {"text": "转场", "start": 1.7, "end": 2.3, "speaker": "S0"}
        ]}, ensure_ascii=False), encoding="utf-8")
        subprocess.run([sys.executable, str(here / "analyze_video.py"), str(video), "--out", str(out),
                        "--transcript-json", str(transcript), "--scene-threshold", "0.20", "--skip-hash"], check=True)
        subprocess.run([sys.executable, str(here / "validate_manifest.py"), str(out / "reconstruction-manifest.json")], check=True)
        required = ["report.md", "narrative-arc.json", "transcript.words.json", "audio-plan.json",
                    "shot-graph.json", "review-flags.json", "hyperframes/index.html", "hyperframes/STORYBOARD.md"]
        missing = [name for name in required if not (out / name).is_file()]
        if missing: raise RuntimeError(f"missing artifacts: {missing}")
        manifest = json.loads((out / "reconstruction-manifest.json").read_text(encoding="utf-8"))
        if len(manifest["shots"]) < 2: raise RuntimeError("synthetic hard cut was not detected")
        if list(out.rglob("*.png")) or list(out.rglob("*.jpg")): raise RuntimeError("image evidence leaked into deliverable")
        print(f"OK: smoke test produced {len(manifest['shots'])} shots")
    return 0


if __name__ == "__main__": raise SystemExit(main())
