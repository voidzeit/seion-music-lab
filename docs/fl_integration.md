# FL Studio integration

The golden rule: **FL Studio consumes files; it never talks to the network or
hosts agents.** SEION writes `.mid` / `.json`; FL reads them. This is the most
stable, debuggable path.

## Phase 1 — manual MIDI import (the MVP, most robust)

After `seion-music generate`, a project folder contains per-track MIDI plus
`full_loop.mid`:

1. Set the FL project tempo to the BPM in `explanation.md`.
2. Drag each `.mid` onto its own track, or `full_loop.mid` to audition.
3. Assign instruments (see the sound-design section of `explanation.md`).
4. The drum MIDI uses the General MIDI map: kick 36, clap 39, closed hat 42,
   open hat 46 — route it to FPC / a sampler.

## Phase 2 — the drop folder

`app/fl_bridge/midi_drop_folder.py` mirrors the latest export into
`data/fl_drop/` with stable names (`latest_idea.json`, `latest_chords.mid`, …)
so FL-side scripts can read fixed paths instead of timestamped folders.

## Phase 3 — Piano Roll scripting (`.pyscript`)

FL Studio runs Python scripts **inside the Piano Roll** to create/modify/delete
notes. SEION ships templates in `fl_scripts/piano_roll/`:

- `SEION Import Idea.pyscript` — read `latest_idea.json`, insert a track's notes.
- `SEION Generate Chords.pyscript` / `SEION Generate Bass.pyscript` — focused
  imports.
- `SEION Humanize.pyscript` — nudge timing/velocity of selected notes.

Install them into FL's scripts folder with:

```python
from app.fl_bridge import install_piano_roll_scripts
install_piano_roll_scripts()   # uses FL_PIANO_ROLL_SCRIPTS_DIR from your .env
```

FL expects these `.pyscript` files in the user *Piano roll scripts* folder.

## Phase 4 — MIDI controller scripting (later)

`fl_scripts/midi_controller/device_SEION_Controller.py` sketches transport/knob
control (generate a variation, accept, "make it darker", energy/density/swing
knobs). This comes last — FL MIDI scripting targets controllers and events, not
full composition.

## What we deliberately avoid

- **ReWire** — discontinued; not a modern integration path.
- Driving the FL GUI by automation.
- Letting any in-FL script call an LLM directly.
