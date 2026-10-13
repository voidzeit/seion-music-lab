# State

## Project Identity

Unknown generic project.

## Current Truth

- AMO memory is initialized.
- Canonical memory lives in `.ai/`.

## Implemented

- Memory scaffold.

## In Progress

- Project-specific scan.

## Risks

- Project memory needs review.
## Postflight — 2026-10-13T17:42:33.052872+00:00

Task: Analyze SEION Music Lab and Ardour integration

Summary: Reviewed the synchronized SEION repository and its existing deterministic MIDI pipeline. Confirmed 55 tests pass in .venv, ruff and compileall pass, AMO scan and graph build pass. Current product is an explainable local-first MIDI composition assistant for FL Studio with SQLite preference/project memory; it has no waveform synthesis, audio analysis, stems, voice, or Ardour adapter yet. Ardour should begin as a file-based MIDI/audio handoff with an optional Lua EditorAction layer. AMO remains coding-project memory; SEION remains musical memory.

Outcome: completed
Changed files: .ai, .amo.yaml, AGENTS.md, .gitignore
## Postflight — 2026-10-13T18:46:08.681253+00:00

Task: Ardour headless render connector + Project 001

Summary: Added connectors/ardour (EXPERIMENTAL): seed session built once in Ardour 9 GUI (6 GM tracks), headless ardour9-lua render_job.lua rewrites region notes and exports master + stems; Python seion_ardour (midi_job, runner, validation, cli). Windows findings: ardour9-lua crashes creating tracks, cannot import MIDI headless, needs ARDOUR_* env vars; renders are not bit-exact (~-38 dB run-to-run). Imported Project 001 (cumbia-de-los-monjes-rave v001, 156 BPM, 160 bars); rendered Drop 1 bars 65-96: master + 6 stems all PASS (non-silent, 51.2 s). Reference MP3 in received/ (git-ignored): 89.1 BPM, F# major (low confidence). User declares full rights except commercial distribution. Ardour workspace: D:\Documents\Music-Ardour.

Outcome: completed
Changed files: .gitignore, pyproject.toml, connectors/ardour, projects/cumbia-de-los-monjes-rave
## Postflight — 2026-10-13T19:59:13.715242+00:00

Task: Surge XT sound kits for Ardour headless renders + reference fingerprint

Summary: Installed torch 2.11 cu128 + demucs 4.1 in .venv; app/audio/separation.py and reference_fingerprint.py measured the original: 89.1 BPM, C# minor, loop C#m-B-B-F#/G#m, vocal recites on B, intro chant bars 1-7 without drums. Project target now 158 BPM / C# minor (v001 still 156 / G minor). Surge XT installed (VST3, C:). Seed v2 built headlessly (latin_perc track -> kick, Surge XT on kick/bass/chords/arp/lead); kits/hard_rave_v1.json selects .fxp patches written into VST3 state by surge_state.py. Render guards: 1-bar preroll, master 25 Hz HPF (DC), per-stem activity check, accept teardown crash only after 'done'. drop_1_surge: -14.7 LUFS, 0 clipped samples, all stems active.

Outcome: completed
Changed files: app/audio, connectors/ardour, projects/cumbia-de-los-monjes-rave, pyproject.toml
