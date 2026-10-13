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

## Sprint 2 — feedback & variations ✅

- directed variations (`seion-music vary <id> -d "darker, simpler arp"`) -> new
  child version, deterministic (`app/music/variations.py` + `variation_agent`)
- `compare_versions` surfaced in the CLI (`vary` shows a before/after diff;
  `seion-music compare <a> <b>` diffs any two saved versions)
- version graph: every idea records `parent_id` / `version` / `lineage`; `list`
  marks variations with `*`
- SQLite-backed memory + project catalog (`app/storage/sqlite_store.py`), with a
  one-time migration of the old JSON preference/feedback files

## Sprint 3 — drums & arrangement depth ✅

- real arrangement: intro / build / main / break / drop / outro with a rising
  energy curve (`build_song_sections`)
- section-aware drums: hats-only intro, kick-less break, fills at transitions,
  optional swing + deterministic humanisation (default kit is byte-stable)
- per-section filter automation that tracks each section's energy
- `tension_curve` now rewards real section energy variation — a 16-bar loop went
  from ~0.63 to ~0.86, overall ~0.76 -> ~0.80

## Sprint 4 — FL Studio Piano Roll ✅

- robust `.pyscript` import (import all melodic tracks or one role; resolves the
  idea JSON from `SEION_IDEA_PATH` or sensible defaults)
- drop-folder workflow wired into the pipeline (`data/fl_drop/latest_*` refreshed
  on every `generate` / `vary`)
- script installer: `seion-music install-fl [--dest ...]`
- deterministic humanize script

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


## Project 001 recovery (2026-10-13) — actively verified in CI

- Legacy v001 (156 BPM, G minor) is rejected as an artistic direction, retained for history.
- v002 generates three original 16-bar 158-BPM / C# minor MIDI experiments
  (groove / trance_bounce / hardcore_hybrid). These are **unheard prototypes**.
- The original Grupo G stem analysis is **derived evidence**, while the 11
  artist style descriptions remain **hypotheses**, not measured fingerprints.
- A Python Ardour adapter can select a v002 prototype and merge its extra
  percussion into GM drums for the experimental seed; no overwrite of
  prior render/session paths.
- Unit tests and Linux CI cover the core prototype and adapter without
  installing the DAW. A real Windows Ardour/Surge rendering test and human
  audition are mandatory before calling production "ready".
- AMO canonical state and test commands are updated; large regenerated
  machine indexes are excluded from the repository.

Next musical gate: audition three independently sound-designed, rendered
16-bar previews, approve one, then expand to a 32-bar drop. Do not generate
another unreviewed 160-bar song.
