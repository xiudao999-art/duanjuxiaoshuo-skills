from __future__ import annotations

import argparse
import json
from pathlib import Path


TALKING_HEAD = "talking-head-large-no-rail-1080x1920"
SHORT_DRAMA = "short-drama-vsr-tight-rail-1080x1920"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def validate(config: dict) -> list[str]:
    profile = str(config.get("subtitle_style_profile") or config.get("name") or "")
    cover = ((config.get("output") or {}).get("narrationSourceSubtitleCover") or {})
    rail = cover.get("rail") or config.get("rail") or {}
    caption = config.get("caption_style") or config.get("caption") or {}
    if profile == TALKING_HEAD:
        errors = []
        if bool(rail.get("enabled", False)):
            errors.append("talking-head captions must not have a rail")
        if tuple(int(caption.get(k, -1)) for k in ("normalSize", "accentSize", "highlightSize")) != (88, 88, 96):
            errors.append("talking-head caption sizes must be 88/88/96")
        return errors
    if profile == SHORT_DRAMA:
        actual = (bool(rail.get("enabled", False)), int(rail.get("y", -1)), int(rail.get("height", -1)), int(rail.get("captionBaseline", -1)))
        errors = []
        if actual != (True, 1318, 90, 1385):
            errors.append(f"short-drama rail must be enabled/1318/90/1385, got {actual}")
        if tuple(int(caption.get(k, -1)) for k in ("normalSize", "accentSize", "highlightSize")) != (64, 64, 64):
            errors.append("short-drama caption sizes must be 64/64/64")
        return errors
    return [f"unsupported or missing subtitle_style_profile: {profile!r}"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", type=Path, nargs="+")
    args = parser.parse_args()
    failed = False
    for path in args.paths:
        errors = validate(load(path))
        print(("PASS " if not errors else "FAIL ") + str(path))
        for error in errors:
            print(f"  - {error}")
        failed = failed or bool(errors)
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
