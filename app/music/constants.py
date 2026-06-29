"""Shared musical constants."""

from __future__ import annotations

# MIDI export resolution (ticks per quarter note).
PPQ = 480

# Musical defaults for SEION Music Lab.
DEFAULT_BPM = 124
DEFAULT_KEY = "A minor"
DEFAULT_BARS = 16
DEFAULT_TIME_SIGNATURE = "4/4"
BEATS_PER_BAR = 4
DEFAULT_PROGRESSION = ["Am7", "Fmaj7", "Cmaj7", "G6"]

# Pitch-class names (sharp spelling) indexed 0-11.
NOTE_NAMES_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Letter -> base pitch class.
LETTER_PITCH_CLASS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

# General MIDI percussion map (channel 10). Keys are SEION drum roles.
GM_DRUMS = {
    "kick": 36,
    "rim": 37,
    "snare": 38,
    "clap": 39,
    "closed_hat": 42,
    "pedal_hat": 44,
    "open_hat": 46,
    "low_tom": 45,
    "crash": 49,
    "ride": 51,
    "shaker": 70,
    "perc": 75,
}

# Suggested General MIDI programs per track role (for full_loop.mid playback).
# These are only hints so the combined MIDI is auditionable before you swap in
# real FL Studio instruments.
GM_PROGRAMS = {
    "harmony": 4,   # Electric Piano 1 (warm)
    "pad": 89,      # Pad 2 (warm)
    "bass": 38,     # Synth Bass 1
    "arp": 81,      # Lead 2 (sawtooth) — stands in for an analog pluck
    "lead": 81,
    "melody": 82,
}
