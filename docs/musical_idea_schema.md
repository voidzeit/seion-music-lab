# MusicalIdea schema

`MusicalIdea` (`app/schemas/musical_idea.py`) is the single source of truth.
Timing is in **beats** (quarter notes), tempo-independent; the MIDI writer
converts to ticks at PPQ 480.

## Top level

| Field | Type | Notes |
| --- | --- | --- |
| `id` | str | project id, e.g. `idea_20260628_143000_warm_hypnotic` |
| `title` | str | human title |
| `created_at` | datetime | UTC, ISO on export |
| `bpm` | int | 40-300 |
| `key` | str | e.g. `"A minor"` |
| `time_signature` | str | e.g. `"4/4"` |
| `bars` | int | loop length |
| `style_targets` | list[str] | artist references |
| `emotional_targets` | list[str] | e.g. warm/melancholic/hypnotic |
| `energy_target` | `{start, end}` | 0-1 |
| `sections` | list[Section] | MVP: one loop section |
| `tracks` | list[Track] | the editable layers |
| `automation` | list[AutomationEvent] | e.g. filter opening |
| `seion_scores` | SeionScore \| null | the evaluation |
| `decision_log` | list[DecisionLogEntry] | explainability |
| `export_paths` | dict | where files were written |
| `user_feedback` | list[Feedback] | listening feedback |

## Track

```json
{
  "id": "track_chords",
  "name": "warm_seventh_chords",
  "role": "harmony",
  "instrument_hint": "warm FLEX pad or electric piano",
  "mixer_hint": { "volume_db": -10, "pan": 0, "effects": ["reverb_medium"] },
  "notes": [ { "pitch": "A3", "midi": 57, "start_beat": 0, "duration_beats": 4, "velocity": 82 } ],
  "drum_events": [],
  "is_drum": false
}
```

A track holds **either** `notes` (melodic) **or** `drum_events` (percussion).
Valid roles: `kick, snare_clap, closed_hat, open_hat, percussion, drums, bass,
harmony, pad, arp, lead, melody, vocal_chop, texture, fx, automation`.

## NoteEvent / DrumEvent

`NoteEvent`: `pitch, midi (0-127), start_beat, duration_beats, velocity (1-127)`.
`DrumEvent`: `instrument, midi (GM percussion), start_beat, duration_beats,
velocity`.

## Conventions

- MIDI 60 = C4 (middle C); A3 = 57; A4 = 69 = 440 Hz.
- Drums export on MIDI channel 10 (0-indexed 9) using the GM percussion map.
