---
name: minimax-emotional-narration
description: Analyze Chinese or mixed-language narration in full context, identify sentence- and phrase-level emotional causes, select the strongest emotional beats, and produce MiniMax TTS emotion plans. Use when Codex must judge which lines should sound happy, sad, angry, fearful, disgusted, surprised, calm, or fluent; mark a voiceover with emotional rises and falls; or prepare expressive MiniMax speech without speed, pitch, or volume controls.
---

# MiniMax Emotional Narration

Turn a narration into a context-aware MiniMax emotion plan. Reason from events and speaker intent before lexical clues. Mark no more than 15 fragments, keep each fragment within 20 visible characters, and assign one dominant MiniMax emotion to each fragment.

## Load resources

- Read `references/minimax-emotion-research.md` before resolving implicit emotion, negation, contrast, irony, quotation, mixed emotion, or MiniMax API behavior.
- Run `scripts/mark_minimax_emotion.py` for a deterministic first pass. Treat its result as reviewable evidence, not a substitute for semantic judgment.

## Analyze in two passes

### Pass 1: understand the whole narration

1. Identify narration type: story, advertisement, explainer, tutorial, commentary, or reflection.
2. Identify narrator stance, emotional experiencer, intended audience response, and default delivery tone.
3. Outline the likely arc: setup, conflict, escalation, reveal, climax, resolution, and CTA where present.
4. Use the previous and next sentence when judging every candidate. Do not classify an isolated sentence when context is available.

### Pass 2: judge each candidate fragment

For each sentence or clause, determine:

1. `experiencer`: who feels or should express the emotion.
2. `trigger`: the event or outcome causing it.
3. `target`: who or what the emotion concerns.
4. `appraisal`: valence, arousal, control, certainty, expectedness, and responsibility.
5. `language_operator`: negation, degree, modality, contrast, rhetorical question, quotation, or irony.
6. `narrative_role`: hook, setup, tension, reveal, climax, resolution, CTA, or bridge.
7. `emotion`: exactly one dominant label.
8. `intensity`: integer 1-5.
9. `confidence`: integer 1-3.
10. `why`: a concrete Chinese explanation citing the event, appraisal, context, or language operator. Never justify a label only with “contains a keyword.”

## Map appraisals to MiniMax emotions

- `happy`: positive result, reward, hope, praise, goal achievement, or relief after pressure.
- `sad`: irreversible loss, regret, separation, failure, loneliness, or low-control reflection.
- `angry`: unfairness, blame, obstruction, betrayal, accusation, resistance, or urgent command.
- `fearful`: future threat, danger, uncertainty, countdown, high stakes, or low control.
- `disgusted`: contamination, contempt, moral revulsion, strong rejection, or distancing.
- `surprised`: expectation violation, sudden discovery, reversal, or reveal. Use it for the discovery instant, not automatically for the emotional outcome.
- `calm`: restored safety, reassurance, acceptance, healing, or low-arousal closure.
- `fluent`: informational or procedural delivery whose main need is clarity rather than emotion.
- `neutral`: internal analysis label only. Leave ordinary bridges unselected and omit the MiniMax emotion parameter for neutral text.

Split mixed turns. For `没想到，我真的中奖了`, mark `没想到` as `surprised` and `我真的中奖了` as `happy`.

## Apply Chinese correction rules

- Resolve the scope of `不`, `没`, `并不`, `一点也不`, `不再`, and similar negation before scoring emotion.
- Give the post-contrast clause more semantic weight after `但是`, `可是`, `却`, `反而`, `不过`, and `然而`.
- Treat `没想到`, `原来`, `竟然`, and `居然` as reveal cues only; inspect the following event for its outcome emotion.
- Distinguish quoted emotion from narrator emotion. `他说他很害怕，但我很平静` contains different experiencers and should be split.
- Detect rhetorical questions from blame, unfairness, or threat, not from the question mark alone.
- Detect irony when literal praise conflicts with a negative event or context. Do not label `你可真厉害，又搞砸了` as `happy`.
- Prefer event meaning over affect words. `终于拿到第一名` is `happy` even without “开心.”

## Apply the stand-up genre profile

When the user requests 脱口秀, comedy monologue, 吐槽, 自嘲, 段子, or stand-up, set `genre=standup` and classify comedy function before emotion.

