'''FL Studio Piano Roll script template (text only).

This string is written out as a ``.pyscript`` file that FL Studio runs inside
the Piano Roll. It reads a local JSON idea exported by SEION and inserts the
notes of one track. It is intentionally simple and defensive — FL's scripting
API (the ``flpianoroll`` module) exposes ``score``, ``Note`` and ``score.PPQ``.

Reference: Image-Line FL Studio Piano Roll scripting API.
'''

from __future__ import annotations

IMPORT_IDEA_SCRIPT = r'''# SEION Import Idea.pyscript
# Reads data/fl_drop/latest_idea.json and inserts a track's notes into the
# current Piano Roll. Choose which track via TRACK_ROLE below.
#
# This script runs INSIDE FL Studio (Piano Roll > Scripting). It does not call
# the network; SEION writes the JSON, FL just consumes it.

import json
import os

import flpianoroll as flp

# Which track role to import: "harmony", "bass", "arp", "melody".
TRACK_ROLE = "harmony"

# Adjust this path to your SEION checkout if needed.
IDEA_PATH = os.path.expanduser(r"~/seion-music-lab/data/fl_drop/latest_idea.json")


def _beats_to_ticks(beats):
    return int(round(beats * flp.score.PPQ))


def import_notes():
    if not os.path.exists(IDEA_PATH):
        return
    with open(IDEA_PATH, "r", encoding="utf-8") as fh:
        idea = json.load(fh)

    track = None
    for candidate in idea.get("tracks", []):
        if candidate.get("role") == TRACK_ROLE:
            track = candidate
            break
    if track is None:
        return

    for ev in track.get("notes", []):
        note = flp.Note()
        note.number = int(ev["midi"])
        note.time = _beats_to_ticks(ev["start_beat"])
        note.length = _beats_to_ticks(ev["duration_beats"])
        note.velocity = float(ev["velocity"]) / 127.0
        flp.score.addNote(note)


import_notes()
'''
