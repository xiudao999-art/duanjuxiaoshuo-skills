#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


LEFT_SUFFIXES = tuple("的地得了着过们性化者")
LEFT_SUFFIX_EXCEPTIONS = (
    "性格",
    "性情",
    "性命",
    "化妆",
    "化学",
    "化验",
    # “过” is also a full lexical verb/directional prefix. These phrases may
    # legitimately begin a cue and must not be mistaken for the aspect suffix.
    "过生日",
    "过年",
    "过来",
    "过去",
)
DEFAULT_TERMS = [
    "人工智能",
    "生命周期",
    "生命周期清单",
    "产品碳足迹",
    "供应链数据",
    "可信数据空间",
    "可用不可见",
    "数据提供方",
    "数据使用方",
    "存证方",
    "居间服务方",
    "天工数据库",
    "天工LCA数据系统",
]
NUMBER_UNITS = "年月日秒分家名个条项%℃"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_srt(path: Path) -> list[dict[str, Any]]:
    cues = []
    raw = path.read_text(encoding="utf-8-sig").strip()
    for block in re.split(r"\r?\n\s*\r?\n", raw):
        lines = [line.strip() for line in block.splitlines()]
        if len(lines) < 3 or "-->" not in lines[1]:
            continue
        text_lines = [line for line in lines[2:] if line]
        cues.append(
            {
                "id": lines[0],
                "time": lines[1],
                "lines": text_lines,
                "text": "".join(text_lines),
            }
        )
    return cues


def load_terms(paths: list[Path], direct_terms: list[str]) -> list[str]:
    terms = [*DEFAULT_TERMS, *direct_terms]
    for path in paths:
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                terms.append(line)
    return sorted(set(terms), key=len, reverse=True)


def boundary_reasons(left: str, right: str, terms: list[str]) -> list[dict[str, str]]:
    reasons: list[dict[str, str]] = []
    if right.startswith(LEFT_SUFFIXES) and not right.startswith(LEFT_SUFFIX_EXCEPTIONS):
        reasons.append({"type": "left_bound_suffix_start", "value": right[0]})
    joined = left + right
    boundary = len(left)
    for term in terms:
        start = joined.find(term)
        while start >= 0:
            if start < boundary < start + len(term):
                reasons.append({"type": "protected_term_split", "value": term})
                break
            start = joined.find(term, start + 1)
    if re.search(r"\d$", left) and re.match(rf"^[{NUMBER_UNITS}]", right):
        reasons.append({"type": "number_unit_split", "value": left[-1] + right[0]})
    # A cue or line break is itself a valid separator between two complete
    # Latin words (for example ``I`` / ``dont``).  The older blanket rule
    # treated every English-to-English boundary as a split and made a wrapped
    # multi-word sentence impossible.  Actual token splits remain blocked by
    # the protected-term span check above; callers must include every source
    # Latin token in the protected-term inventory.
    unique = []
    for item in reasons:
        if item not in unique:
            unique.append(item)
    return unique


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit semantic splits across adjacent SRT cues and inside two-line cues.")
    parser.add_argument("srt", type=Path)
    parser.add_argument("--terms", action="append", default=[], type=Path, help="UTF-8 protected-term file; repeatable")
    parser.add_argument("--term", action="append", default=[], help="One protected term; repeatable")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    cues = parse_srt(args.srt)
    terms = load_terms(args.terms, args.term)
    issues: list[dict[str, Any]] = []

    for cue in cues:
        lines = cue["lines"]
        if len(lines) > 2:
            issues.append(
                {
                    "cue_id": cue["id"],
                    "time": cue["time"],
                    "boundary": "line_break",
                    "lines": lines,
                    "reasons": [{"type": "too_many_lines", "value": str(len(lines))}],
                }
            )
        for line_index, (left, right) in enumerate(zip(lines, lines[1:]), start=1):
            reasons = boundary_reasons(left, right, terms)
            if reasons:
                issues.append(
                    {
                        "cue_id": cue["id"],
                        "time": cue["time"],
                        "boundary": "line_break",
                        "line_index": line_index,
                        "left_text": left,
                        "right_text": right,
                        "reasons": reasons,
                    }
                )

    for left, right in zip(cues, cues[1:]):
        reasons = boundary_reasons(left["text"], right["text"], terms)
        if reasons:
            issues.append(
                {
                    "left_id": left["id"],
                    "right_id": right["id"],
                    "time": left["time"],
                    "boundary": "adjacent_cues",
                    "left_text": left["text"],
                    "right_text": right["text"],
                    "reasons": reasons,
                }
            )

    report = {
        "schema": "subtitle-boundary-audit-v2",
        "srt": str(args.srt.resolve()),
        "srt_sha256": sha256_file(args.srt),
        "cue_count": len(cues),
        "protected_terms": terms,
        "line_break_checked": True,
        "passed": not issues,
        "issues": issues,
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