1. Label each sentence as `premise`, `setup`, `escalation`, `self_deprecation`, `act_out`, `mock_rant`, `turn`, `punchline`, `tag`, or `callback_punchline`.
2. Keep premises conversational or `fluent`. `你们有没有发现` and `我发现` introduce an observation; they are not automatically `surprised`.
3. Treat self-deprecation as controlled, playful delivery. Do not use `sad` unless the text describes a real loss rather than a joke persona.
4. Treat exaggerated workplace or family complaints as `mock_rant`. Use `angry` only when a deliberate mock-angry performance improves the joke; otherwise prefer plain or `fluent`.
5. Treat absurd reinterpretation and misdirection as a turn. Use `surprised` for the reveal and `happy` for a clearly playful payoff.
6. Keep punchlines dry enough to land. Do not make every punchline `happy`, and do not add `(laughs)` merely because the audience is expected to laugh.
7. Preserve act-outs and quoted speech as complete synthesis chunks when a character voice or attitude changes.
8. Prefer about 2-4 emotion switches per 100 Chinese characters for stand-up.

Recommended modern Mandarin stand-up voice: `Chinese (Mandarin)_Unrestrained_Young_Man`. Prefer a relaxed conversational system voice over announcer or advertising voices.

## Select emotional peaks

1. Extract the smallest meaningful original phrase; never rewrite it merely to meet the limit.
2. Keep every selected phrase at 20 visible non-space characters or fewer.
3. Rank candidates by intensity, confidence, narrative role, emotional transition, and non-redundancy.
4. Select at most 15 fragments for the entire article, then restore source order.
5. Prefer hooks, conflicts, reversals, climaxes, resolutions, and meaningful CTAs over routine exposition.
6. Avoid rapid label switching when adjacent clauses carry the same emotional state.

The 20-character rule applies only to the evidence span in `chunks`. Never use that short evidence span automatically as a standalone TTS request.

## Build semantic synthesis chunks

1. Build `synthesis_chunks` separately from annotation `chunks`.
2. Prefer one complete sentence per synthesis chunk and choose the strongest selected emotion inside that sentence as its dominant emotion.
3. Merge adjacent neutral sentences, or adjacent sentences with the same dominant emotion, when the combined text remains coherent.
4. Never split before a modal particle or required complement such as `吧`, `呢`, `啊`, `的是`, `因为`, `所以`, `但`, or `却`.
5. Keep the practical rate near 3-6 emotion switches per 100 Chinese characters. The 15-fragment cap remains an annotation limit, not a target number of voice switches.
6. Keep unselected sentences plain by omitting the MiniMax emotion parameter.

For stand-up, keep one complete sentence per synthesis chunk so setup and punchline timing remain explicit. Do not merge separate comedy roles merely because their emotion is identical.

## Build MiniMax text

- Keep emotion metadata outside spoken text. Do not send `[happy]`, `[sad]`, or similar labels as TTS text.
- Put only original narration, supported pauses such as `<#0.2#>`, `<#0.5#>`, `<#0.8#>`, and sparse supported interjections in `minimax_text`.
- Use interjections only when semantically justified: `(laughs)`, `(chuckle)`, `(sighs)`, `(breath)`, `(inhale)`, `(exhale)`, `(gasps)`, `(groans)`, `(sniffs)`, `(emm)`.
- Create one MiniMax request per `synthesis_chunks` item, not per short annotation span.
- Measure and trim each generated request's leading and trailing silence before concatenation. Then add one controlled pause only once.
- Use about `0.15-0.30` seconds after commas, `0.35-0.65` seconds after ordinary sentences, and `0.70-1.00` seconds only for deliberate reveals or emotional turns.
- For stand-up, use about `0.50-0.60` seconds immediately before a punchline or turn, `0.25-0.35` seconds after a punchline/tag, and about `0.28-0.40` seconds between ordinary setup sentences.
- Do not automatically add `0.5` seconds after every selected emotion span.
- Do not output or recommend speed, pitch, or volume fields.

## Run the helper

```bash
python .codex/skills/minimax-emotional-narration/scripts/mark_minimax_emotion.py --input narration.txt --voice-id your_voice_id --model speech-2.8-hd --output emotion_plan.json
```

Defaults enforce `--max-segments 15` and `--max-chars 20`.

## Output contract

