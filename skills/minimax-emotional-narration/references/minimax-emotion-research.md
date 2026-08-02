# MiniMax narration emotion research

Use this reference to resolve context-sensitive or ambiguous emotion decisions. The operating principle is: infer the event and appraisal first, then map the result to one MiniMax label.

## Evidence base

- MiniMax T2A HTTP API: https://platform.minimax.io/docs/api-reference/speech-t2a-http
- MiniMax MCP guide and emotion values: https://platform.minimax.io/docs/guides/mcp-guide
- Appraisal theories for emotion classification: https://aclanthology.org/2020.coling-main.11/
- Implicit sentiment from event-centered representations: https://aclanthology.org/2021.emnlp-main.551/
- Contextual reasoning for conversation emotion: https://aclanthology.org/2021.acl-long.547/
- Segment-based Chinese emotion detection: https://aclanthology.org/W14-6809/
- Chinese negation and contrast transition: https://aclanthology.org/Y09-1033/
- Chinese irony from sentence/context contrast: https://aclanthology.org/anthology-files/anthology-files/pdf/ijclclp/2022.ijclclp-2.5.pdf
- Emotion experiencer, target, and cause: https://aclanthology.org/anthology-files/pdf/C/C18/C18-1114.pdf
- Narrative structure and emotional peaks: https://pmc.ncbi.nlm.nih.gov/articles/PMC7413736/
- Fine-grained emotion and neutral annotation: https://aclanthology.org/2020.acl-main.372/
- Limits of transferring text emotion directly to speech: https://aclanthology.org/2026.findings-eacl.136/

Research implications:

- Emotion words are insufficient. Events such as winning, losing, escaping danger, or being betrayed imply emotion without naming it.
- Context and speaker identity are necessary to resolve who feels what and why.
- A Chinese sentence can contain multiple segment-level emotions. Select the dominant emotion of each short semantic span rather than averaging the sentence.
- Text emotion does not uniquely determine vocal emotion. Treat the requested audience effect and narration genre as explicit direction.
- Emotional peaks are more useful for expressive narration than dense sentence-by-sentence labeling.

## Full-text analysis frame

Before labeling phrases, record:

| Field | Question |
|---|---|
| Narration type | Story, ad, tutorial, commentary, reflection, or factual explainer? |
| Narrator stance | Participant, witness, evaluator, authority, or neutral guide? |
| Audience effect | Should listeners feel tension, empathy, shock, relief, trust, or motivation? |
| Default tone | Neutral, fluent, calm, or already emotionally charged? |
| Arc | Where are setup, conflict, escalation, reveal, climax, resolution, and CTA? |

Use the nearest previous and next sentence as local context and the whole arc as global context.

## Appraisal decision matrix

| Emotion | Event/result | Valence | Arousal | Control/certainty | Responsibility or action tendency |
|---|---|---|---|---|---|
| `happy` | Success, reward, reunion, hope, relief | Positive | Medium-high | Goal achieved or control restored | Approach, celebrate, share |
| `sad` | Loss, separation, failure, regret | Negative | Low-medium | Low control; often irreversible | Withdraw, reflect, mourn |
| `angry` | Injustice, obstruction, betrayal, insult | Negative | High | Often certain about blame | Other/self responsibility; confront |
| `fearful` | Threat, uncertainty, countdown, risk | Negative | High | Low control or low certainty | Avoid, protect, prepare |
| `disgusted` | Contamination, contempt, moral violation | Negative | Medium-high | Clear rejection | Distance, expel, refuse |
| `surprised` | Unexpected reveal or reversal | Mixed/unknown | High | Expectation violated; discovery now certain | Orient attention |
| `calm` | Safety, acceptance, reassurance, recovery | Positive/neutral | Low | Control or safety restored | Settle, trust, continue |
| `fluent` | Explanation, procedure, factual progression | Neutral | Low-medium | High clarity | Understand, follow |
| `neutral` | Bridge with no meaningful affect | Neutral | Low | Not applicable | Leave unselected |

`surprised` describes the discovery, not whether the discovered outcome is good or bad. Split the reveal cue from the result whenever both can stand as meaningful phrases.

