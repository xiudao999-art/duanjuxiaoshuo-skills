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
- semantic alignment passes with exact-match clip ratio at least 0.50,
  exact-or-context duration ratio at least 0.90, average source clip duration at
  least seven seconds, and zero contradiction, unbound beat, or sub-five-second
  narration clips;
- encoded cut-boundary audit reports zero flash candidates;
- final sentence completes; tail is at least 0.45 seconds and normally no more
  than 6 seconds;

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
- all planned deliverables exist and all per-video QC files pass.
- each delivery includes MP4, matching SRT, per-video QC JSON, caption contract audit, hard-subtitle Pilot audit, and caption-reset contact-sheet evidence.
