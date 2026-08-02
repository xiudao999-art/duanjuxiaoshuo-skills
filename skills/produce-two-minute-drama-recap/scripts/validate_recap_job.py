from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


TURN_TYPES = {"relationship", "evidence", "identity", "goal", "consequence", "allegiance", "none"}


def validate(job: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if job.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")

    duration = job.get("targetDurationSeconds")
    if not isinstance(duration, (int, float)) or not 110 <= duration <= 130:
        errors.append("targetDurationSeconds must be between 110 and 130")

    episode_range = job.get("episodeRange") or {}
    episodes = episode_range.get("episodes") or []
    if not 4 <= len(episodes) <= 8:
        errors.append("episodeRange.episodes must contain 4 to 8 episodes")
    if episodes != sorted(set(episodes)):
        errors.append("episodeRange.episodes must be sorted and unique")
    if episodes and episodes != list(range(episodes[0], episodes[-1] + 1)):
        reasons = episode_range.get("skipReasons") or []
        if not reasons:
            errors.append("episodes must be consecutive unless skipReasons explains every gap")
        else:
            warnings.append("episode gaps require editorial review")
    if episodes and (episode_range.get("start") != episodes[0] or episode_range.get("end") != episodes[-1]):
        errors.append("episodeRange.start/end must match the episodes list")

    if not str(job.get("centralQuestion", "")).strip():
        errors.append("centralQuestion is required")
    if not str(job.get("payoffDecision", "")).strip():
        errors.append("payoffDecision is required")

    units = job.get("units") or []
    if not 6 <= len(units) <= 8:
        errors.append("units must contain 6 to 8 causal story units")
    if units and units[0].get("function") != "hook":
        errors.append("the first unit must have function=hook")
    turns = 0
    narration_text = ""
    unit_ids = set()
    for i, unit in enumerate(units, 1):
        uid = unit.get("id")
        if not uid or uid in unit_ids:
            errors.append(f"unit {i} must have a unique id")
        unit_ids.add(uid)
        for key in ("function", "action", "reaction", "consequence", "narration"):
            if not str(unit.get(key, "")).strip():
                errors.append(f"unit {uid or i} missing {key}")
        turn = unit.get("turnType", "none")
        if turn not in TURN_TYPES:
            errors.append(f"unit {uid or i} has unsupported turnType={turn}")
        if turn != "none":
            turns += 1
        for episode in unit.get("episodes") or []:
            if episode not in episodes:
                errors.append(f"unit {uid or i} references episode {episode} outside the bound range")
        evidence = unit.get("visualEvidence") or []
        if not evidence:
            errors.append(f"unit {uid or i} has no visualEvidence")
        for ev in evidence:
            if ev.get("episode") not in episodes:
                errors.append(f"unit {uid or i} evidence references an unbound episode")
            if not isinstance(ev.get("start"), (int, float)) or not isinstance(ev.get("end"), (int, float)) or ev.get("end", 0) <= ev.get("start", 0):
                errors.append(f"unit {uid or i} has an invalid evidence range")
        narration_text += str(unit.get("narration", ""))
    if turns < 3:
        errors.append("at least 3 units must contain a real model-changing turn")

    han_count = len(re.findall(r"[\u4e00-\u9fff]", narration_text))
    declared = job.get("narrationCharacterCount")
    if declared not in (None, 0) and declared != han_count:
        errors.append(f"narrationCharacterCount={declared} but measured {han_count}")
    if han_count and not 500 <= han_count <= 650:
        warnings.append(f"narration has {han_count} Chinese characters; recommended range is 500 to 650")

    dialogues = job.get("dialogues") or []
    if not 2 <= len(dialogues) <= 4:
        errors.append("dialogues must contain 2 to 4 clips")
    dialogue_total = 0.0
    dialogue_ids = set()
    for i, dialogue in enumerate(dialogues, 1):
        did = dialogue.get("id")
        if not did or did in dialogue_ids:
            errors.append(f"dialogue {i} must have a unique id")
        dialogue_ids.add(did)
        if dialogue.get("episode") not in episodes:
            errors.append(f"dialogue {did or i} references an unbound episode")
        if dialogue.get("completeSentence") is not True:
            errors.append(f"dialogue {did or i} must set completeSentence=true")
        if not str(dialogue.get("text", "")).strip():
            errors.append(f"dialogue {did or i} missing verbatim text")
        start, end = dialogue.get("start"), dialogue.get("end")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or end <= start:
            errors.append(f"dialogue {did or i} has an invalid range")
            continue
        measured = end - start
        declared_duration = dialogue.get("durationSeconds", measured)
        if abs(declared_duration - measured) > 0.15:
            warnings.append(f"dialogue {did or i} declared duration differs from range")
        dialogue_total += measured
        post = dialogue.get("postRollSeconds")
        if not isinstance(post, (int, float)) or not 0.30 <= post <= 0.50:
            warnings.append(f"dialogue {did or i} postRollSeconds should normally be 0.30 to 0.50")
    if dialogues and not 18 <= dialogue_total <= 35:
        warnings.append(f"dialogue total is {dialogue_total:.2f}s; recommended range is 18 to 35s")

    referenced_dialogues = {d for u in units for d in (u.get("dialogueIds") or [])}
    unknown = referenced_dialogues - dialogue_ids
    if unknown:
        errors.append(f"units reference unknown dialogue ids: {sorted(unknown)}")

    output = job.get("output") or {}
    if output.get("narrationSpeed") != 1.25:
        warnings.append("output.narrationSpeed differs from the established 1.25x narration style")
    if output.get("sourcePlaybackSpeed") != 1.0:
        errors.append("output.sourcePlaybackSpeed must be 1.0 for original-speed drama footage")
    if output.get("blockSpeechLoudnessLufs") is None:
        warnings.append("output.blockSpeechLoudnessLufs should declare the shared narration/dialogue target")
    if output.get("displayPunctuation") is not False:
        warnings.append("displayPunctuation should be false for the established caption style")
    if output.get("captionWordSafe") is not True:
        errors.append("output.captionWordSafe must be true")
    font_size = output.get("captionFontSizePx")
    line_gap = output.get("twoLineBaselineGapPx")
    minimum_gap_em = output.get("minimumTwoLineGapEm", 1.65)
    if not isinstance(font_size, (int, float)) or font_size <= 0:
        errors.append("output.captionFontSizePx must be a positive number")
    if not isinstance(line_gap, (int, float)) or line_gap <= 0:
        errors.append("output.twoLineBaselineGapPx must be a positive number")
    if isinstance(font_size, (int, float)) and font_size > 0 and isinstance(line_gap, (int, float)):
        if line_gap / font_size < minimum_gap_em:
            errors.append(
                f"two-line caption baseline gap is {line_gap / font_size:.2f}em; minimum is {minimum_gap_em:.2f}em"
            )
    tail = output.get("finalNarrationTailSeconds")
    if not isinstance(tail, (int, float)) or tail < 0.45:
        errors.append("output.finalNarrationTailSeconds must be at least 0.45")
    measured_tail = output.get("minimumMeasuredTailSilenceSeconds")
    if not isinstance(measured_tail, (int, float)) or measured_tail < 0.35:
        errors.append("output.minimumMeasuredTailSilenceSeconds must be at least 0.35")
    if not str(output.get("sourceNotice", "")).strip():
        errors.append("output.sourceNotice is required")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a two-minute drama recap job plan")
    parser.add_argument("job", type=Path)
    args = parser.parse_args()
    job = json.loads(args.job.read_text(encoding="utf-8-sig"))
    errors, warnings = validate(job)
    print(json.dumps({"passed": not errors, "errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
