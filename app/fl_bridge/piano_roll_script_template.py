'''FL Studio Piano Roll script templates (text only).

These strings are written out as ``.pyscript`` files that FL Studio runs inside
the Piano Roll. They read a local JSON idea exported by SEION and insert notes.
FL's scripting API (the ``flpianoroll`` module) exposes ``score``, ``Note`` and
``score.PPQ``. Everything here is defensive: missing files/keys never raise.

Reference: Image-Line FL Studio Piano Roll scripting API.
'''

from __future__ import annotations

_IMPORT_TEMPLATE = r'''# {title}
# Runs INSIDE FL Studio (Piano Roll > Scripting). Reads the latest SEION idea
# and inserts notes into the current Piano Roll. FL never touches the network;
# SEION writes the JSON, FL just consumes it.
#
# TRACK_ROLE: "all", "harmony", "bass", "arp" or "melody".
# Override the JSON location with the SEION_IDEA_PATH environment variable.

import json
import os

import flpianoroll as flp

TRACK_ROLE = "{role}"

_CANDIDATES = [
    os.environ.get("SEION_IDEA_PATH", ""),
    os.path.expanduser(r"~/seion-music-lab/data/fl_drop/latest_idea.json"),
    os.path.expanduser(r"~/Documents/seion-music-lab/data/fl_drop/latest_idea.json"),
    os.path.expanduser(
        r"~/Documents/Image-Line/FL Studio/Settings/Piano roll scripts/latest_idea.json"
    ),
]


def _idea_path():
    for path in _CANDIDATES:
        if path and os.path.exists(path):
            return path
    return None


def _ticks(beats):
    return int(round(float(beats) * flp.score.PPQ))


def _add_track_notes(track, color):
    for ev in track.get("notes", []):
        note = flp.Note()
        note.number = int(ev["midi"])
        note.time = _ticks(ev.get("start_beat", 0))
        note.length = max(1, _ticks(ev.get("duration_beats", 0.5)))
        note.velocity = min(1.0, max(0.05, float(ev.get("velocity", 100)) / 127.0))
        try:
            note.color = color  # group/colour notes by source track
        except Exception:
            pass
        flp.score.addNote(note)


def import_notes():
    path = _idea_path()
    if not path:
        return
    with open(path, "r", encoding="utf-8") as fh:
        idea = json.load(fh)

    melodic = [t for t in idea.get("tracks", []) if not t.get("is_drum") and t.get("notes")]
    if TRACK_ROLE != "all":
        melodic = [t for t in melodic if t.get("role") == TRACK_ROLE]

    for color, track in enumerate(melodic):
        _add_track_notes(track, color % 16)


import_notes()
'''


HUMANIZE_SCRIPT = r'''# SEION Humanize.pyscript
# Gently humanise the notes currently in the Piano Roll: small, deterministic
# timing and velocity variation (fixed seed, so a run is reproducible).

import random

import flpianoroll as flp

TIMING_TICKS = 6        # max timing nudge in ticks
VELOCITY_JITTER = 0.06  # fraction of the full velocity range


def run():
    rng = random.Random(2026)
    score = flp.score
    for i in range(score.noteCount):
        note = score.getNote(i)
        note.time = max(0, note.time + rng.randint(-TIMING_TICKS, TIMING_TICKS))
        velocity = note.velocity + rng.uniform(-VELOCITY_JITTER, VELOCITY_JITTER)
        note.velocity = min(1.0, max(0.05, velocity))


run()
'''


def build_import_script(role: str = "all", title: str = "SEION Import Idea.pyscript") -> str:
    """Return an import script that loads the given track role (or 'all')."""
    return _IMPORT_TEMPLATE.format(role=role, title=title)


# The default script imports every melodic track at once.
IMPORT_IDEA_SCRIPT = build_import_script("all")
