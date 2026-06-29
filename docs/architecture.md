# Architecture

SEION Music Lab is **local-first** and **deterministic-by-default**. The MVP
generates music with pure Python; LLMs are an optional layer added later without
restructuring.

## Layers

```
CLI / API
   │
Orchestrator (app/orchestrator)        pipeline + state machine + guardrails
   │
Agents (app/agents)                    intake, reference, composer, arranger,
   │                                    sound_design, critic, seion, teacher
Deterministic tools (app/tools)        thin, typed, LLM-callable units
   │
Music theory + generators (app/music)  notes, scales, chords, voicings, bass,
   │                                    arp, drums, arrangement, automation
SEION engine (app/seion)               scorer, style_match, tension, novelty,
   │                                    graph, memory, preference_model
Export (app/export)                    MIDI / JSON / Markdown writers
   │
Storage (app/storage)                  JSON-backed project store
   │
FL Studio                              imports .mid / reads JSON via .pyscript
```

## Key principle

**The LLM decides; SEION validates; FL Studio is the body.**

The DAW is a *consumer of results*, never an agent host. SEION writes files; FL
reads them. This keeps the system stable, debuggable and offline-capable.

## The pipeline (app/orchestrator/run.py)

```
parse -> load style context -> plan -> compose -> validate ->
SEION score -> critique -> (revise) -> export -> save version -> explain
```

Each step is a discrete `GenerationState` (see `state_machine.py`) so the flow
is inspectable and testable.

## Data flow

Everything is funnelled through one contract — the **`MusicalIdea`** Pydantic
model (`app/schemas/musical_idea.py`). MIDI, JSON and Markdown are all derived
from it. See [`musical_idea_schema.md`](musical_idea_schema.md).

## Why deterministic first

- It works with zero API keys and zero cost.
- It is unit-testable and reproducible.
- It gives the future LLM layer a ground truth to compare against.
- Every output is explainable by construction (the decision log).
