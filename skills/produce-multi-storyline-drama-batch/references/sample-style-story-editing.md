# Sample-style causal recap method

Use this method only for `P01_dual_time_conflict`. Global delivery rules live in
[narrative-profiles.md](narrative-profiles.md); do not apply this profile's hook,
dialogue budget, reverse chronology, or payoff test to other profiles.

## Story shape

1. Open with a 7–12 second source scene that contains a visible abnormal action,
   accusation, danger, decision, or irreversible result.
2. State the current problem in one short narration beat, then use a clear bridge
   such as “可这件事并不是从这里开始的” before moving backward.
3. Reconstruct only the causes needed to understand the hook. Build a causal
   chain: trigger → worsening cost → character choice → evidence/action →
   reversal → visible payoff.
4. Return to the opening problem before the ending. Pay off the exact question
   raised by the hook; do not finish on an unrelated later event.
5. Keep one central question. A chronological event list is not a story.

## Narration language

- Put the character, visible action, and consequence before abstract judgement.
- Prefer concrete oral sentences over summaries such as “事情变得越来越复杂”.
- Let each sentence add a cause, cost, choice, piece of evidence, or payoff.
- Use contrast connectors sparingly and purposefully: `可`, `没想到`, `更离谱的是`,
  `接着`, `等到`, `这一次`.
- Target an average of roughly 14–24 Han characters per sentence and keep normal
  sentences at or below 32. Split longer sentences at a semantic pause.
- Use three narration blocks separated by three or four complete source-dialogue
  turns when the material supports it. A practical two-minute starting range is
  360–500 Han characters plus 28–48 seconds of source dialogue; always synthesize
  and measure before locking duration.
- Never invent a motive, prop, document, action, or consequence. Every factual
  clause must map to an event ledger record. Remove unsupported copy even when it
  sounds dramatic.

## Planning-time picture binding

Bind visuals after the script is approved but before TTS/render:

- Give every narration beat a `beat_id`, `beat_text`, `event_id`, `scene_id`,
  reviewed source range, required character/action/location, match type,
  confidence, and contradiction flag.
- Use the best event-bound long scene, not a clip retrieved from narration-word
  similarity. A preceding verified scene may continue under a related clause.
- Use 1–3 continuous clips per narration block, normally 5–19 seconds each.
  Require an average source-clip duration of at least seven seconds and normally
  zero clips below five seconds.
- If reviewed clips exceed synthesized narration duration, first add a concise,
  causally useful line or choose a naturally shorter reviewed range. Never speed
  source drama, truncate an action, or silently replace the shot with a lexical
  match. Require selected picture duration not to exceed the narration block by
  more than one frame; keep a deliberate last-frame hold at six seconds or less.
- When two separately cleaned ranges share the same source boundary, merge them
  when they form one continuous shot. Otherwise leave one encoded frame between
  ranges so the boundary frame is not duplicated.

## Dialogue and handoff

- Enter at a complete sentence or speaker turn, with enough pre-roll to hear the
  first syllable naturally.
- Leave after the complete final sentence and retain 0.3–0.5 seconds of reaction
  or room tone when available.
- Never place narration over an unfinished source sentence. Mute incomplete
  dialogue when its picture is used as narration B-roll.
- Keep source dialogue and drama picture at 1.0x; accelerate only synthesized
  narration when configured.

## Required regression checks

Run these checks on the encoded delivery:

- duration 110–135 seconds, complete final sentence, final tail 0.45–6 seconds;
- hook 7–12 seconds and one non-empty central question;
- three or four complete dialogue turns, normally 28–48 seconds total;
- semantic alignment passed, exact-match clip ratio at least 0.50,
  exact-or-context duration ratio at least 0.90, contradiction and unbound-beat
  counts zero, average source clip at least seven seconds, clips under five
  seconds zero;
- encoded cut-boundary audit has zero flash candidates;
- caption round-trip, word split, protected-term split, overlap, multiline, and
  orphan checks pass;
- hard-subtitle Pilot and caption-reset encoded contact sheets pass.

The validated P01 baseline from the property-parking sample was 110.36 seconds,
an 8.40-second hook, four complete dialogue turns totaling 44.19 seconds, seven
exact-bound narration clips averaging 7.38 seconds, zero sub-five-second clips,
zero unbound factual beats, 11 checked cuts with zero flash candidates, and a
4.25-second complete-sentence tail. Treat those values as a regression example,
not a template that every story must copy exactly.
