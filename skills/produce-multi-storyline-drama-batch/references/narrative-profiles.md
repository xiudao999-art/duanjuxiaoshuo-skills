# Narrative profile contract

Separate global delivery quality from story-specific structure. Every candidate
and production job must declare `narrative_profile`; never apply one profile's
hook, dialogue budget, chronology, or payoff test to the whole batch.

## Global contract

Apply these rules to every profile:

- one central question and a causal, evidence-grounded event path;
- every factual clause bound to event-ledger records; no invented facts;
- event-bound visuals selected before rendering, source footage at 1.0x, no
  repeated range, incomplete action, unfinished dialogue, or lexical fallback;
- complete final sentence, encoded cut audit, caption contract, hard-subtitle
  Pilot, loudness, format, and delivery gates;
- concrete oral narration, normally averaging 10–26 Han characters per sentence
  with a normal maximum of 36. A profile may impose a tighter range.

## Profiles

| Profile | Typical families | Native story logic | Default hook | Dialogue budget | Picture floor |
|---|---|---|---|---|---|
| `P01_dual_time_conflict` | F01, selected F10 | current crisis → backfill cause → evidence/action → return and payoff | 7–12 s | 3–4 turns, 28–48 s | exact ratio ≥0.50, average ≥7 s, zero clips under 5 s |
| `P02_agency_counterattack` | F02, F06, F09, F10 | pressure → costly choice → capability/countermove → consequence | 5–10 s | 2–4 turns, 18–45 s | exact ratio ≥0.40, average ≥6 s |
| `P03_relationship_arc` | F03, F04, F05, F14 | bond → rupture/misread → revealing choice → repair or separation | 5–12 s | 2–5 turns, 20–55 s | exact ratio ≥0.35, average ≥6 s |
| `P04_reveal_investigation` | F07, F08, F12 | anomaly/clue → false answer → verification → reveal and consequence | 5–10 s | 2–4 turns, 15–45 s | exact ratio ≥0.45, average ≥6 s |
| `P05_contrast_anthology` | F11, F13 | shared theme → escalating contrasts → synthesis/payoff | 3–8 s | 0–4 turns, 0–40 s | exact ratio ≥0.25, average ≥4.5 s |

These are starting contracts, not quotas. Override a numeric default only in an
approved per-job `profile_overrides` record with an evidence-based reason. Never
weaken zero-contradiction, zero-unbound-fact, complete-dialogue, subtitle, or
encoded-frame gates.

## Selection

Choose the profile from the candidate's actual central question and causal
shape, not from the family label alone. A family can use another profile when
the evidence supports it; for example, an F10 rescue can use P01 when opened on
the rescue crisis, or P02 when centered on the protagonist's decision and
countermove. Record both `family_id` and `narrative_profile` in planning,
production, filenames/index metadata, and QC reports.

Read [sample-style-story-editing.md](sample-style-story-editing.md) only for
`P01_dual_time_conflict`.
