# Final delivery gates

## Story and evidence

- one central question and causal spine;
- hook pays off or opens an honest unresolved question;
- every factual narration clause maps to audited event IDs;
- no visual contradiction in identity, action, location, time, or emotional state;
- no repeated narration or repeated source range within a video.
- hook is 7–12 seconds when using the sample-style causal method, the current
  problem is explicit, and the ending pays off that same question;
- narration contains no factual clause without an event-ledger binding;
- sentence rhythm is predominantly oral and concrete rather than abstract event
  listing; normal average sentence length is roughly 14–24 Han characters.

## Edit integrity

- source drama and dialogue remain 1.0x;
- complete dialogue turns with 0.3–0.5 second breathing room;
- no narration over an unfinished source sentence;
- no half-shot, one-frame flash, accidental freeze, black frame, or decode error;
- every semantic beat stores the approved spoken narration text and its real
  TTS timing; event titles or summaries cannot stand in for narration text;
- the beat map resolves every event ID against the audited ledger and matches
  the locked story-plan hash, so visual repair cannot silently change the
  family, profile, central question, causal spine, hook, narration/dialogue
  text, event IDs or order, or payoff;
- semantic alignment satisfies the selected Profile's exact-clip,
  exact-duration, average-shot, and under-five-second thresholds from
  [narrative-profiles.md](narrative-profiles.md); globally require
  exact-or-context duration at least 0.90, neutral duration at most 0.10, and
  zero contradiction or unbound beats;
- `motion-coverage-audit.json` uses schema `motion-coverage-audit-v1`, reports
  `status=passed`, zero motion-shortfall/timeline-mismatch/hold-budget blocks,
  and `maximumClipHoldFrames<=3` before VSR/STTN starts;
- `hold_after` defaults to zero; no narration clip or entire narration block
  may use more than three hold frames, and cloned-frame/tpad compensation is
  forbidden;
- exactly one reviewed 540×960 preview and start/middle/end evidence for every
  semantic beat pass before VSR/STTN starts;
- encoded cut-boundary timestamps include `clip_duration + hold_after`, and the
  audit reports zero flash, picture-hold, and freeze-then-cut candidates;
- final sentence completes; tail is at least 0.45 seconds and normally no more
  than 6 seconds;

The final program tail is not a narration-picture freeze allowance. Keep
normal live picture or a deliberate end treatment throughout that tail.

Legacy compatibility is valid only for an exact SHA-256 artifact-set match in
[compatibility-baselines.json](compatibility-baselines.json). It may accept the
approved sample's legacy audit schema, but it cannot relax its Profile
thresholds and never applies to a new or changed render.

Visual repair gets one targeted safe-range pass inside already-bound
events/scenes and one deterministic recheck. If that second preflight fails,
mark the item `visual-coverage-pending` and continue the batch. Do not loop
through repeated model calls, VSR passes, previews, or full renders. Rerender
and rerun VSR only for clips whose locked EDL range changed; the story-plan hash
must remain unchanged.

## Captions

- exact approved-script round-trip;
- maximum 9 displayed characters per cue by default;
- no word split, protected-term split, cue overlap, multiline cue, orphan character, or stacked prior sentence;
- timing follows provider/word ASR and pause resets are visible in the encoded MP4;
- narration captions do not cover the source hard subtitles; the source subtitle must already be outside the narration frame or successfully repaired;
- each designed emphasis event owns a distinct caption cue; no cue receives
  multiple replacement animations.
- a multi-cue emphasis phrase is split into separate one-line events that clear between cues.

## Source hard subtitles

- every source master is classified as `clean`, `burned`, or `unknown`; none remain `unknown` at render time;
- every narration shot with active source subtitles has a reviewed removal/reframe policy;
- every burned-subtitle narration shot uses the locked VSR/STTN-cleaned file for its exact EDL range; missing cleaned bindings are a hard failure;
- narration footage is not swapped or cropped merely to avoid subtitles;
- the gray mosaic/blur rail covers the full repaired subtitle band and contains the new caption without clipping;
- dialogue shots preserve original subtitles and receive no narration-caption overlay unless a separate dialogue rebuild was approved;
- encoded Pilot checks first, middle, and last frame of every narration shot;
- readable source subtitle, source/generated overlap, vertical stretch, and seek-mismatch counts are zero;
- Pilot and framing-plan hashes match the final render configuration.

## Audio and format

- 1080×1920, 9:16, square pixels, 25 fps unless source contract differs;
- audio/video streams present and duration delta within tolerance;
- integrated loudness normally -15 to -13 LUFS and true peak no higher than -1 dBTP;
- do not accept a true peak that merely rounds to -1.00 dBTP; repair with an
  audio-only pass and retain clear codec headroom;
- narration and source dialogue have comparable perceived loudness;
- no clipped first/last syllable.

## Batch

- each filename includes family and episode range;
- candidate rejection and repair history is preserved;
- pairwise core-event overlap below 70% unless explicitly approved;
- all planned deliverables exist or have an explicit non-delivery status such
  as `visual-coverage-pending`, and all delivered per-video QC files pass.
- each delivery includes MP4, matching SRT, per-video QC JSON, caption contract audit, hard-subtitle Pilot audit, and caption-reset contact-sheet evidence.