## Chinese language operators

### Negation

Determine the exact scope before using emotion words:

- `我一点也不开心` is not `happy`; it usually implies restrained `sad` or `neutral` depending on context.
- `别怕，已经安全了` suppresses `fearful` for the narrator and supports `calm` reassurance.
- `这并不是失败` must not be labeled `sad` solely because it contains “失败.”
- `我不是生气，我只是失望` gives priority to the explicit correction and should favor `sad`.

### Contrast and correction

Give post-contrast content more weight, but preserve both sides when they form an emotional turn:

- `本来以为失败了，但是我们赢了` can contain a negative setup followed by `happy` relief.
- `看起来很普通，却救了我一次` uses the second clause as the emotional outcome.
- `不是害怕，而是愤怒` should be `angry`, not `fearful`.

### Rhetorical questions

A question mark is not an emotion label. Infer the speech act:

- `凭什么每次都是我？` expresses blame/unfairness and maps to `angry`.
- `万一赶不上怎么办？` expresses uncertain future threat and maps to `fearful`.
- `你也喜欢这首歌吗？` is usually neutral or happy invitation depending on context.

### Irony

When literal praise conflicts with a negative event, use the intended evaluation:

- `事情都搞砸了，你可真会挑时候` is likely `angry` or `disgusted`, not `happy`.
- `真是个天才，又把钥匙锁屋里了` is criticism despite positive surface wording.
- Without a conflicting event or context, lower confidence instead of assuming irony.

### Quotation and experiencer

- `他说“我很害怕”` assigns fear to the quoted speaker.
- `他说他很害怕，但我很平静` should split into different experiencers and labels.
- A narrator can quote anger while maintaining a neutral documentary tone. Choose the desired performed voice, not blindly the quoted word.

## Intensity and confidence

Use `intensity` for the desired vocal strength:

- `1`: faint undertone.
- `2`: restrained but audible.
- `3`: normal expressive narration.
- `4`: strong hook, conflict, reveal, or payoff.
- `5`: rare peak; explicit high stakes or extreme reaction.

Use `confidence` for classification certainty:

- `1`: ambiguous, context-poor, or possible irony.
- `2`: supported by an event or several indirect cues.
- `3`: explicit event/appraisal plus consistent context.

Do not increase intensity merely because a phrase contains an exclamation mark. Degree adverbs, stakes, event severity, repetition, punctuation, and narrative position should agree.

## Selecting no more than 15 beats

Score each non-neutral candidate with:

`salience = 2 * intensity + 2 * confidence + role_weight + transition_bonus - redundancy_penalty`

- `role_weight = 3` for hook, reveal, or climax.
- `role_weight = 2` for tension, resolution, or CTA.
- `role_weight = 0` for setup or bridge.
- `transition_bonus = 2` when the dominant emotion changes from the previous emotional candidate.
- `redundancy_penalty = 3` when the same emotion and narrative role repeat within the previous two candidates.

Select the highest-scoring 15 at most, then restore original order. Prefer one strong representative phrase over several near-duplicates.

## MiniMax boundaries

- Keep each selected phrase at 20 visible non-space characters or fewer.
- Preserve original wording. Extract a smaller complete phrase instead of paraphrasing.
- Put the emotional label in request metadata, not inside spoken text.
- MiniMax pause markers use `<#x#>` and must not be consecutive. Supported T2A documentation allows decimal-second pauses between speakable text.
- Speech 2.8 supports parenthetical interjections such as `(laughs)`, `(chuckle)`, `(sighs)`, `(inhale)`, `(exhale)`, `(gasps)`, and `(groans)`; use them only when the event supports the vocal action.
- This skill intentionally does not produce delivery-control fields. Its output is emotion labeling, pause planning, and sparse interjections only.
- For neutral text, omit the emotion request field rather than inventing a neutral TTS label.

## Annotation spans versus synthesis chunks

