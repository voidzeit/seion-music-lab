"""A registry of orchestratable tools with JSON schemas.

This is the function-calling surface for a future LLM orchestrator (OpenAI /
Anthropic / OpenRouter all accept this shape). Today the deterministic pipeline
calls the same callables directly. Listing them here means the LLM path and the
deterministic path share one source of truth.
"""

from __future__ import annotations

from collections.abc import Callable

from app import tools


def _schema(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


# name -> (json schema, python callable)
TOOL_REGISTRY: dict[str, tuple[dict, Callable]] = {
    "generate_chord_progression": (
        _schema(
            "generate_chord_progression",
            "Generate a harmony track from a chord progression.",
            {
                "progression": {"type": "array", "items": {"type": "string"}},
                "bars": {"type": "integer"},
            },
            ["bars"],
        ),
        tools.generate_chord_progression,
    ),
    "generate_bassline": (
        _schema(
            "generate_bassline",
            "Generate an offbeat root bassline that follows a progression.",
            {
                "progression": {"type": "array", "items": {"type": "string"}},
                "bars": {"type": "integer"},
            },
            ["bars"],
        ),
        tools.generate_bassline,
    ),
    "generate_arpeggio": (
        _schema(
            "generate_arpeggio",
            "Generate a hypnotic chord-tone arpeggio track.",
            {
                "progression": {"type": "array", "items": {"type": "string"}},
                "bars": {"type": "integer"},
            },
            ["bars"],
        ),
        tools.generate_arpeggio,
    ),
    "generate_drum_pattern": (
        _schema(
            "generate_drum_pattern",
            "Generate a four-on-the-floor drum track.",
            {"bars": {"type": "integer"}},
            ["bars"],
        ),
        tools.generate_drum_pattern,
    ),
    "generate_arrangement": (
        _schema(
            "generate_arrangement",
            "Generate arrangement sections (MVP: one loop section).",
            {"bars": {"type": "integer"}},
            ["bars"],
        ),
        tools.generate_arrangement,
    ),
    "score_seion_idea": (
        _schema(
            "score_seion_idea",
            "Score a musical idea with the deterministic SEION engine.",
            {"idea": {"type": "object"}, "request": {"type": "object"}},
            ["idea", "request"],
        ),
        tools.score_seion_idea,
    ),
    "export_midi": (
        _schema(
            "export_midi",
            "Export a musical idea to per-track + combined MIDI files.",
            {"idea": {"type": "object"}, "project_dir": {"type": "string"}},
            ["idea", "project_dir"],
        ),
        tools.export_idea_midi,
    ),
    "save_project_version": (
        _schema(
            "save_project_version",
            "Persist idea.json and seion_score.json for a project.",
            {"idea": {"type": "object"}},
            ["idea"],
        ),
        tools.save_project,
    ),
    "compare_versions": (
        _schema(
            "compare_versions",
            "Compare two SEION scores and return per-component deltas.",
            {"before": {"type": "object"}, "after": {"type": "object"}},
            ["before", "after"],
        ),
        tools.compare_versions,
    ),
    "log_user_feedback": (
        _schema(
            "log_user_feedback",
            "Store listening feedback and update preference weights.",
            {"feedback": {"type": "object"}},
            ["feedback"],
        ),
        tools.log_user_feedback,
    ),
    "create_fl_piano_roll_script": (
        _schema(
            "create_fl_piano_roll_script",
            "Write the FL Studio Piano Roll import script to a path.",
            {"path": {"type": "string"}},
            ["path"],
        ),
        tools.create_fl_piano_roll_script,
    ),
}


def tool_schemas() -> list[dict]:
    """Return just the JSON schemas (what you'd pass to an LLM as `tools`)."""
    return [schema for schema, _ in TOOL_REGISTRY.values()]


def get_tool(name: str) -> Callable:
    if name not in TOOL_REGISTRY:
        raise KeyError(f"Unknown tool: {name}")
    return TOOL_REGISTRY[name][1]
