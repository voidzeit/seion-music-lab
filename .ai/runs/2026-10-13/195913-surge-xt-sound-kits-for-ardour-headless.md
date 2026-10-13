# Run — Surge XT sound kits for Ardour headless renders + reference fingerprint

Timestamp: 2026-10-13T19:59:13.719649+00:00
Outcome: completed

## Summary

Installed torch 2.11 cu128 + demucs 4.1 in .venv; app/audio/separation.py and reference_fingerprint.py measured the original: 89.1 BPM, C# minor, loop C#m-B-B-F#/G#m, vocal recites on B, intro chant bars 1-7 without drums. Project target now 158 BPM / C# minor (v001 still 156 / G minor). Surge XT installed (VST3, C:). Seed v2 built headlessly (latin_perc track -> kick, Surge XT on kick/bass/chords/arp/lead); kits/hard_rave_v1.json selects .fxp patches written into VST3 state by surge_state.py. Render guards: 1-bar preroll, master 25 Hz HPF (DC), per-stem activity check, accept teardown crash only after 'done'. drop_1_surge: -14.7 LUFS, 0 clipped samples, all stems active.

## Validation

63 pytest passed; ruff passed; drop_1_surge render_report passed

## Changed files

- `app/audio`
- `connectors/ardour`
- `projects/cumbia-de-los-monjes-rave`
- `pyproject.toml`

## Decision

Choose Surge sounds by writing .fxp payloads into the saved VST3 state (kits JSON), not via GUI or MIDI program change; user should not need the Ardour GUI for renders.
