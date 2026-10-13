# Decisions

## DEC-0001 — `.ai/` is source of truth

Status: accepted  
Date: 2026-07-03

Canonical project memory lives in `.ai/`.

Consequences:

- Context packs are derived.
- Machine indexes are derived.
- Runtime is disposable.
- Obsidian is optional.

## Decision — 2026-10-13T17:42:33.052872+00:00

Keep AMO memory separate from SEION musical memory; integrate through documented adapters and evidence, not by merging stores.

## Decision — 2026-10-13T18:46:08.681253+00:00

Ardour is the automated render backend via a GUI-built seed session plus headless note rewriting; never create tracks or import MIDI headless on Windows.

## Decision — 2026-10-13T19:59:13.715242+00:00

Choose Surge sounds by writing .fxp payloads into the saved VST3 state (kits JSON), not via GUI or MIDI program change; user should not need the Ardour GUI for renders.
