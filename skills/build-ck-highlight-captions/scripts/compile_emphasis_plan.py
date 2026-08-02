#!/usr/bin/env python3
"""Validate and compile one reusable emphasis plan into renderer inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TEMPLATES = {
    "rise_settle",
    "char_toss",
    "stretch_reveal",
    "fade_snap",
    "light_sweep",
    "type_on",
    "legacy_zoom_streak",
}
LOW_CONFIDENCE_AUTO_SFX = {"rise_settle", "fade_snap"}
LEVEL_SCORE = {
    "L1": (4, 5),
    "L2": (6, 10),
    "L3": (8, 10),
}


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile a reusable CK emphasis plan into accent/highlight plans."
    )
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def validate(plan: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    require(plan.get("schema_version") == 1, "schema_version must be 1", errors)
    require(float(plan.get("duration", 0)) > 0, "duration must be positive", errors)

    policy = plan.get("policy") or {}
    require(
        policy.get("baseline_policy") in {"same_as_normal", "explicit"},
        "policy.baseline_policy must be same_as_normal or explicit",
        errors,
    )
    normal_baseline = policy.get("normal_baseline")
    require(isinstance(normal_baseline, (int, float)), "policy.normal_baseline is required", errors)
    if policy.get("baseline_policy") == "explicit":
        require(
            isinstance(policy.get("highlight_baseline"), (int, float)),
            "policy.highlight_baseline is required when baseline_policy is explicit",
            errors,
        )
    tolerance = policy.get("onset_tolerance_frames", 1)
    require(isinstance(tolerance, (int, float)) and 0 <= tolerance <= 1, "onset_tolerance_frames must be 0..1", errors)

    used_ids: set[str] = set()
    used_ck_cues: set[int] = set()
    for group, expected_levels in (("accents", {"L1"}), ("events", {"L2", "L3"})):
        items = plan.get(group, [])
        require(isinstance(items, list), f"{group} must be an array", errors)
        if not isinstance(items, list):
            continue
        for index, item in enumerate(items):
            label = f"{group}[{index}]"
            ident = item.get("id")
            require(isinstance(ident, str) and ident.strip(), f"{label}.id is required", errors)
            if isinstance(ident, str):
                require(ident not in used_ids, f"duplicate id: {ident}", errors)
                used_ids.add(ident)
            level = item.get("level")
            require(level in expected_levels, f"{label}.level must be one of {sorted(expected_levels)}", errors)
            score = item.get("score")
            require(isinstance(score, int) and 0 <= score <= 10, f"{label}.score must be an integer 0..10", errors)
            if level in LEVEL_SCORE and isinstance(score, int):
                low, high = LEVEL_SCORE[level]
                if not low <= score <= high:
                    warnings.append(f"{label} score {score} is unusual for {level} ({low}..{high})")
            require(bool(item.get("semantic_role")), f"{label}.semantic_role is required", errors)
            require(bool(item.get("reason")), f"{label}.reason is required", errors)
            cue_ids = item.get("cue_ids")
            require(
                isinstance(cue_ids, list) and cue_ids and all(isinstance(x, int) and x > 0 for x in cue_ids),
                f"{label}.cue_ids must contain positive integers",
                errors,
            )

            if group == "accents":
                phrase = item.get("phrase")
                require(isinstance(phrase, str) and phrase.strip(), f"{label}.phrase is required", errors)
                continue

            lines = item.get("lines")
            require(
                isinstance(lines, list) and 1 <= len(lines) <= 2 and all(isinstance(x, str) and x.strip() for x in lines),
                f"{label}.lines must contain one or two non-empty strings",
                errors,
            )
            if isinstance(lines, list):
                for line in lines:
                    if isinstance(line, str) and len(line.replace(" ", "")) > 16:
                        errors.append(f"{label} line exceeds 16 characters: {line}")
            template = item.get("template")
            require(template in TEMPLATES, f"{label}.template is unsupported: {template}", errors)
            require(
                item.get("onset_anchor") in {"phrase_first_word", "first_stressed_syllable", "payoff_word"},
                f"{label}.onset_anchor is invalid",
                errors,
            )
            require(
                item.get("hold_until") in {"complete_phrase", "complete_spoken_thought"},
                f"{label}.hold_until is invalid",
                errors,
            )
            sfx = item.get("sfx")
            require(
                sfx in {"auto", "none", None} or (isinstance(sfx, str) and sfx.strip()),
                f"{label}.sfx must be auto, none, or a file path",
                errors,
            )
            if sfx == "auto" and template in LOW_CONFIDENCE_AUTO_SFX:
                warnings.append(f"{label} uses low-confidence auto SFX for {template}; prefer none or a clean replacement")
            if isinstance(cue_ids, list):
                for cue_id in cue_ids:
                    if cue_id in used_ck_cues:
                        errors.append(f"cue {cue_id} is replaced by more than one CK event")
                    used_ck_cues.add(cue_id)

    duration = float(plan.get("duration", 0) or 0)
    event_count = len(plan.get("events", []) or [])
    density = (plan.get("policy") or {}).get("density", {})
    max_per_minute = float(density.get("max_ck_per_minute", 6))
    allowed = max(1, round(duration / 60 * max_per_minute)) if duration else 0
    if allowed and event_count > allowed:
        warnings.append(f"CK density is high: {event_count} events for {duration:.1f}s (guideline {allowed})")
    return errors, warnings


def compile_plan(plan: dict) -> tuple[dict, dict, dict]:
    policy = plan["policy"]
    normal_baseline = int(policy["normal_baseline"])
    explicit_baseline = policy.get("highlight_baseline")
    default_baseline = normal_baseline if policy["baseline_policy"] == "same_as_normal" else int(explicit_baseline)

    accents: dict[str, list[str]] = {}
    for item in plan.get("accents", []):
        for cue_id in item["cue_ids"]:
            accents.setdefault(str(cue_id), []).append(item["phrase"])

    highlights = []
    for item in plan.get("events", []):
        rendered = {
            **item,
            "baselines": item.get("baselines", [default_baseline] * len(item["lines"])),
            "sfx_offset": float(item.get("sfx_offset", 0.0)),
            "sfx_gain_db": float(item.get("sfx_gain_db", -4.0 if item.get("sfx") not in {None, "none"} else 0.0)),
        }
        highlights.append(rendered)

    audit = {
        "schema_version": 1,
        "source_plan": str(plan.get("source_plan", "emphasis-plan.json")),
        "duration": plan["duration"],
        "policy": policy,
        "counts": {"L1": len(plan.get("accents", [])), "L2_L3": len(highlights)},
        "decisions": [*plan.get("accents", []), *plan.get("events", [])],
    }
    return {"accents": accents}, {"highlights": highlights}, audit


def main() -> None:
    args = parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    plan["source_plan"] = str(args.plan)
    errors, warnings = validate(plan)
    result = {"passed": not errors, "errors": errors, "warnings": warnings}
    if errors:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    if not args.validate_only:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        accent_plan, highlight_plan, audit = compile_plan(plan)
        (args.out_dir / "accent-plan.json").write_text(json.dumps(accent_plan, ensure_ascii=False, indent=2), encoding="utf-8")
        (args.out_dir / "highlight-plan.json").write_text(json.dumps(highlight_plan, ensure_ascii=False, indent=2), encoding="utf-8")
        (args.out_dir / "emphasis-audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        result["outputs"] = {
            "accent_plan": str(args.out_dir / "accent-plan.json"),
            "highlight_plan": str(args.out_dir / "highlight-plan.json"),
            "audit": str(args.out_dir / "emphasis-audit.json"),
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