Return the original text, full-text annotation, global analysis, all reviewable candidates, selected evidence chunks, semantic synthesis chunks, and generation metadata. Each selected evidence chunk must include:

```json
{
  "id": "beat-001",
  "emotion": "surprised",
  "intensity": 4,
  "confidence": 3,
  "text": "没想到",
  "experiencer": "旁白者",
  "trigger": "预期被打破",
  "target": "揭晓结果",
  "appraisal": {
    "valence": "mixed",
    "arousal": "high",
    "control": "unknown",
    "certainty": "high",
    "expectedness": "unexpected",
    "responsibility": "unknown"
  },
  "narrative_role": "reveal",
  "context_reason": "后句给出正向结果，本片段只承担揭晓。",
  "why": "“没想到”明确表示预期被打破，因此使用 surprised 表达揭晓瞬间。",
  "minimax_text": "(gasps)没想到<#0.5#>",
  "pause_after": 0.5,
  "source_sentence": 1,
  "source_order": 0
}
```

Each `synthesis_chunks` item must contain complete speakable text and one dominant emotion:

```json
{
  "id": "speech-001",
  "text": "没想到吧，真正危险的是越过事件视界。",
  "emotion": "surprised",
  "pause_after": 0.55,
  "trim_edge_silence": true,
  "evidence_chunk_ids": ["beat-001", "beat-002"]
}
```

For synthesis, iterate `synthesis_chunks` and place its label in `voice_setting.emotion`. For neutral text, omit `emotion`. This skill prepares the plan and does not call MiniMax unless the user separately asks for audio generation and provides usable credentials and a voice.
## Stand-up pause audit

When `genre` is `standup`, distinguish an intentional comic wait from a punctuation-created gap before synthesis:

- Preserve a longer pause when the wording explicitly performs waiting or silence, such as `沉默了三秒`, and the wait supports the next joke.
- Treat an internal colon in `speaker cue: quoted line` as a synthesis boundary. Put the cue and the quoted line in separate `synthesis_chunks`, preserve their original order and characters, and use only `0.12-0.22s` between them.
- Do not send a cue and its act-out line as one MiniMax request when a colon may create an uncontrolled pause. Edge-trim both returned clips before concatenation.
- Keep the normal pre-punchline pause near `0.55s`, but do not stack it on top of a long pause already produced inside a chunk.
- Flag any detected silence of `>=0.8s` for review. Accept it only when `context_reason` explains the deliberate comic wait; otherwise split the chunk or shorten the punctuation gap.
- Splitting for pause control must not rewrite, paraphrase, or omit the source narration. It changes request boundaries only.
## Voice selection before emotion planning

Choose the MiniMax base voice before marking emotion or building synthesis chunks. A suitable base voice should already express most of the desired persona without relying on repeated `emotion` changes.

### Fixed decision order

1. Identify the genre: narration, science explainer, commercial, story, stand-up, character performance, or emotional essay.
2. Identify the speaker persona: approximate age, gender presentation when relevant, authority level, intimacy, energy, regional flavor, and whether the speaker is performing a character.
3. Identify the audience relationship: announcer-to-public, teacher-to-learner, host-to-listener, friend-to-friend, or performer-to-audience.
4. Decide whether timbre continuity or dramatic range matters more. Narration and stand-up normally prioritize continuity.
5. Select one primary voice and at most two audition alternatives. Do not switch voices inside one article unless the script contains multiple actual characters.
6. Explain why each candidate fits and why obvious alternatives were rejected.

### Default voice families

- Stable authority: `Chinese (Mandarin)_Reliable_Executive`, `Chinese (Mandarin)_Gentleman`, `Chinese (Mandarin)_Male_Announcer`, `Chinese (Mandarin)_News_Anchor`.
- Conversational and podcast-like: `Chinese (Mandarin)_Sincere_Adult`, `Chinese (Mandarin)_Radio_Host`, `Chinese (Mandarin)_Warm_Bestie`, `Chinese (Mandarin)_Laid_BackGirl`.
- Young and direct: `Chinese (Mandarin)_Straightforward_Boy`, `Chinese (Mandarin)_Gentle_Youth`, `Chinese (Mandarin)_Crisp_Girl`.
- Strong comic persona: `Chinese (Mandarin)_Stubborn_Friend`, `Chinese (Mandarin)_Humorous_Elder`, `Chinese (Mandarin)_Unrestrained_Young_Man`, `Arrogant_Miss`.
- Warm story and family content: `Chinese (Mandarin)_Mature_Woman`, `Chinese (Mandarin)_Wise_Women`, `Chinese (Mandarin)_Kind-hearted_Elder`, `Chinese (Mandarin)_Warm-HeartedAunt`.
- Stylized character only: `Robot_Armor`, `Chinese (Mandarin)_Cute_Spirit`, `Chinese (Mandarin)_Lyrical_Voice`.

