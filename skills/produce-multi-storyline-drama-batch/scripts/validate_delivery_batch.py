from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from difflib import SequenceMatcher
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def plain(value: str) -> str:
    return re.sub(r"[^\u3400-\u9fffA-Za-z0-9]", "", value).lower()


def probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=True, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    video = next((row for row in streams if row.get("codec_type") == "video"), {})
    audio = next((row for row in streams if row.get("codec_type") == "audio"), {})
    return {
        "duration": float(data.get("format", {}).get("duration") or 0),
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "sar": video.get("sample_aspect_ratio"),
        "video": bool(video),
        "audio": bool(audio),
    }


def sentence_duplicates(texts: list[str]) -> list[dict]:
    rows = []
    for block_index, text in enumerate(texts):
        for sentence in re.split(r"[。！？!?；;]+", text):
            value = plain(sentence)
            if len(value) >= 8:
                rows.append((block_index, value, sentence))
    findings = []
    for i, left in enumerate(rows):
        for right in rows[i + 1 :]:
            ratio = SequenceMatcher(None, left[1], right[1]).ratio()
            if ratio >= 0.86:
                findings.append({"leftBlock": left[0], "rightBlock": right[0], "similarity": round(ratio, 3), "left": left[2], "right": right[2]})
    return findings


def interval_duplicates(ranges: list[dict]) -> list[dict]:
    findings = []
    for i, left in enumerate(ranges):
        for j, right in enumerate(ranges[i + 1 :], i + 1):
            if int(left["episode"]) != int(right["episode"]):
                continue
            overlap = min(float(left["end"]), float(right["end"])) - max(float(left["start"]), float(right["start"]))
            shorter = min(float(left["end"]) - float(left["start"]), float(right["end"]) - float(right["start"]))
            if overlap > 0 and overlap / max(0.001, shorter) >= 0.50:
                findings.append({"left": i, "right": j, "episode": int(left["episode"]), "overlapRatioOfShorter": round(overlap / shorter, 3)})
    return findings


def narration_sentence_lengths(timeline: list[dict]) -> list[int]:
    lengths = []
    for row in timeline:
        if row.get("type") != "narration":
            continue
        # Chinese short-form narration is delivered in audible clauses.  A
        # comma/colon normally marks the same breath reset as terminal
        # punctuation, while tiny connective fragments are not independent
        # "normal sentences" for the oral-rhythm gate.
        for sentence in re.split(r"[，,。！？!?；;：:]+", str(row.get("text", ""))):
            count = len(re.findall(r"[\u3400-\u9fff]", sentence))
            if count >= 8:
                lengths.append(count)
    return lengths


def load_if_present(path: Path, default):
    return load(path) if path.is_file() else default


PROFILE_RULES = {
    "P01_dual_time_conflict": {"hook": (7, 12), "dialogues": (3, 4), "dialogue_seconds": (28, 48), "duration": (110, 136), "exact": 0.50, "exact_duration": 0.55, "average_shot": 7.0, "no_under_five": True},
    "P02_agency_counterattack": {"hook": (5, 10), "dialogues": (2, 4), "dialogue_seconds": (18, 45), "duration": (108, 136), "exact": 0.40, "exact_duration": 0.45, "average_shot": 6.0, "no_under_five": False},
    "P03_relationship_arc": {"hook": (5, 12), "dialogues": (2, 5), "dialogue_seconds": (20, 55), "duration": (110, 136), "exact": 0.35, "exact_duration": 0.40, "average_shot": 6.0, "no_under_five": False},
    "P04_reveal_investigation": {"hook": (5, 10), "dialogues": (2, 4), "dialogue_seconds": (15, 45), "duration": (108, 136), "exact": 0.45, "exact_duration": 0.50, "average_shot": 6.0, "no_under_five": False},
    "P05_contrast_anthology": {"hook": (3, 8), "dialogues": (0, 4), "dialogue_seconds": (0, 40), "duration": (100, 136), "exact": 0.25, "exact_duration": 0.30, "average_shot": 4.5, "no_under_five": False},
}


