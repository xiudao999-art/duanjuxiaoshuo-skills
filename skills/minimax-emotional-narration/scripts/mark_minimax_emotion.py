#!/usr/bin/env python
"""Create a context-aware first-pass MiniMax narration emotion plan.

This script does not call MiniMax. It retains candidate analyses for review,
selects up to 15 salient phrases of up to 20 visible characters, and emits an
API-ready chunk plan without delivery-control fields.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


EMOTION_CUES: Dict[str, Sequence[str]] = {
    "happy": ("开心", "快乐", "高兴", "兴奋", "成功", "赢了", "赢得", "第一名", "冠军", "中奖", "中了", "终于", "太好了", "希望", "奖励", "幸福", "喜欢", "笑", "团聚", "做到了", "实现了", "获救", "安全了", "松了口气"),
    "sad": ("难过", "伤心", "遗憾", "失去", "错过", "孤单", "孤独", "眼泪", "失败", "对不起", "怀念", "离开", "再也", "失望", "告别", "不会回来", "来不及挽回"),
    "angry": ("生气", "愤怒", "凭什么", "不公平", "别再", "警告", "骗子", "欺骗", "离谱", "受够", "反击", "荒唐", "过分", "背叛", "搞砸", "不讲理", "欺负", "必须道歉"),
    "fearful": ("害怕", "担心", "紧张", "危险", "风险", "来不及", "倒计时", "万一", "威胁", "不安", "糟糕", "怎么办", "逃不掉", "再晚一步", "随时可能", "未知", "悬念"),
    "disgusted": ("恶心", "嫌弃", "讨厌", "反感", "肮脏", "油腻", "受不了", "垃圾", "廉价", "无耻", "卑鄙", "滚开", "别碰", "令人作呕", "可耻"),
    "surprised": ("没想到", "谁能想到", "竟然", "原来", "突然", "居然", "震惊", "反转", "发现", "一瞬间", "出乎意料", "意外", "怎么会"),
    "calm": ("慢慢", "安静", "平静", "治愈", "轻轻", "放心", "温柔", "陪你", "别急", "呼吸", "没关系", "慢慢来", "已经安全", "一切都会好", "接受", "释然"),
    "fluent": ("首先", "然后", "接着", "最后", "比如", "简单来说", "操作", "步骤", "功能", "教程", "说明", "方法", "需要", "可以这样", "分为"),
}

EVENT_PATTERNS: Sequence[Tuple[str, str, int, str]] = (
    (r"拿到.{0,4}(第一名|冠军)|考上|录取|获奖|做到了|实现.{0,4}目标", "happy", 4, "目标达成"),
    (r"获救|脱险|安全了|赶上了|松了口气", "happy", 4, "压力解除或安全恢复"),
    (r"再也.{0,5}(回不来|不会回来|见不到)|永远失去|离开了|去世", "sad", 5, "不可逆的失去或离别"),
    (r"没赶上|错过了|落选|失败了|被拒绝", "sad", 3, "目标受挫或结果落空"),
    (r"凭什么|不公平|被背叛|被欺骗|搞砸|推卸责任", "angry", 4, "不公平、阻碍或责任冲突"),
    (r"再晚.{0,4}来不及|随时可能|一旦.{0,8}就|万一|倒计时", "fearful", 4, "未来威胁且控制感较低"),
    (r"恶心|令人作呕|无耻|卑鄙|受不了", "disgusted", 4, "强烈排斥或道德反感"),
    (r"没想到|谁能想到|出乎意料|竟然|居然|原来", "surprised", 4, "预期被打破"),
    (r"放心|没关系|已经安全|慢慢来|一切都会好", "calm", 3, "安全感或控制感恢复"),
)

NEGATED_POSITIVE = re.compile(r"(?:一点也不|并不|并没有|从不|不再|不|没)[^，。！？!?；;]{0,4}(?:开心|高兴|快乐|喜欢|幸福|兴奋)")
NEGATED_FEAR = re.compile(r"(?:别|不要|不用|不必)[^，。！？!?；;]{0,3}(?:怕|担心|紧张)|没有危险|并不危险")
NEGATED_FAILURE = re.compile(r"(?:不是|并非|不算)[^，。！？!?；;]{0,3}(?:失败|失去|遗憾)")
NEGATED_ANGER = re.compile(r"(?:不是|并不|没有|不再)[^，。！？!?；;]{0,3}(?:生气|愤怒)")
IRONY_PRAISE = re.compile(r"可真会|真厉害|真聪明|好样的|真是个天才|干得漂亮")
NEGATIVE_CONTEXT = re.compile(r"搞砸|失败|来不及|丢了|坏了|错了|麻烦|灾难|不公平|受够|背叛|欺骗")
REVEAL_PREFIX = re.compile(r"^\s*(谁能想到|没想到|出乎意料|原来|竟然|居然|突然)(?:[，,:：]\s*)?")
ADVERSATIVE = re.compile(r"但是|可是|不过|然而|反而|却|但")
STANDUP_HINTS = re.compile(r"脱口秀|吐槽|段子|你们有没有发现|我发现|我跟你说|老板|领导|同事|我妈|教练")
STANDUP_PREMISE = re.compile(r"你们有没有发现|我发现|我最近|我买了|公司最神奇|我妈学会")
STANDUP_PUNCHLINE = re.compile(r"只是不想上班|我不穿袜子了|版本管理|拥有了领导力|我跟灯熟了|处处都是进步")
STANDUP_ABSURD = re.compile(r"蔬菜催债|吊灯打招呼|生菜管理我|电脑风扇.*加班|手机.*不想上班|冰箱.*领导力")
STANDUP_MOCK_RANT = re.compile(r"老板|领导|加班|第八版|甲方|工资|改一下")
STANDUP_SELF_DEPRECATION = re.compile(r"穿袜子.*喘|我不穿袜子|我连|我这种|我唯一|单身|减肥|健身")
SERIOUS_LOSS = re.compile(r"去世|永远失去|再也见不到|不会回来|告别|死亡")

SOUND_BY_EMOTION = {"happy": "(chuckle)", "sad": "(sighs)", "fearful": "(inhale)", "surprised": "(gasps)", "disgusted": "(groans)"}

APPRAISAL_BY_EMOTION: Dict[str, Dict[str, str]] = {
    "happy": {"valence": "positive", "arousal": "medium", "control": "high", "certainty": "high", "expectedness": "expected_or_relief", "responsibility": "self_or_situation"},
    "sad": {"valence": "negative", "arousal": "low", "control": "low", "certainty": "high", "expectedness": "expected_or_realized", "responsibility": "situation_or_self"},
    "angry": {"valence": "negative", "arousal": "high", "control": "medium", "certainty": "high", "expectedness": "unexpected_or_unfair", "responsibility": "other_or_self"},
    "fearful": {"valence": "negative", "arousal": "high", "control": "low", "certainty": "low", "expectedness": "uncertain", "responsibility": "situation_or_unknown"},
    "disgusted": {"valence": "negative", "arousal": "medium", "control": "medium", "certainty": "high", "expectedness": "irrelevant", "responsibility": "other_or_target"},
    "surprised": {"valence": "mixed", "arousal": "high", "control": "unknown", "certainty": "high", "expectedness": "unexpected", "responsibility": "unknown"},
    "calm": {"valence": "positive_or_neutral", "arousal": "low", "control": "high", "certainty": "high", "expectedness": "settled", "responsibility": "situation_or_self"},
    "fluent": {"valence": "neutral", "arousal": "low", "control": "high", "certainty": "high", "expectedness": "expected", "responsibility": "not_applicable"},
    "neutral": {"valence": "neutral", "arousal": "low", "control": "unknown", "certainty": "unknown", "expectedness": "unknown", "responsibility": "unknown"},
}


def visible_len(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def trim_span(text: str, start: int, end: int) -> Tuple[str, int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return text[start:end], start, end


def hard_split(text: str, start: int, end: int, max_chars: int) -> List[Tuple[str, int, int]]:
    result: List[Tuple[str, int, int]] = []
    chunk_start, count = start, 0
    for index in range(start, end):
        if not text[index].isspace():
            count += 1
        if count > max_chars:
            chunk, left, right = trim_span(text, chunk_start, index)
            if chunk:
                result.append((chunk, left, right))
            chunk_start = index
            count = 0 if text[index].isspace() else 1
    chunk, left, right = trim_span(text, chunk_start, end)
    if chunk:
        result.append((chunk, left, right))
    return result


def split_at_matches(text: str, start: int, end: int, pattern: re.Pattern[str]) -> List[Tuple[int, int]]:
    boundaries = [start]
    for match in pattern.finditer(text[start:end]):
        position = start + match.start()
        if position > start:
            boundaries.append(position)
    boundaries.append(end)
    return [(boundaries[i], boundaries[i + 1]) for i in range(len(boundaries) - 1)]


def split_candidates(text: str, max_chars: int) -> List[Dict[str, object]]:
    candidates: List[Dict[str, object]] = []
    sentence_pattern = re.compile(r"[^。！？!?；;\n]+[。！？!?；;]?|\n+")
    sentence_index = order = 0
    for sentence_match in sentence_pattern.finditer(text):
        raw = sentence_match.group(0)
        if not raw.strip():
            continue
        sentence_index += 1
        sentence_start = sentence_match.start()
        for clause_match in re.finditer(r"[^，,、：:\n]+[，,、：:]?|\n+", raw):
            clause_start = sentence_start + clause_match.start()
            clause_end = sentence_start + clause_match.end()
            for part_start, part_end in split_at_matches(text, clause_start, clause_end, ADVERSATIVE):
                part, left, right = trim_span(text, part_start, part_end)
                if not part:
                    continue
                reveal = REVEAL_PREFIX.match(part)
                spans = [(left, right)]
                remainder = part[reveal.end():].strip() if reveal else ""
                particle_only = bool(re.fullmatch(r"[吧呢啊呀嘛哦哇]+[，,。！？!?；;：:]*", remainder))
                if reveal and reveal.end() < len(part) and remainder and not particle_only:
                    marker_end = left + reveal.end()
                    spans = [(left, marker_end), (marker_end, right)]
                for reveal_start, reveal_end in spans:
                    for fragment, frag_start, frag_end in hard_split(text, reveal_start, reveal_end, max_chars):
                        candidates.append({"order": order, "source_sentence": sentence_index, "text": fragment, "source_start": frag_start, "source_end": frag_end})
                        order += 1
    return candidates


def cue_scores(fragment: str) -> Tuple[Dict[str, int], Dict[str, List[str]], List[str]]:
    scores = {emotion: 0 for emotion in EMOTION_CUES}
    evidence: Dict[str, List[str]] = {emotion: [] for emotion in EMOTION_CUES}
    event_reasons: List[str] = []
    for emotion, cues in EMOTION_CUES.items():
        for cue in cues:
            if cue in fragment:
                scores[emotion] += 2 if len(cue) >= 3 else 1
                evidence[emotion].append(cue)
    for pattern, emotion, weight, reason in EVENT_PATTERNS:
        match = re.search(pattern, fragment)
        if match:
            scores[emotion] += weight
            evidence[emotion].append(match.group(0))
            event_reasons.append(reason)
    return scores, evidence, event_reasons


def apply_language_rules(fragment: str, previous: str, sentence_text: str, scores: Dict[str, int]) -> List[str]:
    operators: List[str] = []
    if NEGATED_POSITIVE.search(fragment):
        scores["happy"] = 0
        scores["sad"] += 3
        operators.append("否定作用于正向情绪，不能按字面判为开心")
    if NEGATED_FEAR.search(fragment):
        scores["fearful"] = 0
        scores["calm"] += 3
        operators.append("安抚或危险否定改变了恐惧含义")
    if NEGATED_FAILURE.search(fragment):
        scores["sad"] = max(0, scores["sad"] - 4)
        operators.append("否定词排除了失败或失去")
    if NEGATED_ANGER.search(fragment):
        scores["angry"] = max(0, scores["angry"] - 4)
        operators.append("否定词排除了愤怒")
    if ADVERSATIVE.search(fragment):
        operators.append("该片段位于转折点，转折后的信息权重更高")
    if IRONY_PRAISE.search(fragment) and NEGATIVE_CONTEXT.search(previous + sentence_text):
        scores["happy"] = 0
        scores["angry"] += 5
        operators.append("表面赞美与负面事件冲突，按反讽处理")
    if "？" in fragment or "?" in fragment:
        if re.search(r"凭什么|怎么又|为什么总|还要我", fragment):
            scores["angry"] += 3
            operators.append("反问表达责备或不公平")
        elif re.search(r"万一|怎么办|会不会|来得及吗", fragment):
            scores["fearful"] += 3
            operators.append("疑问指向未来风险和不确定性")
        else:
            operators.append("疑问号本身不决定情绪")
    if re.search(r"[“\"]|他说|她说|有人说", fragment):
        operators.append("包含引用，需要区分被引用人物与旁白者")
    return operators


def resolve_genre(text: str, requested: str) -> str:
    if requested != "auto":
        return requested
    return "standup" if len(STANDUP_HINTS.findall(text)) >= 2 else "narration"


def apply_genre_rules(fragment: str, sentence_text: str, scores: Dict[str, int], genre: str) -> List[str]:
    if genre != "standup":
        return []
    operators: List[str] = []
    if STANDUP_PREMISE.search(fragment):
        scores["surprised"] = max(0, scores["surprised"] - 5)
        scores["fluent"] += 3
        operators.append("脱口秀观察句是 premise，不按字面发现判为惊讶")
    if (STANDUP_SELF_DEPRECATION.search(fragment) or "再也没有隐私" in fragment) and not SERIOUS_LOSS.search(sentence_text):
        scores["sad"] = 0
        scores["fluent"] += 2
        operators.append("自嘲或夸张抱怨采用可控喜剧语气，不判为真实悲伤")
    if STANDUP_MOCK_RANT.search(fragment):
        scores["angry"] += 2
        operators.append("职场抱怨按 mock-rant 处理，保留轻度愤怒而非失控发火")
    if STANDUP_ABSURD.search(fragment):
        scores["surprised"] += 3
        operators.append("物体获得荒诞人格或权力，构成喜剧反转")
    if STANDUP_PUNCHLINE.search(fragment):
        scores["happy"] += 8
        operators.append("该句完成主要包袱，使用轻松 payoff 而非真实负面情绪")
    if re.search(r"不是.{0,12}(?:而是|是)|现在是|第一次感受到", fragment):
        scores["surprised"] += 2
        operators.append("句式重解释前提，构成 turn")
    return operators


def comedy_role_for(fragment: str, order: int, total: int) -> str:
    if STANDUP_PREMISE.search(fragment):
        return "premise"
    if STANDUP_PUNCHLINE.search(fragment):
        return "callback_punchline" if re.search(r"熟了|版本管理|处处都是进步", fragment) else "punchline"
    if STANDUP_SELF_DEPRECATION.search(fragment):
        return "self_deprecation"
    if STANDUP_MOCK_RANT.search(fragment):
        return "mock_rant"
    if re.search(r"[‘’“”]|问：|说：|发通知", fragment):
        return "act_out"
    if STANDUP_ABSURD.search(fragment) or re.search(r"原来|结果|没想到|第一次|现在是|只是", fragment):
        return "turn"
    if order + 1 == total:
        return "tag"
    if order <= max(0, int(total * 0.15)):
        return "setup"
    return "escalation"


def experiencer_for(fragment: str) -> str:
    if re.search(r"(?:他说|她说|他们说|有人说).{0,8}(?:害怕|开心|生气|难过|平静)", fragment):
        return "被引用人物"
    if re.search(r"(?:我|我们|我的|我们的)", fragment):
        return "旁白者"
    if re.search(r"(?:你|大家|观众|听众)", fragment):
        return "听众或被指向者"
    return "由上下文确定"


def target_for(fragment: str, emotion: str) -> str:
    if emotion == "surprised":
        return "揭晓结果"
    if emotion in {"angry", "disgusted"} and re.search(r"你|他|她|他们|这种|这件", fragment):
        return "被责备或排斥的对象"
    if emotion in {"happy", "sad"}:
        return "事件结果或个人目标"
    if emotion == "fearful":
        return "潜在风险或未知结果"
    if emotion == "calm":
        return "当前处境或听众状态"
    return "叙述内容"


def choose_emotion(scores: Dict[str, int]) -> Tuple[str, int]:
    priority = ("surprised", "angry", "fearful", "disgusted", "sad", "happy", "calm", "fluent")
    emotion = max(priority, key=lambda name: (scores[name], -priority.index(name)))
    return (emotion, scores[emotion]) if scores[emotion] > 0 else ("neutral", 0)


def estimate_intensity(fragment: str, emotion: str, raw_score: int) -> int:
    if emotion == "neutral":
        return 1
    intensity = 1 + min(2, raw_score // 2)
    if re.search(r"太|非常|特别|真的|彻底|再也|绝对|极其|竟然|居然", fragment):
        intensity += 1
    if re.search(r"！{1,}|!{1,}", fragment) and raw_score >= 2:
        intensity += 1
    if emotion in {"calm", "fluent"}:
        intensity = min(intensity, 3)
    return min(5, max(1, intensity))


def confidence_for(emotion: str, raw_score: int, operators: Sequence[str], event_reasons: Sequence[str]) -> int:
    if emotion == "neutral":
        return 1
    confidence = 1
    if raw_score >= 3 or event_reasons:
        confidence = 2
    if raw_score >= 5 and event_reasons:
        confidence = 3
    if any("反讽" in operator for operator in operators):
        confidence = min(confidence, 2)
    return confidence


def narrative_role(fragment: str, emotion: str, intensity: int, order: int, total: int) -> str:
    position = order / max(1, total - 1)
    if emotion == "surprised" or REVEAL_PREFIX.match(fragment):
        return "reveal"
    if position <= 0.15 and emotion in {"surprised", "fearful", "angry"}:
        return "hook"
    if intensity >= 4 and 0.35 <= position <= 0.85:
        return "climax"
    if emotion in {"fearful", "angry", "sad", "disgusted"}:
        return "tension"
    if position >= 0.6 and emotion in {"happy", "calm"}:
        return "resolution"
    if position >= 0.75 and re.search(r"现在|马上|一起|试试|下载|打开|点击|别错过", fragment):
        return "cta"
    if emotion == "fluent":
        return "bridge"
    return "setup"


def appraisal_for(emotion: str, fragment: str) -> Dict[str, str]:
    appraisal = dict(APPRAISAL_BY_EMOTION[emotion])
    if emotion == "happy" and re.search(r"获救|安全|赶上|终于", fragment):
        appraisal["expectedness"] = "relief_after_uncertainty"
    if emotion == "angry" and re.search(r"凭什么|不公平|背叛|欺骗", fragment):
        appraisal["responsibility"] = "other"
    return appraisal


def build_why(emotion: str, evidence: Sequence[str], event_reasons: Sequence[str], operators: Sequence[str]) -> str:
    if emotion == "neutral":
        return "该片段主要承担信息连接，没有足够的事件评价或情绪转折，因此保持中性。"
    label_reason = {
        "happy": "事件呈现正向结果、目标达成或压力解除",
        "sad": "事件涉及失去、落空、遗憾或较低控制感",
        "angry": "事件包含不公平、责备、阻碍或责任冲突",
        "fearful": "事件指向未来威胁、不确定性或较低控制感",
        "disgusted": "说话者对目标表现出强烈排斥、鄙视或道德反感",
        "surprised": "信息打破原有预期，本片段承担发现或揭晓瞬间",
        "calm": "语义正在恢复安全感、秩序或控制感",
        "fluent": "该片段的主要功能是清楚说明步骤或事实",
    }[emotion]
    details: List[str] = []
    if event_reasons:
        details.append("；".join(dict.fromkeys(event_reasons)))
    if evidence:
        details.append("证据为“" + "、".join(dict.fromkeys(evidence)) + "”")
    if operators:
        details.append(operators[0])
    suffix = "，" + "；".join(details) if details else ""
    return f"{label_reason}{suffix}，因此使用 {emotion}。"


def context_reason_for(emotion: str, previous: str, following: str, operators: Sequence[str]) -> str:
    reasons: List[str] = []
    if previous:
        reasons.append("已结合前一片段")
    if following:
        reasons.append("已结合后一片段")
    reasons.extend(operators[:2])
    if emotion == "surprised" and following:
        reasons.append("本片段只表达揭晓，后续结果另行判断")
    return "；".join(reasons) if reasons else "该片段可由自身事件语义判断。"


def role_weight(role: str) -> int:
    if role in {"hook", "reveal", "climax"}:
        return 3
    if role in {"tension", "resolution", "cta"}:
        return 2
    return 0


def analyze_candidates(candidates: List[Dict[str, object]], genre: str = "narration") -> List[Dict[str, object]]:
    sentence_texts: Dict[int, str] = {}
    for item in candidates:
        sentence_texts.setdefault(int(item["source_sentence"]), "")
        sentence_texts[int(item["source_sentence"])] += str(item["text"])
    total = len(candidates)
    previous_emotional = "neutral"
    recent_roles: List[Tuple[str, str]] = []
    for index, item in enumerate(candidates):
        fragment = str(item["text"])
        previous = str(candidates[index - 1]["text"]) if index else ""
        following = str(candidates[index + 1]["text"]) if index + 1 < total else ""
        scores, evidence_map, event_reasons = cue_scores(fragment)
        operators = apply_language_rules(fragment, previous, sentence_texts[int(item["source_sentence"])], scores)
        operators.extend(apply_genre_rules(fragment, sentence_texts[int(item["source_sentence"])], scores, genre))
        emotion, raw_score = choose_emotion(scores)
        intensity = estimate_intensity(fragment, emotion, raw_score)
        confidence = confidence_for(emotion, raw_score, operators, event_reasons)
        role = narrative_role(fragment, emotion, intensity, index, total)
        comedy_role = comedy_role_for(fragment, index, total) if genre == "standup" else None
        transition_bonus = 2 if emotion != "neutral" and previous_emotional not in {"neutral", emotion} else 0
        redundancy_penalty = 3 if (emotion, role) in recent_roles[-2:] else 0
        evidence = evidence_map.get(emotion, [])
        item.update({
            "emotion": emotion,
            "intensity": intensity,
            "confidence": confidence,
            "experiencer": experiencer_for(fragment),
            "trigger": event_reasons[0] if event_reasons else (evidence[0] if evidence else "无明确情绪触发事件"),
            "target": target_for(fragment, emotion),
            "appraisal": appraisal_for(emotion, fragment),
            "language_operators": operators,
            "narrative_role": role,
            "comedy_role": comedy_role,
            "context_reason": context_reason_for(emotion, previous, following, operators),
            "why": build_why(emotion, evidence, event_reasons, operators),
            "salience": 2 * intensity + 2 * confidence + role_weight(role) + transition_bonus - redundancy_penalty,
        })
        if emotion != "neutral":
            previous_emotional = emotion
            recent_roles.append((emotion, role))
    return candidates


def pause_for(fragment: str, emotion: str, intensity: int, next_emotion: str | None) -> float:
    if fragment.endswith(("，", ",", "、", "：", ":")):
        return 0.2
    if fragment.endswith(("。", "！", "？", "!", "?", "；", ";")):
        return 0.55 if emotion == "surprised" or intensity >= 4 else 0.4
    return 0.0


def build_synthesis_chunks(text: str, candidates: Sequence[Dict[str, object]], selected: Sequence[Dict[str, object]], genre: str = "narration") -> List[Dict[str, object]]:
    selected_by_order = {int(item["order"]): item for item in selected}
    sentence_groups: Dict[int, List[Dict[str, object]]] = {}
    for candidate in candidates:
        sentence_groups.setdefault(int(candidate["source_sentence"]), []).append(candidate)

    sentence_chunks: List[Dict[str, object]] = []
    for sentence_index in sorted(sentence_groups):
        group = sentence_groups[sentence_index]
        start = min(int(item["source_start"]) for item in group)
        end = max(int(item["source_end"]) for item in group)
        sentence_text = text[start:end].strip()
        evidence = [selected_by_order[int(item["order"])] for item in group if int(item["order"]) in selected_by_order]
        dominant = max(
            evidence,
            key=lambda item: (int(item["salience"]), int(item["confidence"]), int(item["intensity"])),
            default=None,
        )
        sentence_comedy_role = comedy_role_for(
            sentence_text,
            sentence_index - 1,
            len(sentence_groups),
        ) if genre == "standup" else None
        sentence_emotion = str(dominant["emotion"]) if dominant else None
        if genre == "standup":
            if sentence_comedy_role == "premise":
                sentence_emotion = "fluent"
            elif sentence_comedy_role == "mock_rant":
                sentence_emotion = "angry"
            elif sentence_comedy_role in {"punchline", "callback_punchline"}:
                sentence_emotion = "happy"
            elif sentence_comedy_role == "self_deprecation" and sentence_emotion == "sad":
                sentence_emotion = "fluent"
        sentence_chunks.append({
            "text": sentence_text,
            "emotion": sentence_emotion,
            "dominant_role": str(dominant["narrative_role"]) if dominant else "plain",
            "comedy_role": sentence_comedy_role,
            "source_sentence_start": sentence_index,
            "source_sentence_end": sentence_index,
            "source_start": start,
            "source_end": end,
            "evidence_orders": [int(item["order"]) for item in evidence],
        })

    merged: List[Dict[str, object]] = []
    for item in sentence_chunks:
        previous = merged[-1] if merged else None
        same_delivery = previous is not None and previous["emotion"] == item["emotion"]
        combined_text = f"{previous['text']}{item['text']}" if previous else str(item["text"])
        if previous and same_delivery and genre != "standup" and visible_len(combined_text) <= 120:
            previous["text"] = combined_text
            previous["source_sentence_end"] = item["source_sentence_end"]
            previous["source_end"] = item["source_end"]
            previous["evidence_orders"].extend(item["evidence_orders"])
            if item["dominant_role"] in {"reveal", "climax"}:
                previous["dominant_role"] = item["dominant_role"]
        else:
            merged.append(item)

    result: List[Dict[str, object]] = []
    for index, item in enumerate(merged):
        is_last = index + 1 == len(merged)
        if is_last:
            pause = 0.0
        elif genre == "standup":
            next_role = merged[index + 1]["comedy_role"]
            if next_role in {"turn", "punchline", "callback_punchline"}:
                pause = 0.55
            elif item["comedy_role"] in {"punchline", "tag", "callback_punchline"}:
                pause = 0.3
            else:
                pause = 0.32
        else:
            pause = 0.55 if item["dominant_role"] in {"reveal", "climax"} else 0.4
        result.append({
            "id": f"speech-{index + 1:03d}",
            "text": item["text"],
            "emotion": item["emotion"],
            "pause_after": pause,
            "trim_edge_silence": True,
            "dominant_role": item["dominant_role"],
            "comedy_role": item["comedy_role"],
            "source_sentence_start": item["source_sentence_start"],
            "source_sentence_end": item["source_sentence_end"],
            "source_start": item["source_start"],
            "source_end": item["source_end"],
            "evidence_orders": item["evidence_orders"],
        })
    return result


def sound_prefix(fragment: str, emotion: str, intensity: int) -> str:
    if intensity < 4:
        return ""
    supported_context = {
        "happy": r"笑|哈哈|太开心",
        "sad": r"叹|唉|无奈|眼泪",
        "fearful": r"倒计时|来不及|屏住呼吸|危险",
        "surprised": r"没想到|谁能想到|震惊|竟然|居然|突然",
        "disgusted": r"恶心|受不了|令人作呕",
    }
    pattern = supported_context.get(emotion)
    return SOUND_BY_EMOTION.get(emotion, "") if pattern and re.search(pattern, fragment) else ""


def annotate_text(text: str, selected: Sequence[Dict[str, object]]) -> str:
    annotated = text
    for item in sorted(selected, key=lambda value: int(value["source_start"]), reverse=True):
        start = int(item["source_start"])
        annotated = annotated[:start] + f"[{item['emotion']}:{item['intensity']}]" + annotated[start:]
    return annotated


def global_analysis(text: str, candidates: Sequence[Dict[str, object]], genre: str = "narration") -> Dict[str, object]:
    if re.search(r"首先|步骤|教程|操作|方法", text):
        narration_type = "tutorial_or_explainer"
    elif re.search(r"下载|点击|马上|别错过|奖励|优惠", text):
        narration_type = "advertisement"
    elif re.search(r"后来|那天|从前|故事|直到|没想到", text):
        narration_type = "story"
    else:
        narration_type = "general_narration"
    emotional = [str(item["emotion"]) for item in candidates if item["emotion"] not in {"neutral", "fluent"}]
    return {
        "genre_profile": genre,
        "narration_type": narration_type,
        "narrator_stance": "第一人称体验者" if re.search(r"我|我们", text) else "第三人称讲述者或信息引导者",
        "audience_goal": "跟随事件产生情绪变化" if emotional else "清楚理解信息",
        "default_tone": "fluent" if narration_type == "tutorial_or_explainer" else "neutral",
        "emotion_arc": list(dict.fromkeys(emotional)),
    }


def make_plan(text: str, voice_id: str, model: str, max_segments: int, max_chars: int, genre: str = "auto") -> Dict[str, object]:
    if max_segments < 1 or max_chars < 1:
        raise ValueError("max_segments and max_chars must be at least 1")
    resolved_genre = resolve_genre(text, genre)
    candidates = analyze_candidates(split_candidates(text, max_chars=max_chars), genre=resolved_genre)
    selectable = [item for item in candidates if item["emotion"] != "neutral"]
    selected = sorted(
        sorted(selectable, key=lambda item: (int(item["salience"]), int(item["confidence"]), int(item["intensity"])), reverse=True)[:max_segments],
        key=lambda item: int(item["order"]),
    )
    chunks: List[Dict[str, object]] = []
    for index, item in enumerate(selected):
        emotion, intensity, fragment = str(item["emotion"]), int(item["intensity"]), str(item["text"])
        next_emotion = str(selected[index + 1]["emotion"]) if index + 1 < len(selected) else None
        pause = pause_for(fragment, emotion, intensity, next_emotion)
        prefix = sound_prefix(fragment, emotion, intensity)
        pause_tag = f"<#{pause:.1f}#>" if pause > 0 else ""
        chunks.append({
            "id": f"beat-{index + 1:03d}", "emotion": emotion, "intensity": intensity,
            "confidence": int(item["confidence"]), "text": fragment, "experiencer": item["experiencer"],
            "trigger": item["trigger"], "target": item["target"], "appraisal": item["appraisal"],
            "language_operators": item["language_operators"], "narrative_role": item["narrative_role"],
            "comedy_role": item.get("comedy_role"),
            "context_reason": item["context_reason"], "why": item["why"],
            "minimax_text": f"{prefix}{fragment}{pause_tag}", "pause_after": pause,
            "source_sentence": int(item["source_sentence"]), "source_order": int(item["order"]),
            "source_start": int(item["source_start"]), "source_end": int(item["source_end"]),
            "salience": int(item["salience"]),
        })
    synthesis_chunks = build_synthesis_chunks(text, candidates, selected, genre=resolved_genre)
    evidence_id_by_order = {int(chunk["source_order"]): str(chunk["id"]) for chunk in chunks}
    for speech_chunk in synthesis_chunks:
        speech_chunk["evidence_chunk_ids"] = [
            evidence_id_by_order[order]
            for order in speech_chunk.pop("evidence_orders")
            if order in evidence_id_by_order
        ]
    return {
        "original_text": text,
        "annotated_text": annotate_text(text, selected),
        "analysis": global_analysis(text, candidates, genre=resolved_genre),
        "candidates": candidates,
        "chunks": chunks,
        "synthesis_chunks": synthesis_chunks,
        "generation": {
            "model": model, "voice_id": voice_id,
            "genre_profile": resolved_genre,
            "strategy": "synthesize_semantic_chunks_trim_edges_then_concatenate",
            "max_segments": max_segments, "max_chars_per_segment": max_chars,
            "selected_segments": len(chunks),
            "synthesis_segments": len(synthesis_chunks),
            "notes": "Use synthesis_chunks for TTS. Trim generated edge silence, add one controlled pause, and keep 20-character chunks as evidence only.",
        },
    }


def read_text(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    if args.input:
        return Path(args.input).read_text(encoding="utf-8")
    return sys.stdin.read()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a context-aware MiniMax emotional narration plan.")
    parser.add_argument("--input", help="UTF-8 narration text file.")
    parser.add_argument("--text", help="Narration passed directly.")
    parser.add_argument("--output", help="Write the JSON plan to this file. Defaults to stdout.")
    parser.add_argument("--voice-id", default="REPLACE_WITH_VOICE_ID", help="MiniMax voice_id metadata.")
    parser.add_argument("--model", default="speech-2.8-hd", help="MiniMax model metadata.")
    parser.add_argument("--max-segments", type=int, default=15, help="Maximum selected emotional fragments.")
    parser.add_argument("--max-chars", type=int, default=20, help="Maximum visible characters per selected fragment.")
    parser.add_argument("--genre", choices=["auto", "narration", "standup"], default="auto", help="Genre profile for emotion and timing decisions.")
    args = parser.parse_args()
    plan = make_plan(read_text(args), args.voice_id, args.model, args.max_segments, args.max_chars, genre=args.genre)
    data = json.dumps(plan, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(data + "\n", encoding="utf-8")
    else:
        print(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