The families above are production heuristics inferred from MiniMax's official voice names, not an official quality ranking. If the current inventory matters, query the official Get Voice API instead of assuming the list is permanent. See `references/minimax-voice-selection.md`.

### Stand-up defaults

For Chinese stand-up, audition in this order unless the requested persona says otherwise:

1. `Chinese (Mandarin)_Sincere_Adult`: neutral, conversational default for observation and self-deprecation.
2. `Chinese (Mandarin)_Radio_Host`: clearer host rhythm for workplace or science-comedy material.
3. `Chinese (Mandarin)_Stubborn_Friend`: complaint and mock-rant persona without requiring repeated `angry` changes.
4. `Chinese (Mandarin)_Straightforward_Boy`: younger, faster, direct delivery.

Use `Chinese (Mandarin)_Unrestrained_Young_Man` only when strong performance energy is intentional. It must use one continuous request or very few requests and restrained emotion changes, because repeated independent generations can sound like different people.

Do not default to announcer, news, robot, cute-character, lyrical, or strongly aged voices for general stand-up. Use them only when the script explicitly needs that persona.

### Audition protocol

When voice choice is uncertain, synthesize the same representative `60-120` Chinese characters with `3-4` candidate voices:

- Use the same model, text, punctuation, pause markers, sample rate, and output format.
- Use one request per candidate and no explicit emotion on the first pass.
- Do not use `speed`, `pitch`, or `vol` to make an unsuitable voice appear suitable.
- Apply the same post-synthesis loudness normalization, normally `-14 LUFS` and `-1 dBTP` for short-form narration.
- Compare identity continuity, conversational naturalness, sentence-final cadence, consonant clarity, fatigue over a full paragraph, and whether the voice can carry setup and punchline without becoming a new character.
- Select the base voice first. Only then test minimal emotion or sound-tag variants.

### Continuity rules

- Emotional analysis labels and TTS request boundaries are separate decisions.
- Prefer one request for one coherent paragraph. MiniMax T2A calls are stateless, so excessive splitting increases timbre drift.
- For stand-up, keep one base state for at least `80-90%` of the text. Use explicit emotion only for a genuine act-out or reveal that cannot be conveyed by wording and pause.
- Never map every detected emotional beat to a separate TTS request.
- Use `<#x#>` pause markers and punctuation before adding more emotion changes.
- Loudness is a mastering concern. Normalize after synthesis rather than changing MiniMax `vol`.

### Required plan output

Add a `voice_selection` object to the analysis result:

```json
{
  "voice_selection": {
    "genre": "standup",
    "speaker_persona": "年轻但不夸张，朋友式生活观察",
    "primary_voice_id": "Chinese (Mandarin)_Sincere_Adult",
    "alternatives": [
      "Chinese (Mandarin)_Radio_Host",
      "Chinese (Mandarin)_Straightforward_Boy"
    ],
    "continuity_priority": "high",
    "request_strategy": "one coherent paragraph per request",
    "reason": "基础音色已具备自然聊天感，不需要通过多次情绪切换塑造人设",
    "avoid": [
      "逐句独立生成",
      "用 angry 和 happy 反复改变同一人物音色",
      "用 speed、pitch、vol 修补不合适的基础音色"
    ]
  }
}
```
## Unified emotion, voice, and synthesis workflow

Use this workflow as the authoritative path when a task needs both emotional narration analysis and MiniMax voice selection. Earlier keyword rules, comedy-role rules, and voice heuristics support this workflow but do not replace it.

### Phase 1: Understand the whole article

Before selecting any emotion or voice, determine:

- Genre and delivery context.
- Narrator position and intended listener relationship.
- Default emotional baseline.
- Emotional arc: setup, tension, reversal, climax, resolution, and ending.
- Whether quoted emotions belong to the narrator, another character, or the desired delivery.
- Whether the material needs continuity, dramatic range, or a deliberately stylized character.