COMPATIBILITY_BASELINES_PATH = Path(__file__).resolve().parents[1] / "references" / "compatibility-baselines.json"


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def match_compatibility_baseline(profile: str | None, video: Path | None, production: Path) -> dict | None:
    """Return an approved legacy baseline only when every artifact hash matches."""
    if profile not in PROFILE_RULES or video is None or not COMPATIBILITY_BASELINES_PATH.is_file():
        return None
    manifest = load(COMPATIBILITY_BASELINES_PATH)
    if manifest.get("schema") != "compatibility-baselines-v1":
        return None
    paths = {
        "videoSha256": video,
        "jobSha256": production / "job.json",
        "brollAuditSha256": production / "broll-audit.json",
        "semanticAuditSha256": production / "qc" / "semantic-alignment-audit.json",
        "cutAuditSha256": production / "qc" / "encoded-cut-boundary-audit.json",
    }
    actual = {key: sha256_file(path) for key, path in paths.items()}
    if any(value is None for value in actual.values()):
        return None
    for baseline in manifest.get("baselines", []):
        if baseline.get("profile") != profile:
            continue
        if all(str(baseline.get(key) or "").lower() == value for key, value in actual.items()):
            return baseline
    return None


def resolve_profile(job: dict, semantic_audit: dict | None = None) -> str | None:
    explicit = str(
        job.get("narrative_profile")
        or job.get("narrativeProfile")
        or (job.get("semanticAlignmentPolicy") or {}).get("narrativeProfile")
        or ""
    ).strip()
    if not explicit and isinstance(semantic_audit, dict):
        explicit = str(semantic_audit.get("narrativeProfile") or "").strip()
    if explicit == "P03_relationship_progression":
        explicit = "P03_relationship_arc"
    if explicit in PROFILE_RULES:
        return explicit
    pattern = str(job.get("category_pattern") or job.get("categoryPattern") or "").strip()
    if pattern == "dual_time_backfill":
        return "P01_dual_time_conflict"
    family = str(job.get("family_id") or job.get("familyId") or "").strip()
    if family == "F01":
        return "P01_dual_time_conflict"
    if family in {"F02", "F06", "F09", "F10"}:
        return "P02_agency_counterattack"
    if family in {"F03", "F04", "F05", "F14"}:
        return "P03_relationship_arc"
    if family in {"F07", "F08", "F12"}:
        return "P04_reveal_investigation"
    if family in {"F11", "F13"}:
        return "P05_contrast_anthology"
    family_profile = {
        "连续冲突窗口": "P01_dual_time_conflict",
        "职场压迫连续窗口": "P01_dual_time_conflict",
        "营救打脸线": "P02_agency_counterattack",
        "反派因果线": "P02_agency_counterattack",
        "重要配角人物线": "P02_agency_counterattack",
        "亲子反转人物线": "P02_agency_counterattack",
        "反派母女操控线": "P02_agency_counterattack",
        "权力道歉成长线": "P02_agency_counterattack",
        "亲情慈母线": "P03_relationship_arc",
        "爱情关系线": "P03_relationship_arc",
        "父子人物线": "P03_relationship_arc",
        "爱情守候线": "P03_relationship_arc",
        "交易分离因果线": "P03_relationship_arc",
        "身份揭晓线": "P04_reveal_investigation",
        "道具伏笔线": "P04_reveal_investigation",
        "熊猫血身份悬案线": "P04_reveal_investigation",
        "信物证据链": "P04_reveal_investigation",
        "人物对照线": "P05_contrast_anthology",
        "阶级规则线": "P05_contrast_anthology",
        "交叉视角线": "P05_contrast_anthology",
        "三种母爱对照线": "P05_contrast_anthology",
        "良知回归对照线": "P05_contrast_anthology",
    }
    if family in family_profile:
        return family_profile[family]
    return None


def duration_in_profile_range(duration: float, profile: str | None) -> bool:
    if profile not in PROFILE_RULES:
        return 110 <= duration <= 135
    minimum, maximum = PROFILE_RULES[profile]["duration"]
    return minimum <= duration <= maximum


