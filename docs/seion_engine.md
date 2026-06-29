# The SEION engine

SEION is a **deterministic** musical reasoning engine. In the MVP it is a scorer
plus a memory; no LLM and no ML. It exists so generation is never random — every
idea is measured against musical principles.

## The score

Six components in `[0, 1]`, combined with fixed weights
(`app/schemas/seion_score.py`):

```
overall = 0.25*coherence + 0.20*style_match + 0.20*emotional_clarity
        + 0.15*tension_curve + 0.10*editability + 0.10*novelty
```

| Component | Rewards | Penalises |
| --- | --- | --- |
| **coherence** | in-scale notes, bass on chord roots, clean voicings, sane density | out-of-scale notes, muddy voicings, overload |
| **style_match** | tempo/mode/harmony/groove/automation matching references | wrong tempo, major key vs dark style, no offbeat bass |
| **emotional_clarity** | harmony+tempo+arp aligned with target emotions | conflicts (e.g. major key vs "melancholic") |
| **tension_curve** | rising automation, intentional energy change | a totally flat loop |
| **editability** | clear role separation, 3-6 tracks, editable density | one giant overloaded track |
| **novelty** | blended references, small variation | a flat copy |

## Realism ceilings

A quantised, un-mixed MVP loop is a *skeleton*. Components apply honest ceilings
(e.g. `style_match` tops at ~0.78) because timbre, mix and full arrangement are
finished in FL Studio. This keeps "perfect" scores from being misleading and
teaches that style = notes **plus** sound.

## Why a single loop scores ~0.76

For the default Computer Data + NTO loop:

| coherence | style | emotion | tension | editability | novelty | overall |
| --- | --- | --- | --- | --- | --- | --- |
| ~0.87 | ~0.73 | ~0.85 | ~0.63 | ~0.90 | ~0.43 | **~0.76** |

`tension_curve` and `novelty` are deliberately moderate — that is the system
telling you the next wins are *arrangement* and *your own edits*.

## Memory (app/seion/memory.py + preference_model.py)

Listening feedback updates a `PreferenceModel` (likes / dislikes / current
direction), persisted as JSON under `data/memory`. Over time this becomes your
personal musical language.

## Style graph (app/seion/graph.py)

A small hypergraph (`data/seed/style_graph.seed.json`) links artists -> traits
-> techniques -> emotions. The MVP uses it for look-ups; later it can drive
richer reasoning and ranking.
