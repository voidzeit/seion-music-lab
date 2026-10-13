# Testing — factual commands

    python -m pip install -e ".[dev,preview]"
    python -m pytest -q
    ruff check app tests connectors/ardour/python connectors/ardour/tests
    python -m app.music.prototype_lab --out <new-empty-directory>

Ardour is NOT tested by default in CI. The historical AMO record claims 63
tests passed on 2026-10-13; this is previous local testimony, NOT a fresh
check for the current branch. Current tests and lint need their CI run.

A MIDI file can be structurally valid while sounding bad. A WAV can be
non-silent while sounding wrong. Audio sign-off requires listening.


New current pipeline:
    python -m app.audio.preview_synth --bundle <generated-prototypes> --out <fresh-audio-dir>
    python -m app.audio.audio_analysis --preview-root <fresh-audio-dir> --out <new-json-report>
    seion-music review init <fresh-audio-dir>

The preview engine is an original NumPy synthesizer and is NOT Ardour/Surge.
CI confirms deterministic hashes, WAV integrity, distinct modes, paths and
technical measurements; **human sound selection remains unverified**.


Current GitHub Actions runs in Python 3.12 verify:
- Core/connector and preview unit tests
- CLI end-to-end smoke test
- Ruff lint
- 3 MIDI A/B/C artifacts
- 3 synthetic PCM WAV master previews, individual stems
- Technical WAV A/B/C JSON comparison
- Human review must remain pending until a real listener rates files

No CI test executes licensed original stems or a local Ardour/Surge installation.
