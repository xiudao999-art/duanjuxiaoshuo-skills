# Whole-series overlapping-window planning

Read this reference when `planningMode` is `overlapping_question`.

## Goal

For a normally rich 40-episode drama, retain 10–16 overlapping-question continuous windows first, then add qualified character, relationship, action, mystery, and special-theme windows. Episodes may overlap across windows; story identity may not. Scale every category down when the source lacks qualified causal arcs.

## Production taxonomy and capacity

Assign exactly one primary `storyType` to every planned video. The ranges are planning estimates, not quotas:

| storyType | Chinese label | Qualification | Typical 40-episode capacity |
| --- | --- | --- | ---: |
| `continuous_plot` | 连续剧情窗口 | A coherent 4–8 episode causal arc with a distinct central question; episode ranges may overlap across videos | 10–16 |
| `character_arc` | 主角或重要配角人物线 | One character changes through goals, choices, costs, and consequences | 4–8 |
| `relationship_arc` | 爱情亲情背叛等关系线 | A relationship changes state through visible actions and decisions | 4–8 |
| `action_payoff` | 武打打脸营救等类型线 | Physical or status conflict shares one objective and produces a visible payoff | 4–8 |
| `mystery_reveal` | 身份悬案伏笔反派线 | Clues, concealment, wrongdoing, or identity lead to a supported reveal | 4–8 |
| `special_theme` | 对照道具喜剧等特殊线 | A recurring contrast, object, misunderstanding, dialogue pattern, or motif forms a causal micro-story | 2–5 |

Do not add the category maxima to promise a fixed total. The same event may qualify for several categories during candidate generation, but global novelty and reuse checks decide which version survives.

Assign a specific `narrativeLens` under the primary category. Examples:

- `continuous_plot · result_first` → `连续剧情窗口·结果倒叙`
- `relationship_arc · romance_progression` → `爱情亲情背叛等关系线·爱情推进`
- `action_payoff · action_escalation` → `武打打脸营救等类型线·武打升级`
- `mystery_reveal · hidden_identity` → `身份悬案伏笔反派线·隐藏身份`

Record both the stable IDs and Chinese labels in `series-plan.json`, the per-video `job.json`, the delivery filename, and `qc-report.json`.

## Corpus contract

Create these reusable artifacts before selecting windows:

- `series-corpus.jsonl`: verbatim utterances with episode, start, end, speaker, text, confidence, and word timing reference.
- `characters.json`: canonical character IDs, aliases, roles, relationships, goals, secrets, and identity changes.
- `events.jsonl`: stable event nodes with evidence ranges.
- `story-graph.json`: temporal, causal, relationship, reveal, contrast, and motif edges.
- `shot-index.jsonl`: visible characters, action, location, emotion, objects, motion, dialogue state, and visual-quality score.
- `used-segments-ledger.json`: globally reserved source ranges, narration claims, and audited callbacks.

Do not use an episode summary as a replacement for the verbatim corpus. Keep uncertain ASR text marked with confidence and review it against audio before admitting dialogue.

## Event schema

Every selected event needs:

```json
{
  "eventId": "E0187",
  "episodes": [12],
  "characters": ["C01", "C02"],
  "goal": "",
  "obstacle": "",
  "action": "",
  "reaction": "",
  "consequence": "",
  "reveal": "",
  "emotionBefore": "",
  "emotionAfter": "",
  "dependencies": [],
  "evidence": [{"episode": 12, "start": 318.2, "end": 342.7}],
  "visualStrength": 0.0,
  "dialogueStrength": 0.0,
  "hookStrength": 0.0
}
```

## Candidate generation

When the requested scope is 8–10 template families or 50–70 candidate
hypotheses, follow [template-validation.md](template-validation.md). Extract
4–8 story atoms per normal episode and distinguish candidate hypotheses from
production-eligible windows.

1. Select one narrative lens and one answerable central question.
2. Assign the primary production category that best describes the promised viewer experience, not merely the largest number of shots.
3. Filter events relevant to that question.
4. Walk causal and reveal links to form a path with a hook, setup, escalation, reversal, payoff, and consequence.
5. Bind a coherent 4–8 episode coverage. Prefer consecutive coverage; document any skipped episode and the narration bridge it requires.
6. Generate 1.5–2 times the requested final count so weak and repetitive candidates can be removed.
7. Reject candidates that require invented motives, wrong-character footage, or more exposition than visible action.

## Candidate scoring

Score each candidate out of 100:

- Hook strength: 20
- Causal coherence: 20
- Escalation and emotional change: 15
- Visual and dialogue evidence: 15
- Payoff strength: 15
- Difference from accepted windows: 10
- Editability and complete dialogue: 5

Require a recommended minimum of 72. Prefer a smaller batch over windows below the threshold.

## Difference test

Two overlapping windows are distinct only when all are true:

- Their central questions demand different answers.
- Their payoffs are different visible decisions, revelations, victories, losses, or relationship changes.
- At least 60 percent of each window's core events are not core events in the other.
- Their narration is not a paraphrase of the same causal explanation.
- Their principal hook and payoff footage are different, unless an iconic callback is explicitly audited.

Compute core-event overlap as:

```text
intersection(core events A, core events B) / min(len(A), len(B))
```

Reject a pair above `0.40` by default. Episode overlap alone is allowed and is not a duplication signal.

## Batch selection

Select windows incrementally by score adjusted for novelty. After accepting a window, penalize candidates that reuse its central question, core events, hook, payoff, narration claims, or principal source ranges. Keep representation balanced across available lenses; do not force a lens unsupported by the drama.

For 40 episodes, use `10–16` as the normal final target. This is a quality range, not a quota.

This `10–16` range describes continuous-plot windows only. A broader
whole-series exploration may generate 50–70 hypotheses across all supported
template families, but the final production count is whatever survives the
fact, payoff, evidence, overlap, and editability gates.

## Reuse policy

- Within one video: do not reuse a source shot.
- Across the batch: reserve ordinary principal footage after first use.
- Allow an iconic shot at most twice only when the narrative function differs, such as result-first hook versus later evidence payoff.
- Record exact ranges and semantic narration claims in the global ledger.
- Re-run global duplicate checks after every completed delivery, not only after the batch is finished.
