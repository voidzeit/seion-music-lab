# Testing — factual commands

    python -m pip install -e ".[dev]"
    python -m pytest -q
    ruff check app tests connectors/ardour/python connectors/ardour/tests
    python -m app.music.prototype_lab --out <new-empty-directory>

Ardour is NOT tested by default in CI. The historical AMO record claims 63
tests passed on 2026-10-13; this is previous local testimony, NOT a fresh
check for the current branch. Current tests and lint need their CI run.

A MIDI file can be structurally valid while sounding bad. A WAV can be
non-silent while sounding wrong. Audio sign-off requires listening.
