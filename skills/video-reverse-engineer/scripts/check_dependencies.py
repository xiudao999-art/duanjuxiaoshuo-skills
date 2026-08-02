#!/usr/bin/env python3
"""Check VRE sibling skills and runtimes without installing or vendoring them."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def command_ok(args: list[str]) -> bool:
    try:
        return subprocess.run(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode == 0
    except OSError:
        return False


def first_file(paths: list[Path]) -> Path | None:
    return next((path for path in paths if path.is_file()), None)


def check(project_root: Path) -> dict[str, Any]:
    skill_root = Path(__file__).resolve().parents[1]
    declaration = json.loads(
        (skill_root / "references" / "dependencies.json").read_text(encoding="utf-8")
    )
    skills_root = project_root / ".codex" / "skills"
    missing_skills = [
        name
        for name in declaration["requiredSkills"]
        if not (skills_root / name / "SKILL.md").is_file()
    ]

    python = project_root / ".codex" / "skills" / "video-use" / ".venv" / (
        "Scripts/python.exe" if os.name == "nt" else "bin/python"
    )
    python_ready = python.is_file() and command_ok(
        [
            str(python),
            "-c",
            "import cv2,numpy,scenedetect,torch,transnetv2_pytorch",
        ]
    )

    node = shutil.which("node")
    node_major = 0
    if node:
        try:
            version = subprocess.run(
                [node, "--version"], capture_output=True, text=True, check=True
            ).stdout.strip()
            node_major = int(version.lstrip("v").split(".", 1)[0])
        except (OSError, ValueError, subprocess.SubprocessError):
            node_major = 0

    project_node_modules = project_root / "node_modules"
    dedicated = project_root / "harness" / "video-reverse-engineer" / "node_modules"
    compatibility = project_root / "harness" / "qishui-ad-production" / "node_modules"
    ffmpeg = first_file(
        [
            project_node_modules / "ffmpeg-static" / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg"),
            dedicated / "ffmpeg-static" / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg"),
            compatibility / "ffmpeg-static" / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg"),
        ]
    ) or (Path(shutil.which("ffmpeg")) if shutil.which("ffmpeg") else None)
    ffprobe = first_file(
        [
            project_node_modules / "ffprobe-static" / "bin" / "win32" / "x64" / "ffprobe.exe",
            dedicated / "ffprobe-static" / "bin" / "win32" / "x64" / "ffprobe.exe",
            compatibility / "ffprobe-static" / "bin" / "win32" / "x64" / "ffprobe.exe",
        ]
    ) or (Path(shutil.which("ffprobe")) if shutil.which("ffprobe") else None)
    gsap = first_file(
        [
            project_node_modules / "gsap" / "dist" / "gsap.min.js",
            dedicated / "gsap" / "dist" / "gsap.min.js",
            compatibility / "gsap" / "dist" / "gsap.min.js",
            Path(os.environ["GSAP_RUNTIME"]) if os.environ.get("GSAP_RUNTIME") else Path(),
        ]
    )
    hyperframes = first_file(
        [
            project_node_modules / ".bin" / ("hyperframes.cmd" if os.name == "nt" else "hyperframes"),
            dedicated / ".bin" / ("hyperframes.cmd" if os.name == "nt" else "hyperframes"),
            compatibility / ".bin" / ("hyperframes.cmd" if os.name == "nt" else "hyperframes"),
        ]
    ) or (Path(shutil.which("hyperframes")) if shutil.which("hyperframes") else None)

    missing_runtime = []
    if not python_ready:
        missing_runtime.append("video-use Python environment/imports")
    if node_major < 22:
        missing_runtime.append("Node.js >=22")
    if not ffmpeg:
        missing_runtime.append("FFmpeg")
    if not ffprobe:
        missing_runtime.append("FFprobe")
    if not gsap:
        missing_runtime.append("GSAP browser runtime")
    if not hyperframes:
        missing_runtime.append("HyperFrames CLI")

    warnings = []
    if not os.environ.get("ELEVENLABS_API_KEY") and not (
        project_root / ".codex" / "skills" / "video-use" / ".env"
    ).is_file():
        warnings.append(
            "ELEVENLABS_API_KEY is absent; pass an existing transcript JSON or configure Scribe at runtime."
        )

    return {
        "ready": not missing_skills and not missing_runtime,
        "projectRoot": str(project_root),
        "missingRequiredSkills": missing_skills,
        "missingRuntime": missing_runtime,
        "conditionalSkills": declaration["conditionalSkills"],
        "onDemandSkills": declaration["onDemandSkills"],
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_root = Path(__file__).resolve().parents[4]
    parser.add_argument("--project-root", type=Path, default=default_root)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = check(args.project_root.resolve())
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("READY" if result["ready"] else "NOT READY")
        for name in result["missingRequiredSkills"]:
            print(f"MISSING SKILL: {name}")
        for name in result["missingRuntime"]:
            print(f"MISSING RUNTIME: {name}")
        for warning in result["warnings"]:
            print(f"WARN: {warning}")
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
