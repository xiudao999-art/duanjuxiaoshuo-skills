from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


TURN_TYPES = {"relationship", "evidence", "identity", "goal", "consequence", "allegiance", "none"}
STORY_TYPES = {"continuous_plot", "character_arc", "relationship_arc", "action_payoff", "mystery_reveal", "special_theme"}
LENSES = {
    "linear_escalation", "result_first", "mystery_reveal", "causal_domino",
    "countdown_rescue", "parallel_contrast", "character_growth", "hidden_identity",
    "romance_progression", "alliance_betrayal", "villain_downfall", "action_escalation",
    "status_reversal", "family_redemption", "motif_clue", "dialogue_showdown",
}
FAMILY_IDS = {f"F{i:02d}" for i in range(1, 11)}


def validate_story_selection(job: dict, known_event_ids: set[str], errors: list[str]) -> None:
    family_id = job.get("familyId")
    if family_id not in FAMILY_IDS:
        errors.append("familyId is required and must be F01 through F10")

    selection = job.get("storySelection") or {}
    if not str(selection.get("patternId", "")).strip():
        errors.append("storySelection.patternId is required")
    if not str(selection.get("hookPromise", "")).strip():
        errors.append("storySelection.hookPromise is required")

    slots = selection.get("requiredSlots") or []
    if len(slots) < 5:
        errors.append("storySelection.requiredSlots must contain at least 5 category-specific slots")
    slot_names: set[str] = set()
    slot_event_ids: set[str] = set()
    for index, slot in enumerate(slots, 1):
        name = str(slot.get("slot", "")).strip()
        if not name or name in slot_names:
            errors.append(f"storySelection required slot {index} must have a unique name")
        slot_names.add(name)
        ids = slot.get("eventIds") or []
        if not ids or any(not str(event_id).strip() for event_id in ids):
            errors.append(f"storySelection slot {name or index} needs supported eventIds")
        slot_event_ids.update(str(event_id) for event_id in ids)

    grades = selection.get("eventGrades") or {}
    graded: dict[str, list[str]] = {}
    all_graded: list[str] = []
    for grade in ("A", "B", "C", "D"):
        values = grades.get(grade)
        if not isinstance(values, list):
            errors.append(f"storySelection.eventGrades.{grade} must be a list")
            values = []
        clean = [str(event_id) for event_id in values if str(event_id).strip()]
        graded[grade] = clean
        all_graded.extend(clean)
    if len(graded.get("A", [])) < 3:
        errors.append("storySelection.eventGrades.A must contain at least 3 causal-spine events")
    if len(all_graded) != len(set(all_graded)):
        errors.append("an event ID may appear in only one A/B/C/D grade")

    selected = set(graded.get("A", [])) | set(graded.get("B", [])) | set(graded.get("C", []))
    if not slot_event_ids.issubset(selected):
        errors.append("required slot eventIds must be selected as A, B, or C rather than D/ungraded")
    payoff = {str(event_id) for event_id in (selection.get("payoffEvidenceEventIds") or [])}
    if not payoff:
        errors.append("storySelection.payoffEvidenceEventIds is required")
    elif not payoff.issubset(selected):
        errors.append("payoffEvidenceEventIds must be selected as A, B, or C")
    if known_event_ids and not selected.issubset(known_event_ids):
        errors.append("storySelection contains selected event IDs outside job.eventIds")


def validate(job: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    schema_version = job.get("schemaVersion")
    if schema_version not in {1, 2}:
        errors.append("schemaVersion must be 1 or 2")

    planning_mode = job.get("planningMode", "continuous_arc")
    if planning_mode not in {"continuous_arc", "overlapping_question"}:
        errors.append("planningMode must be continuous_arc or overlapping_question")
    if job.get("storyType") not in STORY_TYPES:
        errors.append("storyType is required and must use the production taxonomy")
    if not str(job.get("storyTypeLabel", "")).strip():
        errors.append("storyTypeLabel is required")
    if job.get("narrativeLens") not in LENSES:
        errors.append("narrativeLens is required and unsupported")
    if not str(job.get("narrativeLensLabel", "")).strip():
        errors.append("narrativeLensLabel is required")
    if planning_mode == "overlapping_question":
        if not str(job.get("seriesPlanWindowId", "")).strip():
            errors.append("seriesPlanWindowId is required in overlapping_question mode")
        event_ids = job.get("eventIds") or []
        core_event_ids = job.get("coreEventIds") or []
        if len(event_ids) < 6 or len(event_ids) != len(set(event_ids)):
            errors.append("overlapping_question jobs require at least 6 unique eventIds")
        if len(core_event_ids) < 3 or len(core_event_ids) != len(set(core_event_ids)):
            errors.append("overlapping_question jobs require at least 3 unique coreEventIds")
        if not set(core_event_ids).issubset(set(event_ids)):
            errors.append("coreEventIds must be a subset of eventIds")
        if not str(job.get("noveltyRationale", "")).strip():
            errors.append("noveltyRationale is required in overlapping_question mode")
        filename = str(job.get("deliveryFilename", "")).strip()
        if not filename:
            errors.append("deliveryFilename is required in overlapping_question mode")
        elif str(job.get("storyTypeLabel")) not in filename or str(job.get("narrativeLensLabel")) not in filename:
            errors.append("deliveryFilename must include storyTypeLabel and narrativeLensLabel")

    if schema_version == 2:
        validate_story_selection(job, set(job.get("eventIds") or []), errors)

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
