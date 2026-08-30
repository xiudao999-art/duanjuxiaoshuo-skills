from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


STORY_TYPES = {
    "continuous_plot",
    "character_arc",
    "relationship_arc",
    "action_payoff",
    "mystery_reveal",
    "special_theme",
}

LENSES = {
    "linear_escalation",
    "result_first",
    "mystery_reveal",
    "causal_domino",
    "countdown_rescue",
    "parallel_contrast",
    "character_growth",
    "hidden_identity",
    "romance_progression",
    "alliance_betrayal",
    "villain_downfall",
    "action_escalation",
    "status_reversal",
    "family_redemption",
    "motif_clue",
    "dialogue_showdown",
}
FAMILY_IDS = {f"F{i:02d}" for i in range(1, 11)}

SCORE_LIMITS = {
    "hook": 20,
    "causalCoherence": 20,
    "escalation": 15,
    "evidence": 15,
    "payoff": 15,
    "novelty": 10,
    "editability": 5,
}


def normalized_text(value: object) -> str:
    return re.sub(r"[\W_]+", "", str(value or "").casefold())


def validate_story_selection(window: dict, label: str, known_event_ids: set[str], errors: list[str]) -> None:
    family_id = window.get("familyId")
    if family_id not in FAMILY_IDS:
        errors.append(f"{label} familyId is required and must be F01 through F10")

    selection = window.get("storySelection") or {}
    if not str(selection.get("patternId", "")).strip():
        errors.append(f"{label} missing storySelection.patternId")
    if not str(selection.get("hookPromise", "")).strip():
        errors.append(f"{label} missing storySelection.hookPromise")

    slots = selection.get("requiredSlots") or []
    if len(slots) < 5:
        errors.append(f"{label} storySelection.requiredSlots needs at least 5 slots")
    slot_names: set[str] = set()
    slot_event_ids: set[str] = set()
    for index, slot in enumerate(slots, 1):
        name = str(slot.get("slot", "")).strip()
        if not name or name in slot_names:
            errors.append(f"{label} required slot {index} must have a unique name")
        slot_names.add(name)
        ids = slot.get("eventIds") or []
        if not ids or any(not str(event_id).strip() for event_id in ids):
            errors.append(f"{label} slot {name or index} needs supported eventIds")
        slot_event_ids.update(str(event_id) for event_id in ids)

    grades = selection.get("eventGrades") or {}
    graded: dict[str, list[str]] = {}
    all_graded: list[str] = []
    for grade in ("A", "B", "C", "D"):
        values = grades.get(grade)
        if not isinstance(values, list):
            errors.append(f"{label} storySelection.eventGrades.{grade} must be a list")
            values = []
        clean = [str(event_id) for event_id in values if str(event_id).strip()]
        graded[grade] = clean
        all_graded.extend(clean)
    if len(graded.get("A", [])) < 3:
        errors.append(f"{label} needs at least 3 A-grade causal-spine events")
    if len(all_graded) != len(set(all_graded)):
        errors.append(f"{label} assigns an event ID to more than one A/B/C/D grade")

    selected = set(graded.get("A", [])) | set(graded.get("B", [])) | set(graded.get("C", []))
    if not slot_event_ids.issubset(selected):
        errors.append(f"{label} required slot eventIds must be selected as A, B, or C")
    payoff = {str(event_id) for event_id in (selection.get("payoffEvidenceEventIds") or [])}
    if not payoff:
        errors.append(f"{label} missing storySelection.payoffEvidenceEventIds")
    elif not payoff.issubset(selected):
        errors.append(f"{label} payoffEvidenceEventIds must be selected as A, B, or C")
    if known_event_ids and not selected.issubset(known_event_ids):
        errors.append(f"{label} storySelection contains event IDs outside eventIds")