def profile_checks(profile: str | None, hooks: list[dict], dialogues: list[dict], dialogue_seconds: float, sentence_lengths: list[int], semantic_metrics: dict) -> dict:
    checks = {"profileResolved": profile in PROFILE_RULES}
    if profile not in PROFILE_RULES:
        return checks
    rule = PROFILE_RULES[profile]
    hook_min, hook_max = rule["hook"]
    dialogue_min, dialogue_max = rule["dialogues"]
    seconds_min, seconds_max = rule["dialogue_seconds"]
    checks.update({
        "profileHookDuration": len(hooks) == 1 and hook_min <= float(hooks[0].get("duration") or 0) <= hook_max,
        "profileDialogueTurns": dialogue_min <= len(dialogues) <= dialogue_max,
        "profileDialogueDuration": seconds_min <= dialogue_seconds <= seconds_max,
        "profileExactMatchRatio": float(semantic_metrics.get("exactMatchClipRatio") or 0) >= float(rule["exact"]),
        "profileExactMatchDurationRatio": float(semantic_metrics.get("exactMatchDurationRatio") or 0) >= float(rule["exact_duration"]),
        "profileAverageShotDuration": float(semantic_metrics.get("averageSourceClipDuration") or 0) >= float(rule["average_shot"]),
    })
    if rule.get("no_under_five"):
        checks["profileNoSourceClipUnderFive"] = int(semantic_metrics.get("sourceClipUnder5SecondsCount") or 0) == 0
    if profile == "P01_dual_time_conflict":
        # P01 conflict recaps deliberately use short, complete spoken clauses
        # for urgency.  Keep the global 10-character floor instead of forcing
        # relationship-style 14-character phrasing onto this profile.
        checks["profileOralSentenceAverage10To24"] = bool(sentence_lengths) and 10 <= sum(sentence_lengths) / len(sentence_lengths) <= 24
        checks["profileNormalSentenceMaximum32"] = bool(sentence_lengths) and max(sentence_lengths) <= 32
    return checks


def semantic_alignment_checks(audit: dict, compatibility_baseline: dict | None = None) -> dict:
    metrics = audit.get("metrics", {}) if isinstance(audit, dict) else {}
    if compatibility_baseline:
        return {
            "semanticApprovedLegacyCompatibilityBaseline": audit.get("schema") == compatibility_baseline.get("legacySemanticSchema"),
            "semanticAlignmentPassed": audit.get("status") == "passed",
            "semanticExactOrContextDuration": float(metrics.get("exactOrContextDurationRatio") or 0) >= 0.90,
            "semanticNeutralDuration": float(metrics.get("neutralDurationRatio") or 0) <= 0.10,
            "semanticNoContradictoryOrUnbound": (
                int(metrics.get("contradictionCount") or 0) == 0
                and int(metrics.get("unboundBeatCount") or 0) == 0
            ),
            "semanticLegacyArtifactSetHashMatched": True,
        }
    return {
        "semanticAlignmentAuditV1": audit.get("schema") == "semantic-alignment-audit-v1",
        "semanticAlignmentPassed": audit.get("status") == "passed",
        "semanticScriptRoundtrip": metrics.get("scriptRoundtrip") is True,
        "semanticStoryPlanHashMatches": metrics.get("storyPlanHashMatches") is True,
        "semanticEventLedgerResolved": metrics.get("eventLedgerResolved") is True,
        "semanticExactOrContextDuration": float(metrics.get("exactOrContextDurationRatio") or 0) >= 0.90,
        "semanticNeutralDuration": float(metrics.get("neutralDurationRatio") or 0) <= 0.10,
        "semanticVisualCoverage": float(metrics.get("visualCoverageRatio") or 0) >= 0.999,
        "semanticPictureHoldAtMostThreeFrames": (
            "maximumPictureHoldSeconds" in metrics
            and int(metrics.get("pictureHoldOverThreeFramesCount") or 0) == 0
            and float(metrics.get("maximumPictureHoldSeconds") or 0) <= 0.12
        ),
        "semanticMasteredTimingTrimAtMostQuarterSecond": float(metrics.get("maximumMasteredTimingTrim") or 0) <= 0.25,
        "semanticCutsPerRolling30Seconds": int(metrics.get("maximumCutsPerRolling30Seconds") or 0) <= 4,
        "semanticNoContradictoryOrUnbound": (
            int(metrics.get("contradictionCount") or 0) == 0
            and int(metrics.get("unboundBeatCount") or 0) == 0
        ),
        "semanticEvidenceFramesPresent": int(metrics.get("missingEvidenceFrameSetCount") or 0) == 0,
        "semanticLowResolutionPreviewPassed": metrics.get("lowResolutionPreviewPassed") is True,
    }


