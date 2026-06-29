"""Deterministic music theory and pattern generation.

Pure, testable, offline. No LLMs, no I/O — these functions turn musical intent
into :class:`~app.schemas.Track` objects and chord/scale data.
"""

from app.music.arpeggios import generate_arp_track
from app.music.arrangement import build_loop_section, build_song_sections
from app.music.automation import filter_open_automation, section_filter_automation
from app.music.bass import generate_bass_track
from app.music.chords import chord_notes, chord_root_midi, parse_chord_symbol
from app.music.drums import generate_drum_track
from app.music.notes import midi_to_note_name, note_name_to_midi
from app.music.scales import is_in_scale, scale_pitch_classes
from app.music.voicings import generate_chord_track, warm_voicing

__all__ = [
    "generate_arp_track",
    "build_loop_section",
    "build_song_sections",
    "filter_open_automation",
    "section_filter_automation",
    "generate_bass_track",
    "chord_notes",
    "chord_root_midi",
    "parse_chord_symbol",
    "generate_drum_track",
    "midi_to_note_name",
    "note_name_to_midi",
    "is_in_scale",
    "scale_pitch_classes",
    "generate_chord_track",
    "warm_voicing",
]
