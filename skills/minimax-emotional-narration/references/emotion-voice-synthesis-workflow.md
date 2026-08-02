# Emotion, voice selection, and MiniMax synthesis workflow

## Purpose

This reference consolidates the production lessons from narration, science-explainer, and stand-up tests. It separates semantic emotion analysis from the technical choices that determine whether a generated voice remains one believable person.

## Three layers that must not be confused

### Semantic layer

Identify emotional causes, context, narrative roles, irony, negation, and the intended listener-facing delivery. This layer can contain up to 15 short evidence spans of no more than 20 visible characters each.

### Direction layer

Choose one base persona and describe restrained performance changes. A semantic label does not automatically become an API emotion parameter.

### Synthesis layer

Choose the real voice ID, model, request boundaries, pause markers, and mastering process. This layer must preserve all text and prioritize identity continuity.

## Why one voice can sound like two people

MiniMax T2A requests are stateless. Separate requests using the same `voice_id` can differ in resonance, breath, cadence, and apparent age. Strong changes such as `angry` to `happy` magnify the difference. Post-synthesis loudness normalization does not cause this identity change.

The preferred repair order is:

1. Use one coherent request.
2. Select a more suitable base voice.
3. Reduce explicit emotion changes.
4. Shape the joke with wording and voice-aware pauses.
5. Split only when a true character change or incompatible emotional state requires it.

## Tested Chinese stand-up observations

### Sincere Adult

Useful general baseline for restrained observation and self-deprecation. Explicit pauses can remain moderate, but long punctuation plus a `0.50s` marker may exceed `0.8s` in the rendered audio.

### Radio Host

The most compact pacing in the controlled five-voice test. Suitable for science-comedy, podcasts, and information-first stand-up. Use small markers because the voice already organizes clauses clearly.

### Stubborn Friend

Persona naturally carries complaint and mock-rant. Repeated `angry` is unnecessary. Long markers produced multiple `0.85-0.92s` gaps in testing, so use a smaller pause budget.

### Straightforward Boy

Young and direct in persona, but the tested output still created several long gaps. Do not infer timing from the voice name; measure the rendered output.

### Laid-back Girl

Appropriate for relaxed female chat and self-deprecation. Natural cadence is already slow, so omit most explicit pauses for compact short-form stand-up.

## Emotion prompt quality test

A useful emotional annotation explains an event and its appraisal:

```json
{
  "text": "真的中奖了",
  "emotion": "happy",
  "experiencer": "旁白者",
  "trigger": "获得意外奖励",
  "appraisal": "正向、低控制、结果已确认",
  "context_reason": "承接前一个 surprised 揭晓片段",
  "why": "快乐来自中奖结果，而不是因为文本中出现了情绪关键词"
}
```

A weak annotation says only `包含开心词` or assigns `surprised` to the entire result sentence.

## Stand-up interpretation rules

- `你们有没有发现` is normally a premise, not surprise.
- Self-deprecation is not sadness unless the speaker communicates genuine loss or helplessness.
- Exaggerated complaint is often mock-rant rather than real anger.
- Absurd agency and violated expectations often create the turn or punchline.
- `surprised` belongs to the discovery instant; the confirmed positive result is `happy` if it must be marked.
- Audience laughter is not a narrator emotion and does not justify automatic `(laughs)`.
- A punchline does not automatically require `happy`; neutral or fluent delivery often preserves dry humor better.

## Quality gates

- No more than 15 annotation spans.
- No annotation span longer than 20 visible characters.
- Original text order and meaning preserved.
- One emotion per annotation span.
- One primary voice per single-speaker article.
- One coherent paragraph per request when feasible.
- No `speed`, `pitch`, or `vol` unless explicitly requested.
- Suspicious silence audit at `>=0.8s`.
- Actual post-encode loudness measured rather than assumed.
- Raw and mastered audio stored separately.

## Official MiniMax references

- System voices: https://platform.minimax.io/docs/faq/system-voice-id
- Get Voice API: https://platform.minimax.io/docs/api-reference/voice-management-get
- T2A HTTP and pause markers: https://platform.minimax.io/docs/api-reference/speech-t2a-http
- Model capabilities: https://platform.minimax.io/docs/guides/models-intro
- MCP emotion compatibility: https://platform.minimax.io/docs/guides/mcp-guide