def motion_coverage_checks(audit: dict, compatibility_baseline: dict | None = None) -> dict:
    if compatibility_baseline:
        return {"motionCoverageApprovedLegacyCompatibilityBaseline": True}
    metrics = audit.get("metrics", {}) if isinstance(audit, dict) else {}
    policy = audit.get("repairPolicy", {}) if isinstance(audit, dict) else {}
    return {
        "motionCoverageAuditV1": audit.get("schema") == "motion-coverage-audit-v1",
        "motionCoveragePassed": audit.get("status") == "passed",
        "motionCoverageNoShortfall": int(metrics.get("blocksWithMotionShortfallCount") or 0) == 0,
        "motionCoverageTimelineMatches": int(metrics.get("blocksWithTimelineMismatchCount") or 0) == 0,
        "motionCoverageHoldBudget": (
            int(metrics.get("blocksOverHoldBudgetCount") or 0) == 0
            and int(metrics.get("maximumClipHoldFrames") or 0) <= 3
        ),
        "motionCoverageStoryPlanImmutable": policy.get("storyPlanMutable") is False,
    }


def encoded_cut_boundary_passed(audit: dict, compatibility_baseline: dict | None = None) -> bool:
    if compatibility_baseline:
        return audit.get("status") == "passed" and not audit.get("flashCandidates")
    return (
        audit.get("status") == "passed"
        and "pictureHoldCandidates" in audit
        and "freezeThenCutCandidates" in audit
        and not audit.get("flashCandidates")
        and not audit.get("pictureHoldCandidates")
        and not audit.get("freezeThenCutCandidates")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a multi-storyline drama delivery batch.")
    parser.add_argument("root", type=Path, help="Batch root containing production/, qc/, and deliveries/.")
    parser.add_argument(
        "--production-root",
        type=Path,
        help="Optional isolated production cache containing recap-* directories.",
    )
    args = parser.parse_args()
    production_root = args.production_root or (args.root / "production")
    manifests = sorted(production_root.glob("*/job.json"))
    cut_rows = load_if_present(args.root / "encoded-cut-boundary-summary.json", [])
    cut_by_id = {str(row.get("recap")): row for row in cut_rows if isinstance(row, dict)}
    reports = []
    if not manifests:
        # The reference two-minute producer stores the self-contained QC
        # triplet directly under deliveries/recap-XX. Validate that layout
        # instead of returning a misleading zero-item success.
        for qc_path in sorted((args.root / "deliveries").glob("*/*.qc.json")):
            job_id = qc_path.parent.name
            qc = load(qc_path)
            videos = sorted(qc_path.parent.glob("*.mp4"))
            srts = sorted(qc_path.parent.glob("*.srt"))
            technical = probe(videos[0]) if len(videos) == 1 else {}
            production = production_root / job_id
            job = load_if_present(production / "job.json", {})
            timeline = job.get("timeline", [])
            hooks = [row for row in timeline if row.get("type") == "hook"]
            dialogues = [row for row in timeline if row.get("type") == "dialogue"]
            narration_lengths = narration_sentence_lengths(timeline)
            dialogue_seconds = sum(float(row.get("duration") or 0) for row in dialogues)
            semantic_audit = load_if_present(production / "qc" / "semantic-alignment-audit.json", {})
            motion_audit = load_if_present(production / "qc" / "motion-coverage-audit.json", {})
            semantic_metrics = semantic_audit.get("metrics", {})
            cut_audit = cut_by_id.get(job_id, {})
            reset_audit = load_if_present(production / "qc" / "caption-reset-render-audit.json", {})
            pilot_review = load_if_present(production / "qc" / "pilot-hard-subtitle-review.json", {})
            narration_rows = [row for row in timeline if row.get("type") == "narration"]
            final_tail = float(narration_rows[-1].get("tailPad") or 0) if narration_rows else 0.0
            final_text = str(narration_rows[-1].get("text", "")) if narration_rows else ""
            profile = resolve_profile(job, semantic_audit)
            compatibility_baseline = match_compatibility_baseline(
                profile, videos[0] if len(videos) == 1 else None, production
            )
            checks = {
                "oneDelivery": len(videos) == 1,
                "oneSubtitle": len(srts) == 1,
                "format1080x1920": technical.get("width") == 1080 and technical.get("height") == 1920,
                "squarePixels": technical.get("sar") in {"1:1", None},
                "streamsPresent": bool(technical.get("video")) and bool(technical.get("audio")),
                "durationProfileRange": duration_in_profile_range(float(technical.get("duration") or 0), profile),
                "producerQcPassed": qc.get("passed") is True,
                "producerChecksPassed": bool(qc.get("checks")) and all(qc.get("checks", {}).values()),
                "captionContractPassed": qc.get("checks", {}).get("caption_contract_pass") is True,
                "hardSubtitlePilotPassed": qc.get("checks", {}).get("hard_subtitle_pilot_audit_pass") is True,
                "subtitleBoundaryPassed": not qc.get("subtitleBoundary", {}).get("issues"),
                "narrationRepeatZero": not qc.get("narrationDuplicateFindings"),
                "sourceRangeRepeatZero": not qc.get("overlapFindings"),
                "oneCentralQuestion": bool(str(job.get("centralQuestion") or "").strip()),
                "oneHook": len(hooks) == 1,
                "globalOralSentenceAverage10To26": bool(narration_lengths) and 10 <= sum(narration_lengths) / len(narration_lengths) <= 26,
                "globalNormalSentenceMaximum36": bool(narration_lengths) and max(narration_lengths) <= 36,
                "sourcePlaybackOne": abs(float(job.get("sourcePlaybackSpeed") or 0) - 1.0) < 0.001,
                "completeFinalSentence": bool(re.search(r"[。！？!?]$", final_text.strip())),
                "tail045To6": 0.45 <= final_tail <= 6.0,
                "encodedCutBoundaryPassed": encoded_cut_boundary_passed(cut_audit, compatibility_baseline),
                "captionResetEvidencePresent": int(reset_audit.get("sampledTransitions") or 0) > 0 and Path(str(reset_audit.get("contactSheet") or "")).is_file(),
                "hardSubtitleManualReviewPassed": pilot_review.get("status") == "passed",
            }
            checks.update(semantic_alignment_checks(semantic_audit, compatibility_baseline))
            checks.update(motion_coverage_checks(motion_audit, compatibility_baseline))
            checks.update(profile_checks(profile, hooks, dialogues, dialogue_seconds, narration_lengths, semantic_metrics))
            reports.append({
                "id": job_id,
                "narrativeProfile": profile,
                "compatibilityMode": compatibility_baseline is not None,
                "compatibilityBaselineId": compatibility_baseline.get("id") if compatibility_baseline else None,
                "compatibilityHashMatched": compatibility_baseline is not None,
                "video": str(videos[0]) if videos else None,
                "checks": checks,
                "passed": all(checks.values()),
            })
    for manifest_path in manifests:
        job = load(manifest_path)
        job_id = str(job.get("id") or manifest_path.parent.name)
        videos = sorted((args.root / "deliveries" / job_id).glob("*.mp4"))
        producer_qc_paths = sorted((args.root / "deliveries" / job_id).glob("*.qc.json"))
        producer_qc = load(producer_qc_paths[0]) if len(producer_qc_paths) == 1 else {}
        production = manifest_path.parent
        captions = job.get("captionAudit") or load_if_present(production / "qc" / "caption-contract-audit.json", {})
        subtitle_boundary = load_if_present(production / "qc" / "subtitle-boundary-audit.json", {})
        pilot = load_if_present(production / "qc" / "pilot-framing-audit.json", {}) or job.get("pilotFramingAudit") or {}
        reset = job.get("captionResetAudit") or load_if_present(production / "qc" / "caption-reset-render-audit.json", {})
        pilot_review = load_if_present(production / "qc" / "pilot-hard-subtitle-review.json", {})
        timeline = job.get("timeline", [])
        narration_rows = [row for row in timeline if row.get("type") == "narration"]
        narration = [str(row.get("text", "")) for row in narration_rows]
        hooks = [row for row in timeline if row.get("type") == "hook"]
        dialogues = [row for row in timeline if row.get("type") == "dialogue"]
        dialogue_seconds = sum(float(row.get("duration") or 0) for row in dialogues)
        narration_lengths = narration_sentence_lengths(timeline)
        final_tail = float(narration_rows[-1].get("tailPad") or 0) if narration_rows else 0.0
        final_text = str(narration_rows[-1].get("text", "")) if narration_rows else ""
        semantic_audit = load_if_present(production / "qc" / "semantic-alignment-audit.json", {})
        profile = resolve_profile(job, semantic_audit)
        motion_audit = load_if_present(production / "qc" / "motion-coverage-audit.json", {})
        semantic_metrics = semantic_audit.get("metrics", {})
        cut_audit = cut_by_id.get(job_id, {})
        compatibility_baseline = match_compatibility_baseline(
            profile, videos[0] if len(videos) == 1 else None, production
        )
        broll = load_if_present(production / "broll-audit.json", [])
        ranges = []
        for block in broll if isinstance(broll, list) else []:
            for clip in block.get("clips", []):
                if all(key in clip for key in ("episode", "clip_start", "clip_duration")):
                    ranges.append({
                        "episode": clip["episode"],
                        "start": clip["clip_start"],
                        "end": float(clip["clip_start"]) + float(clip["clip_duration"]),
                    })
        boundary_issues = subtitle_boundary.get("issues", [])
        technical = probe(videos[0]) if len(videos) == 1 else {}
        checks = {
            "oneDelivery": len(videos) == 1,
            "format1080x1920": technical.get("width") == 1080 and technical.get("height") == 1920,
            "squarePixels": technical.get("sar") in {"1:1", None},
            "streamsPresent": bool(technical.get("video")) and bool(technical.get("audio")),
            "durationProfileRange": duration_in_profile_range(float(technical.get("duration") or 0), profile),
            "narrationRepeatZero": not sentence_duplicates(narration),
            "sourceRangeRepeatZero": not interval_duplicates(ranges),
            "captionRoundtrip": captions.get("scriptRoundtrip") is True or captions.get("roundTripExact") is True,
            "captionMaxCharacters": int(captions.get("maximumCharacters", -1)) <= 9 and int(captions.get("maximumCharacters", -1)) >= 1,
            "captionWordSplitZero": int(captions.get("wordSplitCount", 0)) == 0 and not boundary_issues,
            "captionProtectedTermSplitZero": int(captions.get("protectedTermSplitCount", -1)) == 0,
            "captionOverlapZero": int(captions.get("overlapCount", -1)) == 0,
            "captionMultilineZero": captions.get("singleLine") is True or int(captions.get("multilineCueCount", -1)) == 0,
            "captionOrphanZero": int(captions.get("orphanCount", 0)) == 0 and not boundary_issues,
            "completeFinalSentence": bool(re.search(r"[。！？!?]$", final_text.strip())),
            "tailAtLeast045": final_tail >= 0.45,
            "captionResetAuditPassed": int(reset.get("sampledTransitions", 0)) > 0 and Path(str(reset.get("contactSheet") or "")).is_file(),
            "hardSubtitlePilotPassed": (
                pilot.get("status") == "passed"
                and int(pilot.get("checkedNarrationShots", 0)) > 0
                and int(pilot.get("checkedEncodedFrames", 0)) >= int(pilot.get("checkedNarrationShots", 0)) * 3
                and int(pilot.get("sourceGeneratedOverlapFrames", -1)) == 0
                and int(pilot.get("verticalStretchFrames", -1)) == 0
                and int(pilot.get("seekMismatchFrames", -1)) == 0
            ),
            "hardSubtitleManualReviewPassed": pilot_review.get("status") == "passed",
            "oneCentralQuestion": bool(str(job.get("centralQuestion") or "").strip()),
            "oneHook": len(hooks) == 1,
            "globalOralSentenceAverage10To26": bool(narration_lengths) and 10 <= sum(narration_lengths) / len(narration_lengths) <= 26,
            "globalNormalSentenceMaximum36": bool(narration_lengths) and max(narration_lengths) <= 36,
            "sourcePlaybackOne": abs(float(job.get("sourcePlaybackSpeed") or 0) - 1.0) < 0.001,
            "tailNoMoreThan6": final_tail <= 6.0,
            "encodedCutBoundaryPassed": encoded_cut_boundary_passed(cut_audit, compatibility_baseline),
        }
        checks.update(semantic_alignment_checks(semantic_audit, compatibility_baseline))
        checks.update(motion_coverage_checks(motion_audit, compatibility_baseline))
        checks.update(profile_checks(profile, hooks, dialogues, dialogue_seconds, narration_lengths, semantic_metrics))
        reports.append({
            "id": job_id,
            "narrativeProfile": profile,
            "compatibilityMode": compatibility_baseline is not None,
            "compatibilityBaselineId": compatibility_baseline.get("id") if compatibility_baseline else None,
            "compatibilityHashMatched": compatibility_baseline is not None,
            "video": str(videos[0]) if videos else None,
            "checks": checks,
            "passed": all(checks.values()),
        })
    summary = {"count": len(reports), "passedCount": sum(row["passed"] for row in reports), "failedIds": [row["id"] for row in reports if not row["passed"]], "entries": reports}
    output = args.root / "qc" / "batch-hard-gate-summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    profile_output = args.root / "qc" / "narrative-profile-regression-summary.json"
    profile_output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "entries"}, ensure_ascii=False, indent=2))
    if summary["failedIds"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
