# Ardour connector (EXPERIMENTAL)

Renders a SEION version (per-role `.mid` files + `idea.json`) to WAV master and
stems through Ardour 9 **without the GUI**. SEION never links Ardour code
(GPL-2): everything crosses a file/process boundary.

```
idea.json + midi/*.mid ──> job.lua ──> ardour9-lua render_job.lua ──> master.wav + stem_*.wav
                                         (copy of the seed session)      └─> render_report.json
```

## Usage

```bash
set PYTHONPATH=connectors\ardour\python
.venv\Scripts\python.exe -m seion_ardour.cli projects\<slug>\versions\v001 --bars 65-96 --name drop_1
```

- WAVs + `render_report.json` → `<version>/renders/<name>/` (git-ignored).
- The Ardour session used for the render → `D:\Documents\Music-Ardour\<slug>\<version>_<name>`
  (override with `SEION_ARDOUR_WORKSPACE`), so it can be opened in the GUI.
- Ardour install: `D:\Program Files\Ardour9` (override with `SEION_ARDOUR_HOME`).

## What we verified on Windows (Ardour 9, 2026-10-13)

| Capability (headless `ardour9-lua.exe`) | Status |
|---|---|
| Load session, set tempo, edit MIDI region notes, mute, export WAV | works |
| Create tracks (`new_audio_track` / `new_midi_track`) | **crashes** (access violation in `ardour-3.dll`) |
| Import `.mid` | not possible (`Editor:do_import` is GUI-only) |
| Run without `ARDOUR_DATA_PATH`/`ARDOUR_CONFIG_PATH`/`ARDOUR_DLL_PATH` | fails; `runner.py` sets them |
| Bit-exact renders | **no**: same job twice differs ~-38 dB (General MIDI Synth); master vs sum of stems ~-29 dB. Loudness/peak stable to ~0.01 dB |

Hence the **seed session** (`templates/seion_seed`): built once in the GUI with
`lua/build_seed_session.lua`, it holds one MIDI track + one long MIDI region per
role (`drums`, `latin_perc`, `bass`, `chords`, `arp`, `lead`) with General MIDI
Synth. Each render copies it, replaces every region's notes, shrinks regions to
the song length and exports. Track names are `<role>-1-t1`; `render_job.lua`
maps them back to roles. The GM program per track comes from the seed files
(`python/seion_ardour/seed.py`), not from the project MIDI.

## Seed v2 + kits (Surge XT, no GUI)

`templates/seion_seed_v2` was derived from seed v1 **headlessly** with
`lua/configure_seed_v2.lua`: the `latin_perc` track became `kick`, and kick,
bass, chords, arp and lead got Surge XT (headless *can* swap processors; it
just cannot create tracks). Its `seion_seed.json` merges `latin_perc` notes into
`drums` and splits notes 35/36 out of `drums` into `kick`.

Sounds come from a **kit** (`kits/*.json`): Surge `.fxp` paths per role plus
`gains_db` / `master_gain_db`. `surge_state.py` writes each `.fxp` payload into
the copied session's VST3 state blob before rendering, so changing sounds is a
JSON edit (`--kit other.json`). Findings:

- Surge factory patches are not exposed as VST3 presets, and MIDI program
  changes sent from headless Lua did not reach Surge; the state blob works.
- Some patches misbehave headless (3rd-party "Trance Pluck": DC offset and only
  a start-up burst). Hence: 1 bar of pre-roll that is not exported, a 25 Hz
  high-pass on the master (DC blocker), and an **activity check**: a stem fails
  if it sounds in < 50 % of the windows where its MIDI has notes.
- With Surge plugins loaded, ardour9-lua may crash *after* `close_session`; the
  runner accepts that only when `render.log` ends in `done`.

```bash
.venv\Scripts\python.exe -m seion_ardour.cli projects\<slug>\versions\v001 --bars 65-96 --name drop_1_surge --seed seion_seed_v2
```

## Known limits

- GM sounds are a sketch for groove/arrangement, not production timbres.
- Program changes in project MIDI are ignored (seed decides the patch).
- Tempo changes / time-signature changes inside a song are not supported yet.
- The seed also contains an unused `MIDI 1` track from the first GUI attempt; it
  is silenced (no notes) on every render.


## Portable Surge XT presets and Project 001 v002

The former hard_rave_v1 kit was a *placeholder*, not an approved sound.
Its patch URIs now use the format
surge://patches_factory/Plucks/FM Pluck.fxp rather than absolute C: paths.
Set SEION_SURGE_ROOT to your real Surge XT data folder, such as:

    $env:SEION_SURGE_ROOT = "C:\ProgramData\Surge XT"

The connector does not download or create factory presets. If a requested
FXP is missing or outside the configured data folder, rendering fails closed.

For the independent v002 prototypes:

    python -m app.music.prototype_lab --out projects/cumbia-de-los-monjes-rave/versions/v002/generated
    $env:PYTHONPATH = "connectors/ardour/python"
    python -m seion_ardour.cli projects/cumbia-de-los-monjes-rave/versions/v002/generated --prototype groove --name groove_take01

Change prototype to trance_bounce or hardcore_hybrid, and specify a new name
for every take. The Ardour 9/SURGE integration is still Windows-experimental.
For listenable previews with NO DAW, use app.audio.preview_synth and the
human review gate; see the repository README.