def validate(plan: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    schema_version = plan.get("schemaVersion")
    if schema_version not in {1, 2}:
        errors.append("schemaVersion must be 1 or 2")
    if plan.get("planningMode") != "overlapping_question":
        errors.append("planningMode must be overlapping_question")
    if not str(plan.get("dramaTitle", "")).strip():
        errors.append("dramaTitle is required")

    total = plan.get("totalEpisodes")
    if not isinstance(total, int) or total < 4:
        errors.append("totalEpisodes must be an integer of at least 4")
        total = 0

    target = plan.get("targetWindowCount") or {}
    target_min, target_max = target.get("min"), target.get("max")
    if not isinstance(target_min, int) or not isinstance(target_max, int) or not 1 <= target_min <= target_max:
        errors.append("targetWindowCount must contain valid integer min/max values")
    elif 32 <= total <= 50 and (target_min < 10 or target_max > 16):
        warnings.append("a normal 32–50 episode drama should usually target 10–16 overlapping-question windows")

    corpus = plan.get("corpus") or {}
    for key in ("fullTranscriptPath", "wordTimingPath", "eventLedgerPath", "storyGraphPath"):
        if not str(corpus.get(key, "")).strip():
            errors.append(f"corpus.{key} is required")
    transcribed = corpus.get("transcribedEpisodes") or []
    if transcribed != sorted(set(transcribed)):
        errors.append("corpus.transcribedEpisodes must be sorted and unique")
    if total and transcribed != list(range(1, total + 1)):
        errors.append("the full series must be transcribed before overlapping windows are approved")

    policy = plan.get("reusePolicy") or {}
    if policy.get("allowEpisodeOverlap") is not True:
        errors.append("reusePolicy.allowEpisodeOverlap must be true for this planning mode")
    max_overlap = policy.get("maximumCoreEventOverlapRatio", 0.4)
    if not isinstance(max_overlap, (int, float)) or not 0 <= max_overlap <= 0.4:
        errors.append("maximumCoreEventOverlapRatio must be between 0 and 0.40")
        max_overlap = 0.4
    iconic_uses = policy.get("maximumIconicShotUses")
    if not isinstance(iconic_uses, int) or not 1 <= iconic_uses <= 2:
        errors.append("maximumIconicShotUses must be 1 or 2")

    windows = plan.get("windows") or []
    if isinstance(target_min, int) and isinstance(target_max, int) and not target_min <= len(windows) <= target_max:
        errors.append(f"windows must contain {target_min} to {target_max} approved windows")

    ids: set[str] = set()
    questions: dict[str, str] = {}
    filenames: set[str] = set()
    core_by_window: dict[str, set[str]] = {}

    for index, window in enumerate(windows, 1):
        wid = str(window.get("id", "")).strip()
        label = wid or f"window {index}"
        if not wid or wid in ids:
            errors.append(f"window {index} must have a unique id")
        ids.add(wid)

        story_type = window.get("storyType")
        if story_type not in STORY_TYPES:
            errors.append(f"{label} has unsupported storyType={story_type}")
        if not str(window.get("storyTypeLabel", "")).strip():
            errors.append(f"{label} missing storyTypeLabel")
        lens = window.get("narrativeLens")
        if lens not in LENSES:
            errors.append(f"{label} has unsupported narrativeLens={lens}")
        if not str(window.get("narrativeLensLabel", "")).strip():
            errors.append(f"{label} missing narrativeLensLabel")

        question = str(window.get("centralQuestion", "")).strip()
        normalized_question = normalized_text(question)
        if not normalized_question:
            errors.append(f"{label} missing centralQuestion")
        elif normalized_question in questions:
            errors.append(f"{label} duplicates the central question of {questions[normalized_question]}")
        else:
            questions[normalized_question] = label
        if not str(window.get("payoff", "")).strip():
            errors.append(f"{label} missing payoff")
        if not str(window.get("noveltyRationale", "")).strip():
            errors.append(f"{label} missing noveltyRationale")

        episodes = window.get("episodes") or []
        if not 4 <= len(episodes) <= 8:
            errors.append(f"{label} must cover 4 to 8 episodes")
        if episodes != sorted(set(episodes)):
            errors.append(f"{label} episodes must be sorted and unique")
        if any(not isinstance(ep, int) or ep < 1 or (total and ep > total) for ep in episodes):
            errors.append(f"{label} references an episode outside the series")
        if episodes and episodes != list(range(episodes[0], episodes[-1] + 1)):
            if not (window.get("skipReasons") or []):
                errors.append(f"{label} skips episodes without skipReasons")
            else:
                warnings.append(f"{label} episode gaps require causal-bridge review")

        events = window.get("eventIds") or []
        core = window.get("coreEventIds") or []
        if len(events) < 6 or len(events) != len(set(events)):
            errors.append(f"{label} needs at least 6 unique eventIds")
        if len(core) < 3 or len(core) != len(set(core)):
            errors.append(f"{label} needs at least 3 unique coreEventIds")
        if not set(core).issubset(set(events)):
            errors.append(f"{label} coreEventIds must be a subset of eventIds")
        hook = window.get("hookEventId")
        if hook not in events:
            errors.append(f"{label} hookEventId must appear in eventIds")
        core_by_window[label] = set(core)

        if schema_version == 2:
            validate_story_selection(window, label, set(events), errors)

        score = window.get("score") or {}
        total_score = 0.0
        for key, limit in SCORE_LIMITS.items():
            value = score.get(key)
            if not isinstance(value, (int, float)) or not 0 <= value <= limit:
                errors.append(f"{label} score.{key} must be between 0 and {limit}")
            else:
                total_score += value
        if total_score < 72:
            warnings.append(f"{label} score is {total_score:.1f}; recommended minimum is 72")

        filename = str(window.get("deliveryFilename", "")).strip()
        if not filename:
            errors.append(f"{label} missing deliveryFilename")
        elif filename in filenames:
            errors.append(f"{label} duplicates a deliveryFilename")
        else:
            filenames.add(filename)
        if filename and (str(window.get("storyTypeLabel", "")) not in filename or str(window.get("narrativeLensLabel", "")) not in filename):
            errors.append(f"{label} deliveryFilename must include storyTypeLabel and narrativeLensLabel")

    labels = list(core_by_window)
    for i, left in enumerate(labels):
        for right in labels[i + 1 :]:
            a, b = core_by_window[left], core_by_window[right]
            if not a or not b:
                continue
            ratio = len(a & b) / min(len(a), len(b))
            if ratio > max_overlap:
                errors.append(f"{left} and {right} core-event overlap is {ratio:.2f}; maximum is {max_overlap:.2f}")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a whole-series overlapping recap plan")
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8-sig"))
    errors, warnings = validate(plan)
    print(json.dumps({"passed": not errors, "errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