Do not select a voice from isolated keywords. Do not mark emotions before establishing the article-level baseline.

### Phase 2: Analyze emotional causes

For each candidate sentence or phrase, analyze in this order:

1. Experiencer: who feels or should perform the emotion.
2. Trigger: the event, result, threat, loss, reward, rejection, or revelation causing it.
3. Target: who or what the emotion concerns.
4. Valence and arousal.
5. Expectedness, controllability, certainty, responsibility, and reversibility.
6. Negation, contrast, rhetorical question, exaggeration, quotation, and irony scope.
7. Context role: setup, escalation, act-out, turn, punchline, callback, climax, or resolution.
8. Delivery intention: what the listener should hear, which may differ from a character's literal emotion.

The final annotation set must contain no more than `15` spans. Each annotated source span must contain no more than `20` visible characters. Select only emotionally or narratively salient spans and keep source order.

### Phase 3: Select the base voice

Select the voice after the emotional arc is understood but before synthesis requests are planned.

- Match genre, speaker persona, audience relationship, authority, intimacy, age impression, and performance strength.
- Prefer a voice that naturally expresses the baseline without correction.
- Strongly characterized voices require fewer explicit emotion changes.
- Continuity-sensitive narration and stand-up should use one primary voice throughout.
- Return one primary voice and at most two audition alternatives with concrete reasons.
- Use the controlled audition protocol from `references/minimax-voice-selection.md` when confidence is low.

### Phase 4: Separate annotations from synthesis

Always produce two different products:

1. `emotion_annotations`: short evidence spans used to understand and explain emotion.
2. `synthesis_plan`: complete speakable text and actual MiniMax request boundaries.

Never synthesize only the short annotation spans. Never create one TTS request for every annotation. Unannotated text must remain in the spoken output.

For continuity-sensitive content:

- Keep one base delivery state for at least `80-90%` of the article.
- Prefer one coherent paragraph per request.
- Allow at most `1-3` explicit emotional departures in a normal short article, even when the analysis contains more annotations.
- Use an explicit emotion only when wording, punctuation, and pause cannot communicate a genuine act-out, threat, loss, or reveal.
- Do not alternate `happy`, `angry`, and `surprised` merely to create variety.

### Phase 5: Generate the emotional direction prompt

Use the following structure when creating a WorkAgent or model prompt for emotional analysis:

```text
你是中文旁白情绪导演。你的任务不是寻找情绪关键词，而是先理解全文，再判断声音应该向听众表达什么。

先分析：文章类型、叙述者立场、目标听众、默认语气，以及铺垫、冲突、反转、高潮、收束构成的情绪弧线。

逐句判断：情绪体验者、触发事件、情绪对象、结果、正负效价、唤醒强度、可控性、确定性、预期违背、责任归属、否定作用域、转折重点、引用人物与旁白者的区别，以及是否存在反问、夸张或反讽。

只选择真正影响听感的关键片段。整篇最多15个情绪片段，每段不得超过20个可见字符，必须保持原文和原顺序。一个片段只能选择一个主情感；复合情绪拆成相邻短片段。

可选主情感：happy、sad、angry、fearful、disgusted、surprised、calm、fluent。普通说明和过渡允许不标注。surprised只负责发现或反转瞬间，不负责后续结果。

每个片段必须说明 experiencer、trigger、appraisal、context_reason 和 why。why必须解释事件与上下文，不能只写“包含某个关键词”。

情绪分析标签不等于MiniMax请求边界。最终另外输出完整 synthesis_plan，保留全部原文，并优先保持一个人、一个基础音色和连续语流。
```

Add genre-specific instructions after this common prompt. For stand-up, add comedy roles and require the model to distinguish real anger or sadness from mock-rant, self-deprecation, and audience-facing punchlines.

### Phase 6: Build voice-aware timing

Do not reuse one pause budget for every voice. Start with these production defaults and refine after a controlled audition:

