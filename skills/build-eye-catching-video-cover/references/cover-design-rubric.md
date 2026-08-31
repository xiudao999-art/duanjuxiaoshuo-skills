# Cover design rubric

## Candidate scoring

Score each category from 0–3. Prefer candidates totaling at least 13/18.

| Category | 0 | 1 | 2 | 3 |
| --- | --- | --- | --- | --- |
| Topic recognition | unclear | generic scene | topic implied | topic instantly obvious |
| Curiosity or tension | none | mild | clear hook | strong conflict/reveal |
| Subject clarity | obstructed/blurred | weak | usable | face/object immediately readable |
| Thumbnail readability | collapses small | cluttered | acceptable | strong silhouette and contrast |
| Negative space | none | awkward | usable | natural title area |
| Edit safety | transition/blink | risky | manageable | stable clean frame |

Useful candidate archetypes:

1. Named person + recognizable brand/logo.
2. Comparison, confrontation, or visible `VS` structure.
3. Iconic visual that identifies the topic without text.
4. Strong number, investment, ranking, or policy milestone.
5. Clean portrait/object frame suitable for custom typography.

## Copy hierarchy

Main title:

- Prefer 4–8 Chinese characters for a recurring column or topic.
- Use a single strong reading block.
- Avoid punctuation unless it is part of the required brand phrase.

Subtitle:

- Prefer 10–24 Chinese/ASCII characters.
- Use one closed claim, not a keyword pile.
- Prefer `person/company + action + technology/result`.
- Remove filler words such as “最新消息是”“我们来看看”.
- Preserve protected names and casing.

Example pattern:

```text
Main title: 脑机全球快报
Subtitle: Sam Altman布局超声波脑机接口
```

## Production edit prompt

Adapt this template without adding unsupported facts:

```text
Use case: ads-marketing
Asset type: vertical 9:16 video cover
Primary request: Turn the supplied clean video frame into a polished, high-click cover while preserving the source identity.
Input image: edit target.
Preserve exactly: <people/faces/hands/products/logos/background elements>.
Composition: Keep the original portrait composition. Place typography only in <negative-space location> with strong safe margins. Do not cover <faces/gesture/logo>.
Text, verbatim:
Main title: “<exact main title>”
Subtitle: “<exact subtitle>”
Typography: bold premium headline, high contrast, restrained accent colors matched to the frame, smaller subtitle beneath the main title, readable at thumbnail size.
Style: <news/education/business/entertainment tone> consistent with the source image.
Constraints: exactly two text blocks; copy text verbatim; no old subtitles; no translation line; no extra labels; no added logos; no watermark; preserve the original subjects and existing logos.
```

## Layout guidance

- Keep important text inside the inner 8% horizontal safe area.
- Use negative space before adding a dark title plate.
- Let the title occupy roughly 15–25% of total frame height.
- Keep the subtitle visually subordinate but readable at phone-thumbnail scale.
- Use one accent color sampled from the source. Avoid rainbow palettes.
- Keep faces larger than decorative UI elements when a recognizable person drives the click.

## QC checklist

- [ ] Selected frame came from the intended video moment.
- [ ] Clean frame has no burned captions.
- [ ] Main title is exact.
- [ ] Subtitle is exact and transcript-supported.
- [ ] No accidental extra text or fake logo.
- [ ] Faces, hands, and existing logos remain credible.
- [ ] Text avoids faces, gestures, and logos.
- [ ] Cover remains legible at approximately 270×480 preview size.
- [ ] Final dimensions and aspect ratio are correct.
- [ ] Final image is saved in the project, not only in generated-image storage.
