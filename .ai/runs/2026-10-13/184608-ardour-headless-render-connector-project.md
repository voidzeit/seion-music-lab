# Run — Ardour headless render connector + Project 001

Timestamp: 2026-10-13T18:46:08.685921+00:00
Outcome: completed

## Summary

Added connectors/ardour (EXPERIMENTAL): seed session built once in Ardour 9 GUI (6 GM tracks), headless ardour9-lua render_job.lua rewrites region notes and exports master + stems; Python seion_ardour (midi_job, runner, validation, cli). Windows findings: ardour9-lua crashes creating tracks, cannot import MIDI headless, needs ARDOUR_* env vars; renders are not bit-exact (~-38 dB run-to-run). Imported Project 001 (cumbia-de-los-monjes-rave v001, 156 BPM, 160 bars); rendered Drop 1 bars 65-96: master + 6 stems all PASS (non-silent, 51.2 s). Reference MP3 in received/ (git-ignored): 89.1 BPM, F# major (low confidence). User declares full rights except commercial distribution. Ardour workspace: D:\Documents\Music-Ardour.

## Validation

60 pytest passed; ruff passed; drop_1 render_report passed

## Changed files

- `.gitignore`
- `pyproject.toml`
- `connectors/ardour`
- `projects/cumbia-de-los-monjes-rave`

## Decision

Ardour is the automated render backend via a GUI-built seed session plus headless note rewriting; never create tracks or import MIDI headless on Windows.