| Voice or family | Normal explicit pause | Pre-punchline maximum | Notes |
|---|---:|---:|---|
| `Sincere_Adult` | `0.12-0.20s` | `0.30-0.40s` | General conversational stand-up baseline |
| `Radio_Host` | `0.10-0.18s` | `0.28-0.38s` | Naturally compact and information-forward |
| `Stubborn_Friend` | `0.08-0.15s` | `<=0.30s` | Persona already adds emphasis and pauses |
| `Straightforward_Boy` | `0.08-0.15s` | `<=0.30s` | Do not assume the name guarantees fast timing |
| `Laid_BackGirl` | `0-0.10s` | `0.20-0.28s` | Natural cadence is already relaxed |
| Strong announcer or character voices | audition first | audition first | Avoid as a general stand-up default |

Punctuation already creates pauses. Do not routinely place a long `<#x#>` immediately after `。！？；：`. If a precise pause marker is required, reduce punctuation-driven delay or use a smaller marker so the two pauses do not stack.

Treat `>=0.8s` silence as suspicious unless the text explicitly performs waiting, silence, shock, or a deliberate audience hold. Report intentional and accidental long pauses separately.

### Phase 7: Synthesis defaults

- Default quality model: `speech-2.8-hd` when available for the account and region.
- Set `language_boost` to `Chinese` for Mandarin-focused content.
- Send `voice_id` and documented audio settings.
- Do not send `speed`, `pitch`, or `vol` unless the user explicitly requests them.
- Prefer no explicit emotion on the first audition pass.
- If explicit emotion is required, confirm support for the selected model and use it minimally.
- Do not use sound tags merely because a line is funny. Add `(chuckle)` or similar only when the script requires an audible action.
- Use one request for a coherent short paragraph whenever possible.
- If splitting is unavoidable, trim edge silence and audit timbre continuity before concatenation.

### Phase 8: Mastering and quality audit

Loudness normalization happens after MiniMax synthesis and is not a `vol` adjustment.

- Short-form narration target: approximately `-14 LUFS`, true peak no higher than `-1 dBTP`.
- Preserve the raw MiniMax file and create a mastered output separately.
- Measure actual integrated loudness after encoding; a one-pass target may undershoot, so use measured or two-pass normalization when exact delivery matters.
- Detect silence at a consistent threshold and report count, total silence, longest silence, and all `>=0.8s` regions.
- Report request count and concatenation boundary count. Zero boundaries is preferred for a short single-speaker paragraph.
- Acoustic checks can verify continuity risks, pauses, clipping, and loudness, but they do not replace human judgment of whether a voice is appealing or funny.

### Required final JSON contract

```json
{
  "article_analysis": {
    "genre": "standup",
    "narrator_position": "朋友式观察者",
    "audience": "短视频观众",
    "baseline_delivery": "自然、克制、带轻微自嘲",
    "emotion_arc": ["premise", "escalation", "turn", "punchline"]
  },
  "voice_selection": {
    "primary_voice_id": "Chinese (Mandarin)_Sincere_Adult",
    "alternatives": ["Chinese (Mandarin)_Radio_Host"],
    "continuity_priority": "high",
    "reason": "基础聊天感能够覆盖全文，不需要频繁切换情绪",
    "pause_profile": "sincere_adult"
  },
  "emotion_annotations": [
    {
      "text": "原文关键片段",
      "source_start": 0,
      "source_end": 8,
      "emotion": "surprised",
      "intensity": 0.55,
      "confidence": 0.86,
      "experiencer": "旁白者",
      "trigger": "预期被打破",
      "appraisal": "突然、低风险、结果尚未展开",
      "context_reason": "承担反转瞬间",
      "why": "前文建立正常预期，此处第一次揭晓异常结果"
    }
  ],
  "synthesis_plan": {
    "model": "speech-2.8-hd",
    "request_count": 1,
    "base_emotion": null,
    "explicit_emotion_changes": [],
    "uses_speed_pitch_vol": false,
    "chunks": [
      {
        "text": "包含全部原文的完整可朗读段落",
        "voice_id": "Chinese (Mandarin)_Sincere_Adult",
        "emotion": null,
        "pause_strategy": "voice-aware"
      }
    ]
  },
  "quality_checks": {
    "annotation_count_lte_15": true,
    "annotation_span_lte_20_chars": true,
    "full_text_preserved": true,
    "single_speaker_voice_consistent": true,
    "long_silence_audit_required": true,
    "post_master_target": "-14 LUFS / -1 dBTP"
  }
}
```

For deeper rationale and tested voice-specific timing observations, read `references/emotion-voice-synthesis-workflow.md`.
