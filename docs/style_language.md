# Style language

How SEION turns artist names into music it can actually generate and score.

## From reference to traits

`app/agents/reference_agent.py` holds a registry mapping each reference to
**MIDI-achievable** traits (tempo range, mode, harmony type, groove, automation)
plus sound/arrangement notes. `build_style_context` merges multiple references
into one context the composer and scorer share. Full prose profiles live in
`prompts/styles/`.

| Reference | BPM | Signature moves SEION uses |
| --- | --- | --- |
| Computer Data / Healing | 118-126 | warm maj7/min7, round bass, clean kit, subtle swing |
| DJ Heartstring | 140-150 | supersaw chords, offbeat bass, big breaks |
| Floating Points | 118-128 | jazzy/extended harmony, organic texture, space |
| Fred again.. | 128-150 | vocal-chop intimacy, warm chords, garage swing |
| NTO | 122-126 | short repeating arp, slow filter open, wide reverb |
| Stephan Bodzin | 122-128 | detuned analog lead motif, driving bass, cinematic builds |

## Combining references

When several are selected, SEION merges the BPM range (min low, max high) and
OR-combines boolean traits (any reference wanting offbeat bass turns it on). It
flags contradictions (e.g. 124 BPM warm house mixed with 145 BPM trance) so you
choose clarity over a muddle.

## Building your own language

The point is not to clone these artists — it is to learn their *decisions* and
then drift. Feedback (`seion-music feedback`) updates your `PreferenceModel`
(likes/dislikes/direction), which over time becomes a personal style that sits
alongside the reference registry.

## What MIDI can and cannot carry

- **Carries:** tempo, key/mode, chord type, voicing register, groove placement,
  density, automation shape.
- **Does not carry:** timbre, mix, reverb space, sidechain feel — these are the
  ~20-30% you finish in FL Studio, and why `style_match` is honestly capped.
