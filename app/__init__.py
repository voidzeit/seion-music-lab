"""SEION Music Lab — local-first AI-assisted electronic music production lab.

The package is organised in clean layers:

- ``app.schemas``      — Pydantic data contracts (MusicalIdea, Track, ...).
- ``app.music``        — deterministic music theory and pattern generators.
- ``app.seion``        — the SEION scoring / reasoning engine.
- ``app.export``       — MIDI / JSON / Markdown writers.
- ``app.agents``       — thin (currently deterministic) agent wrappers.
- ``app.orchestrator`` — wires agents + tools into the generation pipeline.
- ``app.providers``    — optional LLM provider adapters (not needed for the MVP).
- ``app.cli``          — the ``seion-music`` Typer command line interface.

The MVP runs fully offline: no LLM API keys are required to generate music.
"""

__version__ = "0.1.0"
