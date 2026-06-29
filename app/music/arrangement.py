"""Arrangement: from a single loop to real song structure (Sprint 3).

``build_loop_section`` (the MVP) is kept for callers that just want one steady
loop. ``build_song_sections`` lays out an intro / build / main / break / drop /
outro with a deliberate energy curve, which is what lets the tension-curve score
rise above the flat-loop floor.
"""

from __future__ import annotations

from app.schemas import Section

# Relative weight (share of total bars) and shape (0=quietest, 1=peak) per part.
_SONG_PLAN: list[tuple[str, float, float]] = [
    ("intro", 0.125, 0.0),
    ("build", 0.25, 0.5),
    ("main", 0.25, 0.7),
    ("break", 0.125, 0.3),
    ("drop", 0.1875, 1.0),
    ("outro", 0.0625, 0.2),
]

_DESCRIPTIONS = {
    "intro": "Hats and atmosphere only — set the scene, hold the kick back.",
    "build": "Kick enters, energy climbs, a fill lifts into the next part.",
    "main": "The full warm-house loop: chords, offbeat bass, arp, four-on-the-floor.",
    "break": "Drop the kick — let the harmony and arp breathe before the peak.",
    "drop": "Peak energy: full kit, accents and the widest, brightest timbre.",
    "outro": "Thin the kit back out so the loop can end or re-cycle cleanly.",
}


def build_loop_section(
    bars: int,
    energy_start: float = 0.45,
    energy_end: float = 0.55,
    name: str = "loop_A",
) -> list[Section]:
    """Return a single loop section spanning all bars (MVP behaviour)."""
    energy = round((energy_start + energy_end) / 2, 3)
    return [
        Section(
            name=name,
            start_bar=1,
            length_bars=bars,
            energy=energy,
            description=(
                "Main loop: warm seventh chords, offbeat bass, hypnotic arp and a "
                "four-on-the-floor kit. Identity first, arrangement later."
            ),
        )
    ]


def _distribute_bars(bars: int) -> list[tuple[str, int]]:
    """Split ``bars`` across the song plan, guaranteeing each kept part >= 1."""
    # Initial proportional allocation.
    alloc = [(name, max(1, round(weight * bars)), shape) for name, weight, shape in _SONG_PLAN]

    # If the rounded total doesn't match, adjust the biggest sections.
    total = sum(n for _, n, _ in alloc)
    order = sorted(range(len(alloc)), key=lambda i: alloc[i][1], reverse=True)
    idx = 0
    while total != bars and order:
        i = order[idx % len(order)]
        name, n, shape = alloc[i]
        if total > bars and n > 1:
            alloc[i] = (name, n - 1, shape)
            total -= 1
        elif total < bars:
            alloc[i] = (name, n + 1, shape)
            total += 1
        idx += 1
    return [(name, n) for name, n, _ in alloc]


def build_song_sections(
    bars: int,
    energy_start: float = 0.25,
    energy_end: float = 0.65,
) -> list[Section]:
    """Lay out intro/build/main/break/drop/outro with a real energy curve.

    Falls back to a single loop section when there aren't enough bars (< 8) to
    give every part room.
    """
    if bars < 8:
        return build_loop_section(bars, energy_start, energy_end, name="loop_A")

    peak = min(1.0, max(energy_end, energy_start + 0.4) + 0.15)
    span = peak - energy_start

    shape_by_name = {name: shape for name, _, shape in _SONG_PLAN}
    sections: list[Section] = []
    cursor = 1
    for name, length in _distribute_bars(bars):
        energy = round(energy_start + shape_by_name[name] * span, 3)
        sections.append(
            Section(
                name=name,
                start_bar=cursor,
                length_bars=length,
                energy=energy,
                description=_DESCRIPTIONS[name],
            )
        )
        cursor += length
    return sections
