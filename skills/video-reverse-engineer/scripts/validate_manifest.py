#!/usr/bin/env python3
"""Dependency-free structural validation for ReconstructionManifest v1."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


ALLOWED_TRANSITIONS = {
    "none", "hard_cut", "fade", "fade_through_black", "cross_dissolve", "whip_pan",
    "velocity_matched_whip_pan", "zoom", "occlusion_cut", "action_match", "montage",
    "insert", "continuous", "custom",
}


def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schemaVersion") != "1.0": errors.append("schemaVersion must be '1.0'")
    source = data.get("source") or {}; duration = source.get("duration")
    if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        errors.append("source.duration must be a positive finite number"); duration = 0
    shots = data.get("shots")
    if not isinstance(shots, list) or not shots:
        errors.append("shots must be a non-empty array"); shots = []
    ids: set[str] = set(); cursor = 0.0
    for index, shot in enumerate(shots):
        path = f"shots[{index}]"; sid = shot.get("id")
        if not isinstance(sid, str) or not sid: errors.append(f"{path}.id is required")
        elif sid in ids: errors.append(f"{path}.id is duplicated: {sid}")
        else: ids.add(sid)
        span = shot.get("range") or {}; start, end = span.get("start"), span.get("end")
        if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in (start, end)):
            errors.append(f"{path}.range must contain finite start/end"); continue
        if end <= start: errors.append(f"{path}.range end must be after start")
        if abs(start - cursor) > 0.02: errors.append(f"{path} breaks timeline coverage at {cursor:.6f}->{start:.6f}")
        cursor = end
        for b, beat in enumerate(shot.get("beats") or []):
            br = beat.get("range") or {}
            if br.get("start", start) < start - 1e-6 or br.get("end", end) > end + 1e-6:
                errors.append(f"{path}.beats[{b}] falls outside its shot")
        for key in ("transitionIn", "transitionOut"):
            t = shot.get(key) or {}; kind = t.get("type", "none")
            if kind not in ALLOWED_TRANSITIONS: errors.append(f"{path}.{key}.type is unsupported: {kind}")
    if shots and abs(cursor - float(duration)) > 0.02: errors.append(f"shots end at {cursor:.6f}, source ends at {duration:.6f}")
    words = ((data.get("audio") or {}).get("words") or []); last = -1.0
    for i, word in enumerate(words):
        start, end = word.get("start"), word.get("end")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or end < start:
            errors.append(f"audio.words[{i}] has invalid time"); continue
        if start + 1e-6 < last: errors.append(f"audio.words[{i}] is not ordered")
        last = end
    walk_geometry(data, "$", errors)
    for i, item in enumerate(data.get("reviewFlags") or []):
        if item.get("severity") not in ("info", "warning", "error"):
            errors.append(f"reviewFlags[{i}].severity is invalid")
    return errors


def walk_geometry(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        if all(k in value for k in ("x", "y", "width", "height")):
            for key in ("x", "y", "width", "height"):
                number = value[key]
                if not isinstance(number, (int, float)) or not math.isfinite(number) or not 0 <= number <= 1:
                    errors.append(f"{path}.{key} must be normalized to [0,1]")
        for key, child in value.items(): walk_geometry(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value): walk_geometry(child, f"{path}[{index}]", errors)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument("manifest", type=Path); args = ap.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8-sig")); errors = validate(data)
    if errors:
        for error in errors: print(f"ERROR: {error}")
        return 1
    print(f"OK: {args.manifest} ({len(data['shots'])} shots)")
    return 0


if __name__ == "__main__": raise SystemExit(main())
