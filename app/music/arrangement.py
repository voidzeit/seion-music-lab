"""Arrangement helpers. The MVP produces a single 16-bar loop section.

Fuller song structure (intro / build / drop / break) is intentionally deferred;
the Arranger Agent will grow this in a later sprint.
"""

from __future__ import annotations

from app.schemas import Section


def build_loop_section(
    bars: int,
    energy_start: float = 0.45,
    energy_end: float = 0.55,
    name: str = "loop_A",
) -> list[Section]:
    """Return a single loop section spanning all bars.

    Energy is reported as the mean of start/end so downstream scoring has a
    value to read even though the loop itself is (deliberately) steady.
    """
    energy = round((energy_start + energy_end) / 2, 3)
    return [
        Section(
            name=name,
            start_bar=1,
            length_bars=bars,
            energy=energy,
            description=(
                "Main 16-bar loop: warm seventh chords, offbeat bass, hypnotic "
                "arp and a four-on-the-floor kit. Identity first, arrangement later."
            ),
        )
    ]
