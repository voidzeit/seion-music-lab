"""How well does the idea match the requested style references?

We only score traits that MIDI can actually carry (tempo, mode, harmony type,
groove, automation). Timbre, mix and full arrangement are what the producer
finishes in FL Studio, so a correct-but-skeletal loop tops out below 1.0 — and
that gap is the honest, teachable part of "matching" an artist.
"""

from __future__ import annotations

from app.music import analysis
from app.music.scales import parse_key
from app.schemas import MusicalIdea, UserRequest

# MIDI captures the musical skeleton; the rest (sound design, mix, arrangement)
# is completed in the DAW. This ceiling encodes that honestly.
STYLE_MIDI_CEILING = 0.78


def _bpm_value(bpm: int, bpm_range: tuple[int, int]) -> float:
    lo, hi = bpm_range
    if lo <= bpm <= hi:
        return 1.0
    distance = lo - bpm if bpm < lo else bpm - hi
    if distance <= 4:
        return 0.6
    if distance <= 10:
        return 0.3
    return 0.1


def compute_style_match(
    idea: MusicalIdea,
    request: UserRequest,
    style_context: dict,
) -> tuple[float, str]:
    checks: list[tuple[float, float]] = []  # (weight, value 0-1)

    # Tempo.
    bpm_range = tuple(style_context.get("bpm_range", (118, 130)))
    checks.append((1.0, _bpm_value(idea.bpm, bpm_range)))

    # Mode (these styles lean minor / modal-dark).
    _, mode = parse_key(idea.key)
    if style_context.get("prefers_minor", True):
        checks.append((1.0, 1.0 if mode != "major" else 0.3))

    # Harmony type.
    if style_context.get("wants_seventh_chords", True):
        checks.append(
            (1.0, 1.0 if analysis.uses_seventh_or_sixth_chords(request.progression) else 0.4)
        )

    # Offbeat bass.
    if style_context.get("wants_offbeat_bass", True):
        bass = idea.track_by_role("bass")
        checks.append((1.0, 1.0 if bass and "offbeat" in bass.name else 0.4))

    # Hypnotic arp (chord tones, low variety per bar).
    if style_context.get("wants_hypnotic_arp", True):
        arp = idea.track_by_role("arp")
        if arp and arp.notes:
            variety = analysis.unique_pitch_classes(arp)
            value = 1.0 if variety <= 5 else 0.6
        else:
            value = 0.3
        checks.append((1.0, value))

    # Four-on-the-floor. A full arrangement deliberately drops the kick in the
    # intro/break, so we don't require a kick in *every* bar — only that the
    # kit is four-on-the-floor across the bars that drive (>= ~55% of bars).
    if style_context.get("wants_four_on_floor", True):
        drums = next((t for t in idea.tracks if t.is_drum), None)
        kicks = (
            sum(1 for e in drums.drum_events if e.instrument == "kick") if drums else 0
        )
        expected = idea.bars * 4
        value = 1.0 if kicks >= expected * 0.55 else (0.6 if kicks else 0.2)
        checks.append((1.0, value))

    # Tension via filter automation (a signature melodic-techno move).
    if style_context.get("wants_filter_automation", True):
        has_auto = any(a.is_rising for a in idea.automation)
        checks.append((0.8, 1.0 if has_auto else 0.4))

    weight = sum(w for w, _ in checks) or 1.0
    raw = sum(w * v for w, v in checks) / weight
    score = round(raw * STYLE_MIDI_CEILING, 4)

    artists = ", ".join(style_context.get("artists", [])) or "the references"
    note = (
        f"Skeleton matches {artists} on tempo, mode, harmony, groove and filter "
        f"motion (raw {raw:.2f}); capped at {STYLE_MIDI_CEILING:.2f} because timbre, "
        f"mix and full arrangement are finished in FL Studio."
    )
    return score, note
