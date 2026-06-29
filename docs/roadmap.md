# Roadmap

## Sprint 1 — deterministic core ✅ (this MVP)

- repo + clean architecture
- `MusicalIdea` and all schemas
- music theory (notes, scales, chords, voicings)
- generators: chords, bass, arp, drums
- MIDI export (per-track + `full_loop.mid`)
- deterministic SEION scorer
- `explanation.md` teacher output
- CLI `seion-music generate`
- tests

## Sprint 2 — feedback & variations

- `seion-music feedback` deepened: preference-weighted generation
- directed variations ("darker, less happy, simpler arp") -> new version
- `compare_versions` surfaced in the CLI
- version graph (loop_001 -> loop_002 with what changed and why)
- SQLite-backed memory (replacing JSON files)

## Sprint 3 — drums & arrangement depth

- richer kits, swing/humanisation options, fills
- real arrangement: intro / build / break / drop / outro
- per-section automation and energy curve
- this is what lifts `tension_curve` above ~0.65

## Sprint 4 — FL Studio Piano Roll

- finalise `.pyscript` import (chords/bass/arp into the Piano Roll)
- drop-folder workflow (`data/fl_drop/latest_*`)
- script installer into the FL user scripts directory
- humanize script

## Sprint 5 — reference analysis

- analyse imported MIDI / described loops ("autopsy" a track)
- targeted "make it more NTO / more Bodzin" suggestions

## Sprint 6 — LLM orchestration

- wire providers (OpenRouter router; OpenAI/Anthropic for reasoning; Ollama local)
- LLM planner + composer using the existing tool registry
- SEION still validates every proposal; deterministic path stays as the floor

## Explicitly out of scope (for now)

- controlling FL via its GUI
- automatic mastering / "sounds professional" claims without audio
- commercial-track remakes
- 100-layer arrangements with no structure