- An annotation span answers “which exact words carry the emotion?” and remains at most 20 visible characters.
- A synthesis chunk answers “what complete semantic unit can MiniMax speak naturally with one dominant emotion?” and may be longer than 20 characters.
- Do not synthesize particles such as `吧`, `呢`, `啊`, `呀`, or incomplete frames such as `真正让人愤怒的是` as independent requests.
- Prefer a complete sentence. When a sentence contains multiple evidence spans, use the highest-salience emotion as the sentence-level synthesis emotion unless a punctuation-supported semantic turn requires two complete clauses.
- Merge adjacent neutral sentences or same-emotion sentences when doing so reduces joins without changing the intended arc.
- Aim for roughly 3-6 actual voice switches per 100 Chinese characters.

## Silence normalization

MiniMax requests often contain natural leading and trailing silence. When multiple requests are concatenated:

1. Detect each request's leading and trailing silence.
2. Trim edge silence while preserving a short 20-50 ms safety margin.
3. Concatenate the trimmed speech.
4. Add exactly one controlled pause at the semantic boundary.

Recommended assembled pauses:

- Comma or light clause boundary: `0.15-0.30` seconds.
- Ordinary sentence boundary: `0.35-0.65` seconds.
- Reveal, climax, or deliberate emotional turn: `0.70-1.00` seconds.

Do not stack model edge silence, an inline pause marker, and an assembler silence file at the same boundary.

## Required review cases

| Text | Expected reasoning |
|---|---|
| `我真的太开心了` | Explicit positive state -> `happy`. |
| `终于拿到第一名` | Implicit successful event -> `happy`. |
| `我一点也不开心` | Negation blocks literal happy reading -> restrained `sad` or context-dependent neutral. |
| `凭什么每次都是我？` | Unfairness and blame -> `angry`. |
| `再晚一步就来不及了` | Future threat and low control -> `fearful`. |
| `本来以为失败了，没想到真的中了` | Negative setup, `surprised` reveal, then `happy` result. |
| `事情搞砸了，你可真会挑时候` | Context reverses literal praise -> `angry`/`disgusted`. |
| `他说他很害怕，但我很平静` | Separate experiencers -> `fearful`, then `calm`. |

## Stand-up and comedy monologue profile

Analyze joke mechanics before emotional vocabulary:

| Comedy role | Function | Default delivery |
|---|---|---|
| `premise` | Establish a relatable observation | Plain or `fluent`; conversational |
| `setup` | Supply facts needed for the joke | Plain; do not oversell |
| `escalation` | Increase absurdity or stakes | Slightly stronger, usually still controlled |
| `self_deprecation` | Make the performer the comic target | Dry/playful; not automatically `sad` |
| `act_out` | Quote or impersonate a person/object | Preserve as a complete voice chunk |
| `mock_rant` | Exaggerated complaint | Restrained `angry` only when intentionally performed |
| `turn` | Reinterpret the premise or reveal misdirection | `surprised` when expectation genuinely flips |
| `punchline` | Deliver the main incongruity | Dry plain, `surprised`, or light `happy` depending on mechanism |
| `tag` | Short follow-up joke | Light, quick, 0.25-0.35s follow-through |
| `callback_punchline` | Return to an earlier image | Light `happy` or `surprised`; allow recognition beat |

Stand-up disambiguation rules:

- `你们有没有发现` is a premise marker, not evidence of surprise.
- `再也没有隐私`, `我连袜子都穿不动`, and similar hyperbole are usually persona exaggeration, not literal sadness.
- Workplace words such as `老板`, `领导`, `加班`, and `第八版` support mock-rant context but do not require full anger.
- Absurd agency such as `生菜管理我`, `冰箱有领导力`, or `跟吊灯熟了` supports a comic turn/punchline even without explicit emotion words.
- Do not synthesize audience laughter or make the performer laugh at every punchline.
- Keep one sentence per synthesis request and avoid merging premise, turn, and punchline.

Stand-up pause defaults:

- Ordinary premise/setup boundary: `0.28-0.40` seconds.
- Before turn or punchline: `0.50-0.60` seconds.
- After punchline/tag: `0.25-0.35` seconds.
- Callback recognition beat: `0.40-0.55` seconds.
