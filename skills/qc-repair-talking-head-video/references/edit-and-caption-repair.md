# Edit and caption repair

## EDL rules

- Express decisions in source time, never only in the old output timeline.
- Snap video boundaries to frames and audio boundaries to verified word edges.
- Pad edges by 30–200 ms according to speech pace and ASR drift.
- Apply about 30 ms audio fades to both sides of every extracted segment.
- Preserve enough room after a conclusion for natural cadence, but do not add an empty branded tail.

## Repetition repair patterns

- **A, restated A, B:** keep the clearer A and B.
- **Definition, repeated definition, mechanism:** keep one definition and the mechanism.
- **False start, clean restart:** remove the false start.
- **Long-form logistics, core claim:** remove logistics when producing a standalone short.
- **List item, stage direction, next item:** remove the direction and join complete item boundaries.

## Subtitle remapping

For each kept source range `(a, b)` with output offset `o`:

`output_time = source_time - a + o`

Clip or discard old cues by word timestamps, not cue midpoint alone. Cue-midpoint selection can retain words from a removed clause or discard words at a kept edge.

After remapping:

1. Read text around every join.
2. Remove prefix/suffix residue from discarded material.
3. Restore words that were dropped by an overlapping old cue.
4. Rechunk by meaning and protected terms.
5. Rebuild emphasis/CK cue IDs and overlay start times.
6. Run deterministic and manual boundary audits.

## Chinese phrase boundaries

Keep together when practical:

- number + unit: `三年前`, `44家`, `180多名`;
- abbreviations: `LCA`, `AI服务`;
- names and institutions;
- compound nouns: `供应链数据`, `生命周期清单`, `可信数据空间`;
- role names: `数据供给方`, `数据使用方`, `存证方`, `居间服务方`;
- left-bound suffixes such as `的、地、得、了、着、过、们、性、化` with their host phrase.

Do not trust an automatic zero-issue result without inspecting project-specific compounds.

## Pause repair

- Under roughly 400 ms is normally natural.
- 400–800 ms may be rhetorical; listen in context.
- Over roughly 800 ms at a synthetic join deserves review, but waveform energy and speech cadence matter more than the number.
- Ignore a pause when it is not perceptually disruptive, as long as the sentence remains coherent.

