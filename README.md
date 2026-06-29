# SEION Music Lab

**A local-first, AI-assisted electronic music production lab for FL Studio.**

SEION Music Lab turns a musical *intention* into **editable, explained** material
for FL Studio:

```
prompt -> plan -> MusicalIdea (JSON) -> MIDI -> SEION score -> explanation -> feedback -> next version
```

It is **not** a "make me a track" button. It is an analyst + assistant composer +
pattern designer + critic + style archivist that helps you:

- understand the decisions producers make,
- copy structures to learn from them,
- finish ideas,
- train your ear,
- and slowly build your own musical language.

The first version (this MVP) runs **fully offline** with **deterministic** music
generation — **no LLM API keys required**. LLM providers (OpenAI, Anthropic,
OpenRouter, Ollama) are wired as optional layers for later.

References this lab is tuned for: **Computer Data / Healing, DJ Heartstring,
Floating Points, Fred again.., NTO, Stephan Bodzin.**

---

## What it generates

Running one command creates a project folder with:

| File | What it is |
| --- | --- |
| `idea.json` | The full `MusicalIdea` — the single source of truth. |
| `seion_score.json` | The deterministic SEION evaluation. |
| `explanation.md` | A teacher's write-up: every decision, the score, FL import steps. |
| `chords.mid` | Warm seventh-chord harmony (one chord/bar). |
| `bass.mid` | Offbeat root bass. |
| `arp.mid` | Hypnotic chord-tone arpeggio. |
| `drums.mid` | Four-on-the-floor kit. |
| `full_loop.mid` | All tracks combined (type-1 MIDI, tempo embedded). |

---

## Install

Requires **Python 3.11+**.

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .
```

For development (tests + linters):

```powershell
pip install -e ".[dev]"
```

Optional extras: `.[server]` (FastAPI API), `.[llm]` (httpx for providers),
`.[audio]` (pretty_midi / numpy).

Copy `.env.example` to `.env` if you want to set paths or (later) API keys.
**Never commit real keys.** The MVP needs none.

---

## Generate your first loop

```powershell
seion-music generate --style "Computer Data,NTO" --key "A minor" --bpm 124 --bars 16 --emotion "warm,melancholic,hypnotic"
```

Output lands in:

```
data/projects/<project_id>/
├─ idea.json
├─ seion_score.json
├─ explanation.md
├─ chords.mid
├─ bass.mid
├─ arp.mid
├─ drums.mid
└─ full_loop.mid
```

Other commands:

```powershell
seion-music list                       # list saved projects (variations marked *)
seion-music feedback <project_id> --rating 7 --comment "darker, less happy" --liked "bass" --disliked "arp too busy"

# Sprint 2 — directed variations + score diff
seion-music vary <project_id> --direction "darker, simpler arp, more drive"
seion-music compare <project_id> <variation_id>

# Sprint 4 — install the FL Studio Piano Roll scripts
seion-music install-fl                  # or --dest "<FL>/Settings/Piano roll scripts"

seion-music version
```

---

## Import into FL Studio

1. Set the FL project tempo to the BPM shown.
2. Drag `chords.mid`, `bass.mid`, `arp.mid`, `drums.mid` onto their own tracks
   (or `full_loop.mid` to audition everything at once).
3. Assign instruments — see the suggestions in `explanation.md`
   (warm pad, mono synth bass, analog pluck, clean house kit).
4. Route the drum MIDI to a kit; it uses the General MIDI map
   (kick 36, clap 39, closed hat 42, open hat 46).

Full details, plus the Piano Roll scripting roadmap, are in
[`docs/fl_integration.md`](docs/fl_integration.md).

---

## How it works

```
UserRequest
  -> Intake Agent        (normalise the request)
  -> Reference Agent     (artists -> actionable traits)
  -> Composer Agent      (deterministic music generators)
  -> SEION scorer        (coherence, style, emotion, tension, editability, novelty)
  -> Critic Agent        (concrete next changes)
  -> Export              (MIDI / JSON / Markdown)
  -> Versioned project memory
```

The SEION score is a weighted blend:

```
overall = 0.25*coherence + 0.20*style_match + 0.20*emotional_clarity
        + 0.15*tension_curve + 0.10*editability + 0.10*novelty
```

See [`docs/architecture.md`](docs/architecture.md),
[`docs/seion_engine.md`](docs/seion_engine.md) and
[`docs/musical_idea_schema.md`](docs/musical_idea_schema.md).

---

## Tests

```powershell
pytest -q
```

Covers note/scale/chord theory, MIDI export, SEION scoring and an end-to-end
generation smoke test.

---

## Project layout

```
app/
  schemas/      Pydantic contracts (MusicalIdea, Track, NoteEvent, ...)
  music/        deterministic theory + pattern generators
  seion/        the SEION scoring/memory engine
  agents/       thin deterministic agents (LLM-ready interfaces)
  orchestrator/ the generation pipeline + state machine + tool registry
  tools/        orchestratable units (also the future LLM tool surface)
  export/       MIDI / JSON / Markdown writers
  providers/    optional LLM adapters (OpenAI/Anthropic/OpenRouter/Ollama)
  fl_bridge/    FL Studio drop folder + Piano Roll script install
  storage/      JSON-backed project store (SQLite later)
  cli/          the `seion-music` CLI
prompts/        system + style + task prompts (for the LLM phase)
data/           projects, seed graphs, memory, logs
fl_scripts/     FL Studio Piano Roll + MIDI controller scripts
docs/           architecture, schema, SEION engine, FL integration, roadmap
tests/          pytest suite + fixtures
```

---

## Status & roadmap

This is **Sprint 1**: deterministic generation, scoring, explanation, export.
Next up: feedback-driven variations, drums/arrangement depth, then Piano Roll
scripting. See [`docs/roadmap.md`](docs/roadmap.md).

License: MIT.
