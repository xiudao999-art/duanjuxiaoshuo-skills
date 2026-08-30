# Empirical template validation

Read this reference when the user wants to expand a full drama into many
different narratives, validate a taxonomy against real episodes, or estimate
how many distinct recaps the source can support.

## Separate hypotheses from production windows

Use three counts and never merge them:

1. `templateCount`: normally 8–10 reusable viewer-question families.
2. `candidateHypothesisCount`: normally 50–70 ideas for a rich 40-episode
   drama, generated before global deduplication.
3. `productionEligibleCount`: candidates that survive factual, causal,
   evidence, overlap, and editability gates.

The 50–70 range is an exploration pool, not a delivery promise. Report all
three counts. Never rename rejected paraphrases as different edits merely to
hit a quota.

## Extract story atoms at useful granularity

Do not create only one or two summary events per episode. Target 4–8 story
atoms per normal short-drama episode, reducing the target only when an episode
is exceptionally short or static. One atom records one meaningful change in a
goal, obstacle, action, reaction, evidence state, relationship state, cost, or
consequence.

Each atom needs:

- stable `eventId`, episode, participants, and evidence range;
- goal, obstacle, action, reaction, consequence, and reveal;
- hook, escalation, reversal, payoff, and cliffhanger suitability;
- dialogue and visual strength;
- one evidence level.

Use these evidence levels:

- `speech_verbatim`: exact source words with timing;
- `speech_supported`: a fact directly supported by source speech;
- `visual_confirmed`: visible in inspected source frames or footage;
- `inferred_question`: a plausible question, not an established answer.

Only the first three may support a declarative narration claim. Never convert
an `inferred_question` into a payoff. A generated micro-expression, prop,
camera angle, screen, or gesture is unverified until a human or vision pass
finds it in source footage.

## Derive template families from viewer questions

A template is not a topic label. It is a repeatable contract consisting of a
viewer question, eligible event pattern, expected escalation, and visible
payoff. Test these ten families, then keep only those supported by the drama:

| ID | Template family | Governing viewer question |
| --- | --- | --- |
| `F01` | Causal plot window | What chain of choices caused this result? |
| `F02` | Character strategy or transformation | How did this person change tactics, status, or self-definition? |
| `F03` | Relationship state transition | What actions changed trust, allegiance, intimacy, or hostility? |
| `F04` | Antagonist mechanism | How does the opposing side control people, information, or resources, and where does it fail? |
| `F05` | Ability or credibility proof | How is a disputed ability, claim, or competence repeatedly tested and accepted? |
| `F06` | Rule, resource, or economic game | Who controls money, rules, tasks, evidence, or allocation, and how does control move? |
| `F07` | Action, crisis, rescue, or public counterattack | What concrete objective escalates into a visible win, loss, or rescue? |
| `F08` | Identity, mystery, clue, or reveal | Which clues support an answer, and is that answer actually reached in available footage? |
| `F09` | Motif, prop, phrase, or behavior recurrence | How does a repeated object, phrase, costume, animal, or behavior change meaning? |
| `F10` | Alternate perspective, contrast, irony, or comedy | How does the same conflict look from another character, a before/after comparison, or an expectation gap? |

Drama-specific templates may use more vivid names, but bind each one to one
family ID. Mark a template `conditional` when its required payoff occurs after
the available source boundary.

After binding the family ID, choose one validated category pattern from
[category-editing-playbook.md](category-editing-playbook.md). The pattern is a
selection and editing contract, not another title tag. Reject a pattern when
its required event path, dialogue state change, visual bridge, or payoff is
absent. Do not apply a rule learned from one family to unrelated families.

Before scoring, apply the family-specific event-slot contract in
[category-story-selection.md](category-story-selection.md). Grade each event
as causal spine, motive evidence, category evidence, or decoration/repetition.
Reject a candidate when a required slot is missing; do not compensate with an
analytical sentence in the validation draft.

## Generate candidates in two writing passes

For each supported template, generate 5–7 candidate hypotheses. In the first
pass, write only a 180–300 Han-character validation draft plus the central
question, event path, hook, payoff, and novelty statement. This is long enough
to test story logic and cheap enough to discard.

After scoring and deduplication, expand only shortlisted candidates into the
500–650 Han-character production narration. Count script length locally; do
not trust a model's claimed count. Verify every quoted line against the
verbatim corpus before it enters either pass.

The validation draft must also state which category-specific pattern is being
tested and name the exact event evidence for each required beat. A generic
claim such as “use faster pacing” or “increase conflict” is not a valid pattern
test.

## Apply deterministic gates before simulated scoring

Reject or repair a candidate before subjective scoring when any condition is
true:

- the promised payoff is absent from available footage;
- fewer than four or more than eight episodes are used without an approved
  exception;
- fewer than five supported story atoms form the path;
- an event ID does not exist;
- a quote is not verbatim;
- a declarative claim is supported only by `inferred_question`;
- the hook, payoff, or principal footage conflicts with an accepted window;
- core-event overlap with an accepted candidate exceeds `0.40`.
- a required family-specific story slot has no supported event ID;
- a proposed event is retained only because it is spectacular or thematically
  similar while it changes no later action in that family.

Then simulate three perspectives independently: story editor, ordinary mobile
viewer, and evidence/editing editor. Score continuity 25, logic 25,
attraction 25, editability 15, and differentiation 10. Compute the aggregate
locally from the three returned score sets. Ignore a model-provided aggregate
field.

Apply verdicts only after hard gates:

- `strong`: aggregate at least 86 and no hard issue;
- `viable`: aggregate 72–85 and no hard issue;
- `repair`: potentially useful but one or more repairable hard issues remain;
- `reject`: absent payoff, invented fact, unusable evidence, or unresolved
  duplication.

## Validate difference at three levels

Two candidates are distinct only when all are true:

1. Their central questions require different answers.
2. Their core-event overlap is at most `0.40`.
3. Their principal hook, payoff footage, and causal explanation are materially
   different.

Episode overlap is allowed. A different title, lens label, opening sentence,
or chronology alone is not sufficient.

## Report empirical capacity

Report:

- episode and minute coverage;
- story-atom count and evidence coverage;
- templates tested, validated, conditional, and rejected;
- candidate hypotheses generated;
- hard-gate failures by reason;
- duplicate pairs above the overlap threshold;
- maximum or approximate maximum non-conflicting subset;
- production-eligible count and remaining coverage gaps.

Scale capacity from supported atoms and payoffs, not episode count alone. If a
24-episode source yields only 18 non-conflicting windows, say so; do not
extrapolate it to 50 by relabeling the same events.
