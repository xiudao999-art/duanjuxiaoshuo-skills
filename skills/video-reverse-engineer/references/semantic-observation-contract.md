# Semantic Observation Contract

Use this format when a VLM or human enriches deterministic analysis:

TransNetV2 can be connected independently through analyzer `--transnet-json`; accept a list of seconds, `{boundaries:[...]}`, frame entries with `frame`, or shot entries with `start`.

```json
{
  "video": {"theme":"","audience":"","narrativeType":"","visualGrammar":[],"emotionArc":[]},
  "globalStyle": {"palette":{},"layoutZones":[],"typography":{}},
  "sequences": [{"id":"sequence-001","range":{"start":0,"end":3},"function":"hook","reason":"","confidence":0.8}],
  "shots": {
    "shot-001": {
      "narrativeFunction":"hook","reasonToExist":"","beats":[],"composition":{},"camera":{},"subjects":[],
      "spokenDelivery":{},"visibleExpression":[],"inferredNarrativeEmotion":[],"actions":[],
      "layers":[],"textElements":[],"transitionIn":{},"transitionOut":{},
      "continuityAnchors":[],"reconstruction":{},"confidence":0.7,"evidence":[]
    }
  },
  "conflicts": []
}
```

- Cite exact ranges for every observation.
- Describe visible facial actions before assigning an inferred performance label.
- Use normalized geometry for subjects and text.
- Describe camera motion independently from subject motion.
- Classify boundaries as hard cut, fade, cross dissolve, whip-pan, zoom, occlusion cut, action match, montage, insert, continuous, or custom.
- Put unsupported or contradictory claims in `conflicts`.
- Add an image/video prompt only for an unavoidable media slot, limited to scene, action, lens, lighting, and continuity constraints.
