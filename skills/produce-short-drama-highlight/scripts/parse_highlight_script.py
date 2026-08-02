from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


CN_NUMBERS = {
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
    "十一": 11, "十二": 12, "十三": 13, "十四": 14, "十五": 15,
    "十六": 16, "十七": 17, "十八": 18, "十九": 19, "二十": 20,
}

SECTION_RE = re.compile(r"^##\s+片段([一二三四五六七八九十]+)[：:]\s*(.+?)\s*$")
EPISODE_RE = re.compile(r"第\s*(\d+)\s*集")
DIALOGUE_RE = re.compile(r"^☆\s*\*\*(.+?)\*\*(?:（(.+?)）)?[：:]\s*(.+?)\s*$")


def parse(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    items: list[dict] = []
    current: dict | None = None
    in_visuals = False

    for line_no, raw in enumerate(lines, start=1):
        line = raw.strip()
        match = SECTION_RE.match(line)
        if match:
            if current:
                items.append(current)
            chinese_index, title = match.groups()
            if chinese_index not in CN_NUMBERS:
                raise ValueError(f"Unsupported Chinese index at line {line_no}: {chinese_index}")
            current = {
                "index": CN_NUMBERS[chinese_index],
                "chineseIndex": chinese_index,
                "title": title,
                "episodes": [],
                "visualRefs": [],
                "beats": [],
                "sourceLine": line_no,
            }
            in_visuals = False
            continue

        if not current:
            continue

        if line.startswith("**涉及原视频："):
            current["episodes"] = sorted({int(value) for value in EPISODE_RE.findall(line)})
            in_visuals = False
            continue
        if line == "### 画面引用":
            in_visuals = True
            continue
        if line.startswith("★"):
            in_visuals = False
            text = line[1:].strip()
            if text:
                current["beats"].append({"type": "narration", "text": text, "sourceLine": line_no})
            continue
        if line.startswith("☆"):
            in_visuals = False
            dialogue = DIALOGUE_RE.match(line)
            if not dialogue:
                raise ValueError(f"Malformed dialogue at line {line_no}: {line}")
            speaker, stage, text = dialogue.groups()
            current["beats"].append({
                "type": "dialogue",
                "speaker": speaker.strip(),
                "stage": stage.strip() if stage else None,
                "text": text.strip(),
                "sourceLine": line_no,
            })
            continue
        if in_visuals and line and not line.startswith("---") and not line.startswith("#"):
            current["visualRefs"].append(line)

    if current:
        items.append(current)

    indices = [item["index"] for item in items]
    if indices != list(range(1, len(items) + 1)):
        raise ValueError(f"Highlight indices must be continuous from 1: {indices}")
    for item in items:
        if not item["episodes"] or not item["beats"]:
            raise ValueError(f"Highlight {item['index']} lacks episodes or beats")

    return {
        "source": str(path.resolve()),
        "schemaVersion": 1,
        "count": len(items),
        "highlights": items,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse approved short-drama highlight Markdown.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    payload = parse(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Parsed {payload['count']} highlights -> {args.output}")


if __name__ == "__main__":
    main()
