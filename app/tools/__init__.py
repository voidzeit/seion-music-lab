"""Orchestratable tools.

Each function here is a small, well-typed unit of work. Today the orchestrator
calls them directly; tomorrow they double as the function-calling surface for an
LLM (see app.orchestrator.tool_registry).
"""

from app.tools.compare_versions import compare_versions
from app.tools.create_fl_piano_roll_script import create_fl_piano_roll_script
from app.tools.export_markdown import write_explanation_file
from app.tools.export_midi import export_idea_midi
from app.tools.generate_arp import generate_arpeggio
from app.tools.generate_arrangement import generate_arrangement
from app.tools.generate_bassline import generate_bassline
from app.tools.generate_chords import generate_chord_progression
from app.tools.generate_drums import generate_drum_pattern
from app.tools.log_feedback import log_user_feedback
from app.tools.save_version import save_project
from app.tools.score_idea import score_seion_idea

__all__ = [
    "compare_versions",
    "create_fl_piano_roll_script",
    "write_explanation_file",
    "export_idea_midi",
    "generate_arpeggio",
    "generate_arrangement",
    "generate_bassline",
    "generate_chord_progression",
    "generate_drum_pattern",
    "log_user_feedback",
    "save_project",
    "score_seion_idea",
]
