# SEION Music Lab — Project 001

**La Cumbia de los Monjes — experimental rave rework.**

Primary goal: design a **new self-consistent electronic sound**, not a
conventional Latin-rave remix, national-identity project or copy of eleven DJs.

The source recording and Demucs stems are private (git-ignored). The public
repository contains analysis statistics, original MIDI and development code.

## Project truth

- Source reference: ~89.1 BPM, C# minor candidate (uncalibrated chroma score).
- Production hypothesis: 158 BPM, 4/4, C# minor with deliberate modal colour.
- v001: archived/rejected 156 BPM G minor placeholder — **not approved**.
- v002: reproducible, original 16-bar A/B/C MIDI experiments.

Generate the v002 experiments:

    python -m app.music.prototype_lab --out projects/cumbia-de-los-monjes-rave/versions/v002/generated

Then render with the experimental Ardour seed (needs installed Ardour/Surge):

    set PYTHONPATH=connectors/ardour/python
    python -m seion_ardour.cli projects/cumbia-de-los-monjes-rave/versions/v002/generated --prototype groove --name groove_take01

The CLI preserves previous render takes and Ardour sessions; use a new
--name for every audition. It does not automatically prove musical quality.

See creative_brief.md, reference/style_hypotheses.json and
../../docs/project001_review_gate.md for artistic acceptance and provenance.
