# AMO Context Pack

## Task

SEION Music Lab music generation, Ardour integration, audio analysis roadmap

## Budget

Profile: `quick`
Max tokens: `3000`
Purpose: Default task context for common coding work.

## Agent Operating Rules

- Prefer canonical memory and top-ranked files.
- Treat this context pack as the session entrypoint.
- Prefer expansion paths over asking the user to repeat context.
- Use canonical memory before chat history when facts conflict.
- Keep the working set small; expand only when evidence is missing.

## Authority Order

1. `source_code`
2. `git_history`
3. `canonical_ai_memory`
4. `machine_indexes`
5. `context_packs`
6. `adapter_files`
7. `runtime_notes`
8. `chat_history`

## Degradation Signals

Start a handoff or compact the session when any of these appear:

- The agent repeats previously resolved work.
- The agent asks for project facts already present in memory.
- The agent edits files outside the intended scope.
- The agent loses the test or validation plan.
- The conversation contains more process than task evidence.
- The prompt needs copied summaries from earlier turns.

## Current Truth

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

## Decisions Snapshot

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

## Tests Snapshot

# Tests

## Required commands

No test commands configured yet.

## Notes

Update this file with project-specific validation commands.

## Validation — 2026-10-13T17:42:33.052872+00:00

55 pytest tests passed; ruff check passed; compileall passed; amo validate passed

## Relevant Context Units

| Unit | Type | Tokens | Expand |
|---|---|---:|---|
| seion_music_lab.egg-info/dependency_links.txt | file_summary | 12 | `seion_music_lab.egg-info/dependency_links.txt` |
| seion_music_lab.egg-info/entry_points.txt | file_summary | 12 | `seion_music_lab.egg-info/entry_points.txt` |
| seion_music_lab.egg-info/top_level.txt | file_summary | 12 | `seion_music_lab.egg-info/top_level.txt` |
| app/seion/__init__.py | file_summary | 20 | `app/seion/__init__.py` |
| seion_music_lab.egg-info/requires.txt | file_summary | 84 | `seion_music_lab.egg-info/requires.txt` |
| app/agents/seion_agent.py | file_summary | 56 | `app/agents/seion_agent.py` |
| app/cli/__init__.py | file_summary | 20 | `app/cli/__init__.py` |
| app/seion/nodes.py | file_summary | 56 | `app/seion/nodes.py` |
| app/seion/edges.py | file_summary | 60 | `app/seion/edges.py` |
| app/orchestrator/__init__.py | file_summary | 44 | `app/orchestrator/__init__.py` |
| app/tools/create_fl_piano_roll_script.py | file_summary | 44 | `app/tools/create_fl_piano_roll_script.py` |
| app/tools/export_markdown.py | file_summary | 44 | `app/tools/export_markdown.py` |
| app/tools/generate_drums.py | file_summary | 44 | `app/tools/generate_drums.py` |
| app/tools/log_feedback.py | file_summary | 44 | `app/tools/log_feedback.py` |
| app/music/__init__.py | file_summary | 136 | `app/music/__init__.py` |
| app/music/rhythm.py | file_summary | 120 | `app/music/rhythm.py` |
| app/seion/novelty.py | file_summary | 132 | `app/seion/novelty.py` |
| app/schemas/seion_score.py | file_summary | 144 | `app/schemas/seion_score.py` |
| app/seion/preference_model.py | file_summary | 144 | `app/seion/preference_model.py` |
| app/tools/generate_arrangement.py | file_summary | 56 | `app/tools/generate_arrangement.py` |
| app/tools/score_idea.py | file_summary | 56 | `app/tools/score_idea.py` |
| app/storage/db.py | file_summary | 60 | `app/storage/db.py` |
| app/tools/generate_arp.py | file_summary | 60 | `app/tools/generate_arp.py` |
| app/tools/generate_bassline.py | file_summary | 60 | `app/tools/generate_bassline.py` |
| app/tools/generate_chords.py | file_summary | 60 | `app/tools/generate_chords.py` |

## Graph Neighborhood

Selection was seeded from these task-relevant files:

- `seion_music_lab.egg-info/SOURCES.txt`
- `seion_music_lab.egg-info/dependency_links.txt`
- `seion_music_lab.egg-info/entry_points.txt`
- `seion_music_lab.egg-info/requires.txt`
- `seion_music_lab.egg-info/top_level.txt`
- `app/cli/seion_music.py`
- `app/music/analysis.py`
- `app/agents/seion_agent.py`
- `app/music/__init__.py`
- `app/music/arpeggios.py`

Structurally near files (expansion candidates, by graph proximity):

- `app/__init__.py` (proximity 0.56)
- `app/agents/arranger_agent.py` (proximity 0.56)
- `app/agents/composer_agent.py` (proximity 0.56)
- `app/agents/critic_agent.py` (proximity 0.56)
- `app/agents/intake_agent.py` (proximity 0.56)
- `app/agents/reference_agent.py` (proximity 0.56)
- `app/agents/sound_design_agent.py` (proximity 0.56)
- `app/agents/teacher_agent.py` (proximity 0.56)

## Expansion Map

Open referenced files only when deeper context is needed. Do not load the entire repository by default.

## Session Handoff Rule

Before the chat becomes long or noisy, run:

```bash
amo handoff --task 'SEION Music Lab music generation, Ardour integration, audio analysis roadmap' --summary "<current state and next step>"
```

## Postflight

After completing the task, run:

```bash
amo postflight --task 'SEION Music Lab music generation, Ardour integration, audio analysis roadmap' --summary "<what changed>"
amo validate
```
